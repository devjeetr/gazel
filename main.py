from tree_sitter import Language, Parser


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

        if edit[edit_type_k] == edit_insert_type:
            current_source = insert(
                current_source, edit[edit_start_k], edit[edit_text_k]
            )
            for gaze in gazes:
                new_gaze = gaze.copy()
                row, col = index_to_position[edit[edit_start_k]]

                lines_inserted = edit[edit_text_k].count("\n")

                if new_gaze[gaze_line_k] == row and new_gaze[gaze_col_k] >= col:
                    if lines_inserted > 0:
                        new_gaze[gaze_line_k] += lines_inserted
                        new_gaze[gaze_col_k] = new_gaze[gaze_col_k] - col
                    else:
                        new_gaze[gaze_col_k] += len(edit[edit_text_k])

                # if any lines were inserted, we need to
                elif new_gaze[gaze_line_k] > row:
                    # for that particular row
                    new_gaze[gaze_line_k] += lines_inserted

                modified_gazes.append(new_gaze)

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
                    print("skipping")
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
                        print("greater")
                        modified_gazes.append(new_gaze)
                    else:
                        print("not greater appending default")
                        modified_gazes.append(new_gaze)
                else:
                    print(f"Appending unchanged")
                    modified_gazes.append(new_gaze)
        gaze_sets.append(modified_gazes)
        current_gazes = modified_gazes
    return gaze_sets
