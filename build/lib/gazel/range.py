from gazel.core_types import Position, PositionMapping, Range, Snapshot, Token, Point
from typing import Tuple, Union, Optional


def _shift_range(token_range: Range, n: int, mapping: PositionMapping) -> Range:
    return Range(
        _shift_position(token_range.start, n, mapping),
        _shift_position(token_range.end, n, mapping),
    )


def _shift_position(position: Position, n: int, mapping: PositionMapping) -> Position:
    if not n:
        n = 0
    new_index = position.index + n

    return Position(index=new_index, point=mapping[new_index])


def token_at_point(snapshot: Snapshot, point: Point) -> Union[Token, None]:
    index = snapshot.source.mapping[point.line, point.col]
    return token_at_index(snapshot, index)


def range_overlaps(a: Tuple[int, int], b: Tuple[int, int]):
    return set(range(a[0], a[1])) & set(range(b[0], b[1]))


def range_contains(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """if range `a` completely contains range `b`

    Parameters
    ----------
    a : Tuple[int, int]
        [description]
    b : Tuple[int, int]
        [description]

    Returns
    -------
    [type]
        [description]
    """
    return b[0] >= a[0] and b[1] < a[1]


def get_token_at_range(snapshot: Snapshot, r: Tuple[int, int]) -> Optional[Token]:
    for token in snapshot.tokens:
        if range_overlaps((token.range.start.index, token.range.end.index), r):
            return token

    return None


def range_contains_index(r: Range, index: int) -> bool:
    return index >= r.start.index and index < r.end.index


def token_at_index(snapshot: Snapshot, index: int) -> Optional[Token]:
    for token in snapshot.tokens:
        if range_contains_index(token.range, index):
            return token
    return None


def same_point_range(a: Range, b: Range) -> bool:
    return a.start.point == b.start.point and a.end.point == b.end.point


def extract_range(source: str, r: Range):
    return source[r.start.index : r.end.index]
