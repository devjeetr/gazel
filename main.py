from tree_sitter import Language, Parser
from typing import List

# JS_LANGUAGE = Language("build/my-languages.so", "javascript")


def create_position_index_mapping(source):
    lines = source.splitlines(True)
    index_to_position = []
    position_to_index = []

    index = 0
    current_line = 0

    for line_number, line in enumerate(lines):
        if len(position_to_index) < current_line + 1:
            position_to_index.append([])

        for column, _ in enumerate(line):
            index_to_position.append((line_number, column))
            position_to_index[line_number].append(index)

            index += 1
        current_line += 1

    return index_to_position, position_to_index


def insert(source, start, text):
    return source[: start + 1] + text + source[start + 1 :]


def delete(source, start, size):
    return source[:start] + source[start + size :], source[start : start + size]


def find_word_at(text, index):
    l = index
    r = index

    while l > 0 and text[l] not in [" ", "\n", ";", ","]:
        l -= 1
    l += 1

    while r < len(text) and text[r] not in [" ", "\n", ";", ","]:
        r += 1

    return text[l:r]


def copy(items):
    new_items = []

    for item in items:
        new_items.append(item.copy())

    return new_items


def adjust_gaze_for_insert_edit(gaze_position, edit_position, text):
    gaze_row, gaze_col = gaze_position
    edit_row, edit_col = edit_position
    lines_inserted = text.count("\n")
    adjusted_row, adjusted_col = (gaze_row, gaze_col)
    # if the gaze is on the same line as the edit
    # and at a later column
    if gaze_row == edit_row and gaze_col >= edit_col:
        if lines_inserted > 0:
            adjusted_row = gaze_row + lines_inserted
            # on the new line, our gazes shift to the left
            adjusted_col = gaze_col - edit_col
        else:
            adjusted_col = gaze_col + len(text)

    # if any lines were inserted, we need to
    elif gaze_row > edit_row:
        # for that particular row
        adjusted_row = gaze_row + lines_inserted

    return adjusted_row, adjusted_col


def perform_adjustments(
    gazes,
    edits,
    source,
    gaze_line_k="line",
    gaze_col_k="col",
    edit_start_k="start",
    edit_text_k="text",
    edit_type_k="type",
    edit_size_k="size",
    edit_insert_type="insert",
    edit_delete_type="delete",
):
    gaze_sets = []

    current_source = source[:]
    current_gazes = copy(gazes)

    for edit in edits:
        index_to_position, position_to_index = create_position_index_mapping(
            current_source
        )

        modified_gazes = []
        # if it is insert
        if edit[edit_type_k] == edit_insert_type:
            # insert it
            current_source = insert(
                current_source, edit[edit_start_k], edit[edit_text_k]
            )
            # now for each gaze
            for gaze in gazes:
                # copy it
                row, col = index_to_position[edit[edit_start_k]]
                gaze_row, gaze_col = gaze[gaze_line_k], gaze[gaze_col_k]
                adjusted_row, adjusted_col = adjust_gaze_for_insert_edit(
                    (gaze_row, gaze_col), (row, col), edit[edit_text_k]
                )
                modified_gazes.append(
                    {**gaze, gaze_line_k: adjusted_row, gaze_col_k: adjusted_col,}
                )

        else:  # delete

            current_source, deleted_text = delete(
                current_source, edit[edit_start_k], edit[edit_size_k]
            )
            for i, gaze in enumerate(current_gazes):
                print(i)
                new_gaze = gaze.copy()

                row, col = index_to_position[edit[edit_start_k]]
                lines_deleted = deleted_text.count("\n")
                print(deleted_text)
                # check if the current gaze was deleted
                gaze_index = position_to_index[new_gaze[gaze_line_k]][
                    new_gaze[gaze_col_k]
                ]
                if (
                    gaze_index >= edit[edit_start_k]
                    and gaze_index < edit[edit_start_k] + edit[edit_size_k]
                ):
                    # skip this gaze, it was deleted
                    continue
                # if lines didn't change
                if lines_deleted == 0:
                    print("deleted == 0")
                    if new_gaze[gaze_line_k] == row and new_gaze[gaze_col_k] >= col:
                        new_gaze[gaze_col_k] -= edit[edit_size_k]
                    modified_gazes.append(new_gaze)
                elif new_gaze[gaze_line_k] >= row:
                    last_line_w_delete = index_to_position[
                        edit[edit_start_k] + edit[edit_size_k]
                    ][0]
                    if new_gaze[gaze_line_k] == last_line_w_delete:
                        gaze_index = position_to_index[new_gaze[gaze_line_k]][
                            new_gaze[gaze_col_k]
                        ]
                        gaze_index -= edit[edit_size_k]
                        row, col = index_to_position[gaze_index]
                        new_gaze[gaze_col_k] = col
                        new_gaze[gaze_line_k] = row
                        modified_gazes.append(new_gaze)
                    elif new_gaze[gaze_line_k] > row:
                        new_gaze[gaze_line_k] -= lines_deleted
                        modified_gazes.append(new_gaze)
                    else:
                        modified_gazes.append(new_gaze)
                else:
                    modified_gazes.append(new_gaze)
        gaze_sets.append(modified_gazes)
        current_gazes = modified_gazes
    return gaze_sets
