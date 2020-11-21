from gazel.core_types import Source, PositionMapping, Position, Range, Snapshot, Token
from gazel.common import create_position_index_mapping, Id
from gazel.parsing import get_tokens
from typing import Dict


def make_source(source: str, language: str) -> Source:
    itp, pti = create_position_index_mapping(source)

    return Source(source, PositionMapping(itp, pti), language)


def token_from_capture(
    capture, source: str, mapping: PositionMapping, token_id=None
) -> Token:
    (start, end), syntax_node = capture
    start_point = mapping[start]
    end_point = mapping[end]
    token_range = Range(Position(start, start_point), Position(end, end_point))

    return Token(range=token_range, syntax_node=syntax_node, id=token_id, source=source)


def make_snapshot(source: str, language: str, index=0, next_id=Id(),) -> Snapshot:
    _source = make_source(source, language)
    captures = get_tokens(source, language, _source.mapping.point_to_index)
    tokens = tuple(
        token_from_capture(capture, source, _source.mapping, token_id=next_id())
        for capture in captures
    )
    token_by_range: Dict[Range, Token] = {}
    for token in tokens:
        token_by_range[token.range] = token

    return Snapshot(index, _source, tokens, _token_by_range=token_by_range)
