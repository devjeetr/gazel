from typing import List
from common import create_position_index_mapping, Id, insert, delete
from parsing import make_parse_table, get_capture_for_gaze


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


class Position:
    def __init__(self, row=0, col=0, index=0):
        self.row = row
        self.index = index
        self.col = col


def adjust_gaze_for_delete_edit(
    gaze: Position,
    edit: Position,
    deleted_text: str,
    index_to_position,
    position_to_index,
):
    lines_deleted = deleted_text.count("\n")
    adjusted_row, adjusted_col = (gaze.row, gaze.col)
    # check if the current gaze was deleted
    if gaze.index >= edit.index and gaze.index < edit.index + len(deleted_text):
        # skip this gaze, it was deleted
        return
    # if lines didn't change
    if lines_deleted == 0:
        if gaze.row == edit.row and gaze.col >= edit.col:
            adjusted_col -= len(deleted_text)
    elif gaze.row >= edit.row:
        last_line_w_delete = index_to_position[edit.index + len(deleted_text)][0]
        if gaze.row == last_line_w_delete:
            adjusted_index = position_to_index[gaze.row][gaze.col] - len(deleted_text)
            adjusted_row, adjusted_col = index_to_position[adjusted_index]
            # modified_gazes.append(new_gaze)
        elif gaze.row > edit.row:
            adjusted_row -= lines_deleted

    return (adjusted_row, adjusted_col)


def perform_adjustments_for_edit(
    gazes,
    edit,
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
    index_to_position, position_to_index = create_position_index_mapping(source)

    modified_gazes = []
    # if it is insert
    if edit[edit_type_k] == edit_insert_type:
        # insert it
        source = insert(source, edit[edit_start_k], edit[edit_text_k])
        # now for each gaze
        for gaze in gazes:
            # copy it
            edit_row, edit_col = index_to_position[edit[edit_start_k]]
            gaze_row, gaze_col = gaze[gaze_line_k], gaze[gaze_col_k]
            adjusted_row, adjusted_col = adjust_gaze_for_insert_edit(
                (gaze_row, gaze_col), (edit_row, edit_col), edit[edit_text_k]
            )
            modified_gazes.append(
                {**gaze, gaze_line_k: adjusted_row, gaze_col_k: adjusted_col,}
            )

    else:  # delete
        source, deleted_text = delete(source, edit[edit_start_k], edit[edit_size_k])
        for gaze in gazes:

            edit_row, edit_col = index_to_position[edit[edit_start_k]]

            edit_position = Position(
                row=edit_row, col=edit_col, index=edit[edit_start_k]
            )
            gaze_index = position_to_index[gaze[gaze_line_k]][gaze[gaze_col_k]]
            gaze_position = Position(
                row=gaze[gaze_line_k], col=gaze[gaze_col_k], index=gaze_index
            )

            adjusted_position = adjust_gaze_for_delete_edit(
                gaze_position,
                edit_position,
                deleted_text,
                index_to_position,
                position_to_index,
            )

            if adjusted_position:
                modified_gazes.append(
                    {
                        **gaze,
                        gaze_line_k: adjusted_position[0],
                        gaze_col_k: adjusted_position[1],
                    }
                )

    return modified_gazes, source


def perform_adjustments(
    gazes,
    edits,
    source,
    language_extension,
    gaze_line_k="line",
    gaze_col_k="col",
    edit_start_k="start",
    edit_text_k="text",
    edit_type_k="type",
    edit_size_k="size",
    edit_insert_type="insert",
    edit_delete_type="delete",
    edit_time_k="time",
    gaze_time_k="time",
):
    next_id = Id()
    # special case for first gaze
    gazes_before_first_edit = [
        {**gaze, "gaze_id": next_id()}
        for gaze in gazes
        if gaze[gaze_time_k] < edits[0][edit_time_k]
    ]
    _, pti = create_position_index_mapping(source)
    parse_table = make_parse_table(source, language_extension)
    gazes_before_first_edit = annotate_gazes(
        gazes_before_first_edit,
        parse_table,
        pti,
        gaze_line_k=gaze_line_k,
        gaze_col_k=gaze_col_k,
    )

    gaze_sets = [gazes_before_first_edit]

    # now for the rest of the gazes
    current_gazes = gazes[:]
    current_source = source[:]
    for i, edit in enumerate(edits):
        valid_gazes = [
            gaze for gaze in current_gazes if gaze[gaze_time_k] < edit[edit_time_k]
        ]

        adjusted_gazes, current_source = perform_adjustments_for_edit(
            valid_gazes,
            edit,
            current_source,
            gaze_line_k="line",
            gaze_col_k="col",
            edit_start_k="start",
            edit_text_k="text",
            edit_type_k="type",
            edit_size_k="size",
            edit_insert_type="insert",
            edit_delete_type="delete",
        )

        if i + 1 < len(edits):
            remaining_gazes = [
                gaze
                for gaze in current_gazes
                if gaze[gaze_time_k] >= edit[edit_time_k]
                and gaze[gaze_time_k] < edits[i + 1]
            ]
        else:
            remaining_gazes = [
                gaze for gaze in current_gazes if gaze[gaze_time_k] >= edit[edit_time_k]
            ]

        _, pti = create_position_index_mapping(current_source)
        remaining_gazes = [{**gaze, "gaze_id": next_id()} for gaze in remaining_gazes]
        parse_table = make_parse_table(current_source, language_extension)
        remaining_gazes = annotate_gazes(
            remaining_gazes, parse_table, pti, gaze_line_k, gaze_col_k
        )

        gaze_sets.append(adjusted_gazes + remaining_gazes)
    return gaze_sets


def annotate_gazes(gazes, parse_table, pti, gaze_line_k="line", gaze_col_k="col"):
    annotated = []

    for gaze in gazes:
        index = pti[gaze[gaze_line_k]][gaze[gaze_col_k]]
        name = get_capture_for_gaze((index, index + 1), parse_table)
        annotated.append({**gaze, "syntax_class": name})

    return annotated


def track_edits_across_time(
    source: str,
    language_extension: str,
    gazes: List[dict],
    edits: List[dict],
    gaze_line_k="line",
    gaze_col_k="col",
    edit_start_k="start",
    edit_text_k="text",
    edit_type_k="type",
    edit_size_k="size",
    edit_insert_type="insert",
    edit_delete_type="delete",
):
    itp, pti = create_position_index_mapping(source)

