from dataclasses import dataclass
from gazel.parsing import get_tokens
from gazel.common import create_position_index_mapping, Id
from typing import Dict, List, Literal, Mapping, Optional, Tuple, NamedTuple
from difflib import Differ
from pprint import pformat


@dataclass(frozen=True, eq=True, order=True)
class Point:
    line: int
    col: int

    def __repr__(self):
        return f"(l={self.line},c={self.col})"


@dataclass(frozen=True, repr=True, eq=True, order=True)
class Position:
    index: int
    point: Point


@dataclass(frozen=True, repr=True, eq=True, order=True)
class Range:
    start: Position
    end: Position

    def __repr__(self):
        return f"Range: [{self.start}, {self.end}]"


class IndexRange(NamedTuple):
    start: int
    end: int


@dataclass(frozen=True, eq=True, order=True)
class Token:
    range: Range
    source: str
    id: int
    syntax_node: str

    def __repr__(self):
        return self.source[self.range.start.index : self.range.end.index]


class PositionMapping:
    """maps from line-col to index &
       index to line-col
    """

    def __init__(
        self,
        index_to_point: Mapping[int, Point] = None,
        point_to_index: Mapping[Point, int] = None,
    ):

        self.index_to_point = index_to_point
        self.point_to_index = point_to_index

    def __getitem__(self, key):
        if isinstance(key, (list, tuple)):
            assert len(key) == 2

            line, col = key
            # assert isinstance(line, (None, int)) and isinstance(col, (None, int))
            if not line:
                line = 0
            if not col:
                col = len(self.index_to_point[line])

            return self.point_to_index[Point(line, col)]
        elif isinstance(key, int):
            return self.index_to_point[key]

        raise Exception("Invalid access")


@dataclass(frozen=True)
class TokenChange:
    type: Literal["moved", "inserted", "deleted", "edited"]
    old: Optional[Token]
    new: Optional[Token]

    def __repr__(self):
        old_text = ""
        if self.old:
            old_text = self.old.source[
                self.old.range.start.index : self.old.range.end.index
            ]
        new_text = ""
        if self.new:
            new_text = self.new.source[
                self.new.range.start.index : self.new.range.end.index
            ]

        d = Differ()
        return pformat(list(d.compare([old_text], [new_text])))


class GazeChange(NamedTuple):
    type: Literal["deleted", "moved"]
    old: Dict
    new: Dict


@dataclass(frozen=True)
class Source:
    text: str
    mapping: PositionMapping
    language: str


@dataclass(frozen=True)
class Snapshot:
    id: int
    source: Source
    tokens: Tuple[Token, ...]
    _token_by_range: Mapping[Range, Token]
    changes: Tuple[TokenChange, ...] = ()
    time: float = 0.0


class SnapshotDiff(NamedTuple):
    old: Snapshot
    new: Snapshot
    token_changes: List[TokenChange]
    gaze_changes: List[GazeChange]


def make_source(source: str, language: str) -> Source:
    itp, pti = create_position_index_mapping(source)

    return Source(source, PositionMapping(itp, pti), language)


def token_from_capture(
    capture, source: str, mapping: PositionMapping, token_id=None
) -> Token:
    (start, end), syntax_node = capture
    start_point = mapping[start]
    end_point = mapping[end]
    token_range = Range(Position(start, start_point), Position(end, end_point))

    return Token(range=token_range, syntax_node=syntax_node, id=token_id, source=source)


def make_snapshot(source: str, language: str, index=0, next_id=Id(),) -> Snapshot:
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
