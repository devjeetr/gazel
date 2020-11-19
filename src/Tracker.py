from core_types import SnapshotDiff
import functools
from typing import Dict, List, Union

import pampy
import pandas as pd

from core import make_versions


def get_edit_time(edit: Dict) -> float:
    return pampy.match(
        edit,
        {"type": "aggregated"},
        edit["edits"][-1]["timestamp"],
        default=edit["timestamp"],
    )


def _merge_edits(*edits: List[Dict]) -> Dict:
    assert len(edits) > 0

    first_edit = edits[0]

    if first_edit["type"] == "aggregated":
        first_edit["edits"].extend(edits[1:])
        return first_edit
    else:
        return {"type": "aggregated", "edits": edits}


def _aggregate_edits(edits: Dict, aggregation_window=2):
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

    return functools.reduce(_reducer, edits)


class Tracker:
    def __init__(
        self,
        source: str,
        gazes: Union[List[dict], pd.DataFrame],
        changelog: List[dict],
        source_language: str,
        edit_aggregation_window: float = 1.0,
    ):
        # TODO
        # test _aggregated_edits & re-introduce
        # self.changelog = _aggregate_edits(changelog, edit_aggregation_window)
        self.changelog = changelog

        self.edit_aggregation_window = edit_aggregation_window
        self.snapshots = make_versions(source, source_language, changelog)
        # fmt: off
        self.gazes = pampy.match(gazes, 
                                 pd.DataFrame, gazes, 
                                 list, pd.DataFrame(gazes))
        # fmt: on

    def diff(self, start=int, end=int) -> SnapshotDiff:
        """Returns the diff between the given versions.
        Args:
            start ([type], optional): [description]. Defaults to int.
            end ([type], optional): [description]. Defaults to int.
        """
        changes = []

        for i in range(start, end):
            snapshot = self.snapshots[i]

            changes.extend(snapshot.changes)
        

        return changes

    def gazes_for_edit_window(self, index) -> List[Dict]:
        assert index < len(self.snapshots)

        start_time = pampy.match(
            index, 0, 0, default=self.changelog[index]["timestamp"]
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

    def top_n_edited(self, n=5):
        pass