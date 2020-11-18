from typing import Tuple, List


def insert(source, start, text):
    return source[:start] + text + source[start:]


def delete(source, start, size):
    return source[:start] + source[start + size :], source[start : start + size]


class Id:
    def __init__(self):
        self.i = -1

    def __call__(self):
        self.i += 1
        return self.i


def create_position_index_mapping(
    source,
) -> Tuple[List[Tuple[int, int]], List[List[int]]]:
    lines = source.splitlines(True,)
    index_to_position = []
    position_to_index = []

    index = 0
    current_line = 0

    for line_number, line in enumerate(lines):
        if len(position_to_index) < line_number + 1:
            position_to_index.append([])

        for column, _ in enumerate(line):
            index_to_position.append((line_number, column))
            position_to_index[line_number].append(index)

            index += 1

    return index_to_position, position_to_index

