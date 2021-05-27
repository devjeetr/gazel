import functools
from typing import Dict, List, Set, Union, cast

import pampy
import pandas as pd

from gazel.core import assign_tokens_to_gazes, make_versions
from gazel.core_types import GazeChange, Snapshot, SnapshotDiff, TokenChange


def get_edit_time(edit: Dict) -> float:
    if edit["type"] == "aggregated":
        return edit["edits"][-1]["timestamp"]
    else:
        return edit["timestamp"]


def _merge_edits(*edits: Dict) -> Dict:
    assert len(edits) > 0

    first_edit = edits[0]

    if first_edit["type"] == "aggregated":
        first_edit["edits"].extend(edits[1:])
        return first_edit
    else:
        return {"type": "aggregated", "edits": list(edits)}


def _aggregate_edits(edits: List[Dict], aggregation_window=3):
    def _reducer(accumulated_edits: List[Dict], next_edit: Dict) -> List[Dict]:
        if not accumulated_edits:
            return [next_edit]
        else:
            last_edit = accumulated_edits[-1]
            last_time = get_edit_time(last_edit)
            curr_time = get_edit_time(next_edit)
            if curr_time - last_time < aggregation_window:
                return accumulated_edits[:-1] + [_merge_edits(last_edit, next_edit)]

            return accumulated_edits + [next_edit]

    return functools.reduce(_reducer, edits, cast(List[Dict], []))


class Tracker:
    def __init__(
        self,
        source: str,
        gazes: Union[List[dict], pd.DataFrame],
        changelog: List[dict],
        source_language: str,
        edit_aggregation_window: float = 3.0,
    ):
        changelog = _aggregate_edits(changelog, edit_aggregation_window)
        self.changelog = changelog
        # self.changelog = changelog

        self.edit_aggregation_window = edit_aggregation_window
        self.snapshots = make_versions(source, source_language, self.changelog)
        gazes = assign_tokens_to_gazes(gazes.to_dict("records"), self.snapshots)
        self.gazes: pd.dataFrame = pd.DataFrame(gazes)

    def diff(self, start: int = 0, end: int = -1) -> SnapshotDiff:
        """Returns a diff between the snapshot versions
        `start` and `end`. The diff includes all changes to
        tokens and gazes that occur between `end` and `start`.

        Parameters
        ----------
        start : int
            the index of the starting snapshot
        end : int
            the index of the modified snapshot

        Returns
        -------
        SnapshotDiff
            token and gaze changes that occur for this diff.
        """
        changes: List[TokenChange] = []

        for i in range(start, end):
            snapshot = self.snapshots[i]
            changes.extend(snapshot.changes)

        gaze_changes: List[GazeChange] = []

        last_snapshot_time = self.snapshots[end - 1].time
        gazes: pd.DataFrame = self.gazes
        potentially_changed_gazes = gazes[gazes["system_time"] < last_snapshot_time]

        # TODO: Add gaze changes
        for token_change in changes:
            if token_change.type == "moved":
                assert (
                    token_change.old and token_change.new
                ), "TokenChange must have `old` and `new` tokens if change type is `moved`"
                affected_gazes = potentially_changed_gazes[
                    potentially_changed_gazes.syntax_node_id == token_change.old.id
                ]
                affected_gazes = affected_gazes.to_dict("records")

                for gaze in affected_gazes:
                    new_col = (
                        token_change.new.range.start.point.col
                        + gaze["syntax_node_offset"]
                    )
                    new_gaze = {
                        **gaze,
                        "source_file_line": token_change.new.range.start.point.line,
                        "source_file_col": new_col,
                    }
                    gaze_changes.append(
                        GazeChange(type="moved", old=gaze, new=new_gaze)
                    )

        return SnapshotDiff(
            old=self.snapshots[start],
            new=self.snapshots[end - 1],
            token_changes=changes,
            gaze_changes=gaze_changes,
        )

    def fixations_for_edit_window(
        self, index: int, snapshot_only=False
    ) -> pd.DataFrame:
        """returns all the gazes for the snapshot at index `index`.
        By default, it will provide all gazes from the start of the experiment,
        until the snapshot `i`. If you want gazes only for the duration of time
        that this snapshot exists, use `snapshot_only=True`.

        Parameters
        ----------
        index : int
            snapshot index
        snapshot_only : bool, optional
            if false, returns all gazes until snapshot `i`, else
            returns only gazes within the time window of snapshot `i`, by default False

        Returns
        -------
        pd.DataFrame
            A dataframe containing the requested gazes.
        """
        assert index < len(self.snapshots)

        start_time = pampy.match(
            # fmt: off
            index, 
            0, 0, 
            default=self.changelog[index]["timestamp"]
            # fmt: on
        )
        end_time = pampy.match(
            index,
            len(self.snapshots) - 1,
            float("inf"),
            default=self.changelog[index + 1]["timestamp"],
        )

        filtered_index = (self.gazes["system_time"] >= start_time) & (
            self.gazes["system_time"] < end_time
        )
        filtered_gazes = self.gazes[filtered_index]

        return filtered_gazes

    def snapshot(self, index: int) -> Snapshot:
        """Returns the snapshot at index `index`

        Parameters
        ----------
        index : [type]
            the snapshot index. 
            This is `0` for the original source version,
            `1` for the first edit, `2` for second edit 
            and so on.

        Returns
        -------
        Snapshot
            The snapshot at index `index`
        """
        return self.snapshots[index]

    def snapshot_at_time(self, t: float) -> Snapshot:
        """Returns the snapshot that exists at time `t`

        Parameters
        ----------
        t : float
            timestamp for which you need the snapshot

        Returns
        -------
        Snapshot
            The snapshot at time `t`
        """
        for i, _ in enumerate(self.snapshots[1:]):
            if t >= self.snapshots[i - 1].time and t < self.snapshots[i].time:
                return self.snapshots[i - 1]

        return self.snapshots[-1]

    def get_fixations(self):
        return self.gazes

    def get_fixations_for_snapshot(self, i: int) -> pd.DataFrame:
        assert i >= 0, "index must be >= 0"
        assert i < len(self.snapshots), "invalid snapshot id"

        start_time = self.snapshots[i].time
        end_time = (
            self.snapshots[i + 1].time if i + 1 < len(self.snapshots) else float("inf")
        )
        gazes = self.gazes
        return gazes[(gazes.system_time >= start_time) & (gazes.system_time < end_time)]

    def get_token_history(
        self, id_or_ids: Union[Set[int], int], start_snapshot=0
    ) -> List[TokenChange]:
        if isinstance(id_or_ids, int):
            id_or_ids = {id_or_ids}

        diff = self.diff(start_snapshot, len(self.snapshots))
        token_changes = diff.token_changes
        return list(
            filter(
                lambda change: _get_token_id_for_change(change)
                in cast(Set[int], id_or_ids),
                token_changes,
            )
        )

    def get_first_token_by_text(self, text):
        for snapshot in self.snapshots:
            for token in snapshot.tokens:
                start, end = token.range.start.index, token.range.end.index
                token_text = token.source[start:end]
                if token_text == text:
                    return token


def _get_token_id_for_change(change: TokenChange) -> int:
    if change.old:
        return change.old.id
    if change.new:
        return change.new.id

    raise Exception("Either old or new token need to exist in TokenChange")

