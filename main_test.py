from main import perform_adjustments, create_position_index_mapping


def make_gazes(gazes):
    return [{"line": line, "col": col, "time": 0} for (line, col) in gazes]


def test_when_text_is_added_to_line():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(0, 4), (0, 6)])
    edits = [{"type": "insert", "start": 5, "text": "ab", "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]

    assert adjusted[0] == gazes[0]
    assert adjusted[1]["line"] == gazes[1]["line"]
    assert adjusted[1]["col"] == gazes[1]["col"] + 2


def test_when_newline_is_added_to_line():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(0, 4), (0, 6)])
    edits = [{"type": "insert", "start": 5, "text": "ab\n", "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]

    assert adjusted[0] == gazes[0]
    assert adjusted[1]["line"] == gazes[1]["line"] + 1
    assert adjusted[1]["col"] == 1


def test_when_newline_is_added_to_line_2():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(0, 4), (0, 6)])
    edits = [{"type": "insert", "start": 1, "text": "ab\n", "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]

    assert adjusted[0]["line"] == 1
    assert adjusted[0]["col"] == 3
    assert adjusted[1]["line"] == 1
    assert adjusted[1]["col"] == 5


def test_when_multiple_newline_is_added_to_line_2():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(0, 4), (0, 6)])
    edits = [{"type": "insert", "start": 1, "text": "\nab\n", "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]

    assert adjusted[0]["line"] == 2
    assert adjusted[0]["col"] == 3
    assert adjusted[1]["line"] == 2
    assert adjusted[1]["col"] == 5


def test_when_text_deleted_same_line():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(0, 4), (0, 6)])
    edits = [{"type": "delete", "start": 5, "size": 1, "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]
    print(adjusted)
    assert adjusted[0]["line"] == 0
    assert adjusted[0]["col"] == 4
    assert adjusted[1]["line"] == 0
    assert adjusted[1]["col"] == 5


def test_when_text_containing_gaze_is_deleted():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(0, 4), (0, 6)])
    edits = [{"type": "delete", "start": 6, "size": 1, "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]
    assert len(adjusted) == 1
    assert adjusted[0]["line"] == 0
    assert adjusted[0]["col"] == 4


def test_when_deleting_entire_line():
    source = "\n".join(["0123456", "0123456",])

    gazes = make_gazes([(1, 4), (1, 6)])
    edits = [{"type": "delete", "start": 0, "size": 8, "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]
    assert adjusted[0]["line"] == 0
    assert adjusted[0]["col"] == 4
    assert adjusted[1]["line"] == 0
    assert adjusted[1]["col"] == 6


def test_when_deleting_middle_of_line():
    source = "\n".join(["0123456", "0123456", "0123456"])

    gazes = make_gazes([(1, 4), (1, 6), (2, 6)])
    edits = [{"type": "delete", "start": 3, "size": 7, "time": 2}]

    adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]
    assert adjusted[0]["line"] == 0
    assert adjusted[0]["col"] == 5
    assert adjusted[1]["line"] == 0
    assert adjusted[1]["col"] == 7

    assert adjusted[2]["line"] == 1
    assert adjusted[2]["col"] == 6


# def test_when_multiple_edits():
    # source = "\n".join(["let x = 22;", "let y = 33;",])

    # gazes = make_gazes([(0, 4), (0, 6)])
    # edits = [
    #     {
    #         "type": "insert",
    #         "start": len(source) - 1,
    #         "text": "let z = x + y;",
    #         "time": 2,
    #     }
    # ]

    # adjusted = perform_adjustments(gazes, edits, source, language_extension="js")[1]

#     assert adjusted[0] == gazes[0]
#     assert adjusted[1]["line"] == gazes[1]["line"]
#     assert adjusted[1]["col"] == gazes[1]["col"] + 2
