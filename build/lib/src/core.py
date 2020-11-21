from typing import (
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)
from copy import deepcopy
import pampy

from common import (
    EditConfig,
    GazeConfig,
    Id,
    create_position_index_mapping,
    delete,
    insert,
)
from core_types import (
    TokenChange,
    Point,
    Position,
    PositionMapping,
    Range,
    Snapshot,
    Source,
    Token,
)
from parsing import get_tokens


def extract_range(source: str, r: Range):
    return source[r.start.index : r.end.index]


def token_from_capture(
    capture, source: str, mapping: PositionMapping, token_id=None
) -> Token:
    (start, end), syntax_node = capture
    start_point = mapping[start]
    end_point = mapping[end]
    token_range = Range(Position(start, start_point), Position(end, end_point))

    return Token(range=token_range, syntax_node=syntax_node, id=token_id, source=source)


def make_source(source: str, language: str) -> Source:
    itp, pti = create_position_index_mapping(source)

    return Source(source, PositionMapping(itp, pti), language)


def make_snapshot(
    source: str, language: str, index=0, next_id=Id(),
):
    _source = make_source(source, language)
    captures = get_tokens(source, language, _source.mapping.point_to_index)
    tokens = tuple(
        token_from_capture(capture, source, _source.mapping, token_id=next_id())
        for capture in captures
    )
    token_by_range: Dict[Range, Token] = {}
    for token in tokens:
        token_by_range[token.range] = token

    return Snapshot(index, _source, tokens, _token_by_range=token_by_range)


def same_point_range(a: Range, b: Range):
    return a.start.point == b.start.point and a.end.point == b.end.point


def get_change(old: Token = None, new: Token = None) -> Optional[TokenChange]:
    if not old and new:
        return TokenChange(type="inserted", old=old, new=new)
    elif old and not new:
        return TokenChange(type="deleted", old=old, new=new)
    elif old and new:
        if not same_point_range(old.range, new.range):
            return TokenChange(type="moved", old=old, new=new)

    return None


def _shift_position(position: Position, n, mapping: PositionMapping) -> Position:
    if not n:
        n = 0
    new_index = position.index + n

    return Position(index=new_index, point=mapping[new_index])


def _shift_range(token_range: Range, n: int, mapping: PositionMapping) -> Range:
    return Range(
        _shift_position(token_range.start, n, mapping),
        _shift_position(token_range.end, n, mapping),
    )


def range_overlaps(a: Tuple[int, int], b: Tuple[int, int]):
    return set(range(a[0], a[1])) & set(range(b[0], b[1]))


def _adjust_tokens_for_edit(
    old_snapshot: Snapshot,
    new_snapshot: Snapshot,
    direction: Literal["left", "right"],
    affected_index_range: Tuple[int, int],
    next_id=Id(),
):
    shift = affected_index_range[1] - affected_index_range[0]
    shift = pampy.match(direction, "left", -shift, "right", shift)
    adjusted_tokens: List[Token] = []
    changes: List[TokenChange] = []

    # FIXME
    # deleted tokens do not get reported to
    # the change list.
    for token in new_snapshot.tokens:
        if range_overlaps(
            affected_index_range, (token.range.start.index, token.range.end.index)
        ):
            new_token = Token(token.range, token.source, next_id(), token.syntax_node)
            change = get_change(old=None, new=new_token)

            adjusted_tokens.append(new_token)
            if change:
                changes.append(change)
        else:
            # only tokens that start after the
            # end of the affected range need
            # to be adjusted
            if token.range.start.index >= affected_index_range[1]:
                old_range = _shift_range(
                    token.range, -shift, old_snapshot.source.mapping
                )
                if old_range in old_snapshot._token_by_range:
                    old_token = old_snapshot._token_by_range[old_range]
                    new_token = Token(
                        source=token.source,
                        range=token.range,
                        syntax_node=token.syntax_node,
                        id=old_token.id,
                    )
                    adjusted_tokens.append(new_token)
                    change = get_change(old_token, new_token)
                    if change:
                        changes.append(change)
                    else:
                        # newly inserted token
                        # this should actually never happen?
                        new_token = Token(
                            token.range, token.source, next_id(), token.syntax_node
                        )
                        adjusted_tokens.append(new_token)
                        change = get_change(None, new_token)
                        if change:
                            changes.append(change)

    return adjusted_tokens, changes


def token_info_for_delete(
    old_snapshot: Snapshot, start: int, size: int, next_id=Id(), id=0, time=0.0
):
    new_source, _ = delete(old_snapshot.source.text, start, size)

    new_snapshot = make_snapshot(new_source, old_snapshot.source.language, index=id,)
    affected_range = (start, start + size)
    tokens, changes = _adjust_tokens_for_edit(
        old_snapshot, new_snapshot, "left", affected_range, next_id
    )

    return Snapshot(
        id=new_snapshot.id,
        source=new_snapshot.source,
        tokens=tokens,
        changes=changes,
        _token_by_range=new_snapshot._token_by_range,
        time=time,
    )


def token_info_for_insert(
    old_snapshot: Snapshot, start: int, text: str, next_id=Id(), id=0, time=0.0
):
    new_source = insert(old_snapshot.source.text, start, text)

    new_snapshot = make_snapshot(new_source, old_snapshot.source.language, index=id,)
    affected_range = (start, start + len(text))

    tokens, changes = _adjust_tokens_for_edit(
        old_snapshot, new_snapshot, "right", affected_range, next_id
    )
    return Snapshot(
        id=new_snapshot.id,
        source=new_snapshot.source,
        tokens=tokens,
        changes=changes,
        _token_by_range=new_snapshot._token_by_range,
        time=time,
    )


def edit_source(
    snapshot: Snapshot, edit: dict, next_id: Callable[[], Union[str, float, int]], id=0
) -> Snapshot:
    return pampy.match(
        edit,
        {"type": "insert"},
        lambda edit: token_info_for_insert(
            snapshot,
            start=edit["offset"],
            text=edit["text"],
            next_id=next_id,
            id=id,
            time=edit["timestamp"],
        ),
        {"type": "delete"},
        lambda edit: token_info_for_delete(
            snapshot,
            start=edit["offset"],
            size=edit["len"],
            next_id=next_id,
            id=id,
            time=edit["timestamp"],
        ),
    )


def range_contains_index(r: Range, index: int) -> bool:
    return index >= r.start.index and index < r.end.index


def token_at_index(snapshot: Snapshot, index: int) -> Union[Token, None]:
    for token in snapshot.tokens:
        if range_contains_index(token.range, index):
            return token
    return None


def token_at_point(snapshot: Snapshot, point: Point) -> Union[Token, None]:
    index = snapshot.source.mapping[point.line, point.col]
    return token_at_index(snapshot, index)


def make_versions(source: str, language: str, edits: List[dict]) -> List[Snapshot]:
    snapshots = []
    snapshot_id = 0
    next_id = Id()
    # first version
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

    current_version = 0
    gazes = deepcopy(gazes)
    for gaze in gazes:
        if current_version + 1 < len(snapshots):
            if gaze[gaze_config.time_key] > snapshots[current_version + 1].time:
                # TODO add assertion here
                current_version += 1
        line, col = gaze[gaze_config.line_key], gaze[gaze_config.col_key]
        snapshot = snapshots[current_version]
        gaze_index = snapshot.source.mapping[line, col]
        token = token_at_index(snapshot, gaze_index)  # TODO

        if token:
            gaze["syntax_node_offset"] = gaze_index - token.range.start.index
            gaze["syntax_node"] = token.syntax_node
            gaze["syntax_node_id"] = token.id
        else:
            gaze["syntax_node_offset"] = None
            gaze["syntax_node"] = None
            gaze["syntax_node_id"] = None

    return gazes


# next_id = Id()
# source = "auto x = 5;\nauto y = 22;\n"

# edits = [
#     {"type": "insert", "offset": 0, "len": 6, "text": "asdasd ", "timestamp": 1},
#     {"type": "delete", "offset": 0, "len": 6, "timestamp": 4},
# ]

# gazes = [
#     {"source_file_line": 0, "source_file_col": 2, "system_time": 0, "gaze_id": 0},
#     {"source_file_line": 0, "source_file_col": 2, "system_time": 2, "gaze_id": 4},
#     {"source_file_line": 0, "source_file_col": 2, "system_time": 2, "gaze_id": 5},
# ]

# snapshots = make_versions(source, "cpp", edits)

# modified_gazes = assign_tokens_to_gazes(gazes, snapshots)

# print(modified_gazes)
