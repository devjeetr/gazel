from typing import Tuple, List
from tree_sitter import Language, Parser, Tree, TreeCursor, Node
from common import create_position_index_mapping


def point_to_index(point, position_to_index, last=False):
    print(f"{point[0]}:{point[1]}")
    return (
        position_to_index[point[0]][point[1]]
        if not last
        else position_to_index[point[0]][point[1] - 1] + 1
    )


def add_query_indices(captures, position_to_index):
    print(captures)
    return [
        (
            (
                point_to_index(capture[0].start_point, position_to_index),
                point_to_index(capture[0].end_point, position_to_index, True),
            ),
            capture[1],
        )
        for capture in captures
    ]


def make_hash(start, end):
    return f"{start}:{end}"


def unhash(hs) -> Tuple[int, int]:
    return [int(item) for item in hs.split(":")]


def make_query_table(captures):
    table = {}

    for capture in captures:
        indices, name = capture
        hs = make_hash(*indices)
        if hs in table:
            previous = table[hs]
            if previous.count(".") < name.count("."):
                table[hs] = name
        else:
            table[hs] = name

    return table


def get_capture_for_gaze(gaze_position, table):
    gs, ge = gaze_position

    # find a table entry that completely contains
    # this gaze
    for k in table:
        start, end = unhash(k)
        if start <= gs and end >= ge:
            return k


def load_language(extension):
    if extension == "js":
        language = Language("languages/languages.so", "javascript")
        with open("./languages/javascript/queries/highlights.scm") as f:
            query_spec = f.read()

        return language, query_spec

    if extension == "cpp":
        language = Language("languages/languages.so", "cpp")
        with open("./languages/cpp/queries/highlights.scm") as f:
            query_spec = f.read()

        return language, query_spec
    raise Exception("No language for extension " + extension)


source = "let x = 20;"


def make_parse_table(source, language_extension):
    """Makes a table of source code tokens and their ranges,
    allowing you to look it up to assign syntax nodes to gazes
    using `get_capture_for_gaze`

    Args:
        source (string): contents of the source file
        language_extension (string): language extension

    Returns:
        dict: a table mapping from hashed start/end indices
             in the text to corresponding syntax class
    """
    language, query_spec = load_language(language_extension)
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(source, "utf-8"))
    query = language.query(query_spec)
    captures = query.captures(tree.root_node)
    _, pti = create_position_index_mapping(source)
    indexed_captures = add_query_indices(captures, pti)
    table = make_query_table(indexed_captures)

    return table


def make_parser(language):
    parser = Parser()
    parser.set_language(language)

    return parser


def get_captures(node, query_spec, language):
    query = language.query(query_spec)
    return query.captures(node)


# def get_tokens(source, language_extension, pti):
#     # print(source)

#     language, query_spec = load_language(language_extension)
#     parser = make_parser(language)
#     tree = parser.parse(bytes(source, "utf-8"))

#     captures = get_captures(tree.root_node, query_spec, language)
#     indexed_captures = add_query_indices(captures, pti)

#     seen = {}
#     for capture in indexed_captures:
#         indices, name = capture
#         previous_len = len(seen.get(indices, "").split("."))

#         if previous_len < len(name.split(".")) or indices not in seen:
#             seen[indices] = name

#     return list(seen.items())


def get_tokens(source, language_extension, pti):
    language, query_spec = load_language(language_extension)
    parser = make_parser(language)
    tree = parser.parse(bytes(source, "utf-8"))

    return extract_tokens_from_tree(tree)


def make_inverse_parse_table(parse_table: dict):
    table = {}
    for k, token_type in parse_table.items():
        start, end = unhash(k)

        for i in range(start, end):
            table[i] = ((start, end), token_type)

    return table


def make_move(cursor, move, fn):
    # think of the parameter "move" as the move that was made to
    # arrive at the present node
    if move == "down":
        fn(cursor)
        if cursor.goto_first_child():
            make_move(cursor, "down", fn)
        elif cursor.goto_next_sibling():
            make_move(cursor, "right", fn)
        elif cursor.goto_parent():
            make_move(cursor, "up", fn)
    elif move == "right":
        fn(cursor)
        if cursor.goto_first_child():
            make_move(cursor, "down", fn)
        elif cursor.goto_next_sibling():
            make_move(cursor, "right", fn)
        elif cursor.goto_parent():
            make_move(cursor, "up", fn)
    elif move == "up":
        if cursor.goto_next_sibling():
            make_move(cursor, "right", fn)
        elif cursor.goto_parent():
            make_move(cursor, "up", fn)


def is_child_node(node: Node) -> bool:
    return node.child_count == 0


def extract_tokens_from_tree(tree: Tree) -> List[Tuple[Tuple[int], str]]:
    cursor: TreeCursor = tree.walk()
    children = []

    def walker(cusor: TreeCursor):
        if is_child_node(cursor.node):
            indices = (cursor.node.start_byte, cursor.node.end_byte)
            children.append((indices, cursor.node.type))

    make_move(cursor, "down", walker)

    return children


def my_fn(cursor):

    # print(cursor.node.start_byte, cursor.node.end_byte)
    # print(cursor.node.has_changes)
    if cursor.node.child_count == 0:
        print(cursor.node.type)

