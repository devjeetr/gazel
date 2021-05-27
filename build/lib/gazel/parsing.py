
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple, cast

from git import Repo
from tqdm.auto import tqdm
from tree_sitter import Language, Node, Parser, Tree, TreeCursor

SUPPORTED_LANGUAGES = {
    "java": "java",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "cpp": "cpp",
    "cs": "c-sharp",
    "go": "go",
    "yml": "yaml",
    "yaml": "yaml",
    "elm": "elm",
    "c": "c",
    "py": "python",
    "lua": "lua",
    "rb": "ruby",
    "r": "r",
    "R": "r",
    "rs": "rust",
    "php": "php",
    "ocaml": "ocaml",
    "toml": "toml",
    "jl": "julia",
}


def clone_repo(repo_url: str, repo_path: str):
    def make_progress():
        bar = tqdm()
        total = None

        def progress_reporter(op_code, curr_count, max_count, message):
            nonlocal total
            if total is None:
                total = max_count
                bar.reset(total=total)

            bar.update(curr_count)

            if curr_count == max_count:
                bar.close()

        return progress_reporter

    repo = Repo.clone_from(repo_url, repo_path, progress=make_progress())
    del repo


def get_repo_path(cache_dir: str, language: str):
    return os.path.join(cache_dir, f"tree-sitter-{language}")


def build_language_library(cache_dir: str, library_path: str):
    language_repo_paths = []
    for language in SUPPORTED_LANGUAGES:
        repo_name = f"tree-sitter-{language}"
        repo_path = get_repo_path(cache_dir, language)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if not os.path.exists(repo_path):
            clone_repo(f"https://github.com/tree-sitter/{repo_name}", repo_path)
        language_repo_paths.append(repo_path)

    Language.build_library(
        library_path, language_repo_paths,
    )


def load_language(
    extension: str,
    cache_dir: Optional[str] = None,
    language_library: Optional[str] = None,
) -> Parser:
    if not cache_dir:
        cache_dir = Path().home() / ".cache" / "tree-sitter-grammars"
    if not language_library:
        language_library = "language_lib.so"
    assert (
        extension in SUPPORTED_LANGUAGES
    ), f"Invalid language, can be one of [{', '.join(SUPPORTED_LANGUAGES)}]"
    language_library = os.path.join(cache_dir, language_library)

    if not os.path.exists(language_library):
        build_language_library(cache_dir=cache_dir, library_path=language_library)

    language = SUPPORTED_LANGUAGES[extension]
    grammar = Language(language_library, language)

    return grammar


def make_parser(language):
    parser = Parser()
    parser.set_language(language)

    return parser


def get_tokens(source: str, language_extension: str, pti):
    language = load_language(language_extension)
    parser = make_parser(language)
    tree = parser.parse(bytes(source, "utf-8"))
    captures = extract_tokens_from_tree(tree)

    return captures


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
    children: List[Tuple[Tuple[int], str]] = []

    def walker(cursor: TreeCursor):
        if is_child_node(cursor.node):
            indices: Tuple[int] = cast(
                Tuple[int], (cursor.node.start_byte, cursor.node.end_byte)
            )
            children.append((indices, cursor.node.type))

    walk_tree(cursor, "down", walker)

    return children

