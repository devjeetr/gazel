from dataclasses import dataclass
from typing import Dict, List, Literal, Mapping, Optional, Tuple, NamedTuple
import pandas as pd


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
    type: Literal["moved", "inserted", "deleted"]
    old: Optional[Token]
    new: Optional[Token]


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
