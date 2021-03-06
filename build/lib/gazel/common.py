from typing import Dict, Mapping, NamedTuple, Tuple
from gazel.core_types import Point


class Id:
    def __init__(self):
        self.i = -1

    def __call__(self):
        self.i += 1
        return self.i


def create_position_index_mapping(
    source,
) -> Tuple[Mapping[int, Point], Mapping[Point, int]]:
    lines = source.splitlines(True,)
    index_to_position: Dict[int, Point] = {}
    position_to_index: Dict[Point, int] = {}

    index = 0

    for line, lineContents in enumerate(lines):

        for col, _ in enumerate(lineContents):
            point = Point(line=line, col=col)
            index_to_position[index] = point
            position_to_index[point] = index

            index += 1

    point = Point(line=len(lines) - 1, col=len(lines[-1]))
    index_to_position[index] = point
    position_to_index[point] = index

    return index_to_position, position_to_index


class EditConfig(NamedTuple):
    time_key: str = "timestamp"
    size_key: str = "len"
    text_key: str = "text"
    offset_key: str = "offset"
    line_key: str = "line"
    col_key: str = "col"


class GazeConfig(NamedTuple):
    time_key: str = "system_time"
    line_key: str = "source_file_line"
    col_key: str = "source_file_col"

