from typing import Tuple, List, Literal
from tree_sitter import Language, Parser, Tree, TreeCursor, Node


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


def make_parser(language):
    parser = Parser()
    parser.set_language(language)

    return parser


def get_tokens(source: str, language_extension: str, pti):
    language, _ = load_language(language_extension)
    parser = make_parser(language)
    tree = parser.parse(bytes(source, "utf-8"))

    return extract_tokens_from_tree(tree)


def walk_tree(cursor: TreeCursor, move: Literal["down", "up", "right"], fn) -> None:
    """Visits every node starting at the given cursor position,
       calling 'fn' for each node.

    Args:
        cursor (TreeCursor): tree cursor to traverse
        move (Literal["down", "up", "right"]): the move made to get to current cursor position
        fn (function): the visitor function to apply to each node.
    """
    if move in ("down", "right"):
        fn(cursor)
        if cursor.goto_first_child():
            walk_tree(cursor, "down", fn)
        elif cursor.goto_next_sibling():
            walk_tree(cursor, "right", fn)
        elif cursor.goto_parent():
            walk_tree(cursor, "up", fn)
    elif move == "up":
        if cursor.goto_next_sibling():
            walk_tree(cursor, "right", fn)
        elif cursor.goto_parent():
            walk_tree(cursor, "up", fn)


def is_child_node(node: Node) -> bool:
    return node.child_count == 0


def extract_tokens_from_tree(tree: Tree) -> List[Tuple[Tuple[int], str]]:
    """Walks the given tree, in a depth first manner, 
    and extracts token indices from all child nodes

    Args:
        tree (Tree): target tree

    Returns:
        List[Tuple[Tuple[int], str]]: [description]
    """
    cursor: TreeCursor = tree.walk()
    children = []

    def walker(cusor: TreeCursor):
        if is_child_node(cursor.node):
            indices = (cursor.node.start_byte, cursor.node.end_byte)
            children.append((indices, cursor.node.type))

    walk_tree(cursor, "down", walker)

    return children

