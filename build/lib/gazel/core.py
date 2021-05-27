from copy import deepcopy
from typing import List

from gazel.common import GazeConfig, Id
from gazel.core_constructors import make_snapshot
from gazel.core_types import PositionMapping, Snapshot
from gazel.edits import edit_source
from gazel.range import token_at_index


def make_versions(source: str, language: str, edits: List[dict]) -> List[Snapshot]:
    snapshots = []
    snapshot_id = 0
    next_id = Id()

    snapshots.append(
        make_snapshot(source, language, index=snapshot_id, next_id=next_id)
    )

    for edit in edits:
        next_snapshot = edit_source(
            snapshots[snapshot_id], edit, next_id=next_id, id=len(snapshots)
        )
        snapshots.append(next_snapshot)
        snapshot_id += 1

    return snapshots


def is_point_valid(line: int, col: int, mapping: PositionMapping) -> bool:
    if not (line >= 0 and col >= 0): return False

    try:
        point = mapping[line, col]

        return True
    except:
        return False


def assign_tokens_to_gazes(
    gazes: List[dict],
    snapshots: List[Snapshot],
    gaze_config: GazeConfig = GazeConfig(),
) -> List[dict]:
    """Assigns token information to the gazes provided

    Parameters
    ----------
    gazes : List[dict]
        The gazes to apply the token info to. This list is not mutated by
        this function.
    snapshots : List[Snapshot]
        A list of snapshots from which to obtain token information.
        The timestamps of these snapshots must correspond to the timestamps
        in the gazes
    gaze_config : GazeConfig, optional
        a config containing the keys of various columns in a single gaze entry, by default GazeConfig()

    Returns
    -------
    List[dict]
        A list of gazes annotated with token information.
    """
    # TODO: cleanup
    # TODO: test
    current_version = 0
    gazes = deepcopy(gazes)
    for gaze in gazes:
        if current_version + 1 < len(snapshots):
            if gaze[gaze_config.time_key] > snapshots[current_version + 1].time:
                current_version += 1
        line, col = gaze[gaze_config.line_key], gaze[gaze_config.col_key]
        
        snapshot = snapshots[current_version]
        if not is_point_valid(line, col, snapshot.source.mapping):
            continue
        gaze_index = snapshot.source.mapping[line, col]

        token = token_at_index(snapshot, gaze_index)  # TODO

        if token:
            gaze["syntax_node_offset"] = gaze_index - token.range.start.index
            gaze["syntax_node"] = token.syntax_node
            gaze["syntax_node_id"] = token.id
            gaze["syntax_node_text"] = token.source[
                token.range.start.index : token.range.end.index
            ]
        else:
            gaze["syntax_node_offset"] = None
            gaze["syntax_node"] = None
            gaze["syntax_node_id"] = None
            gaze["syntax_node_text"] = None

    return gazes

