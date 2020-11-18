from typing import Tuple, Union, Iterable, List
from common import create_position_index_mapping, Id, insert, delete
from parsing import get_tokens
from TokenSet import TokenSet
from Token import Token


def token_info_for_insert(
    old_tokens: TokenSet, start: int, text: str, next_id=Id(), edit_time=None
):
    new_source = insert(old_tokens.source, start, text)

    assert new_source[start] == text
    assert len(new_source) == len(old_tokens.source) + len(text)

    new_tokens = TokenSet(new_source, old_tokens.language)
    affected_range = (start, start + len(text))
    shift = len(text)
    for token in new_tokens.tokens:
        if token.overlaps(affected_range):
            # affected token, assign new id
            token.id = next_id()
            token.changed = True

            token.last_edited = edit_time
        else:
            if token.start >= affected_range[1]:
                old_range = token.shift(-shift).range()
                if old_tokens.contains(old_range):
                    previous_token = old_tokens.at(old_range)
                    token.id = previous_token.id

                    assert token.start == previous_token.start + shift
                    assert token.end == previous_token.end + shift
                else:
                    token.id = next_id()
                    token.changed = True

                token.last_edited = edit_time
    return new_tokens


def token_info_for_delete(
    old_tokens: TokenSet, start, size, next_id=Id(), edit_time=None
):
    new_source, _ = delete(old_tokens.source, start, size)

    new_tokens = TokenSet(new_source, old_tokens.language)
    affected_range = (start, start + size)
    shift = size
    
    for token in new_tokens.tokens:
        if token.overlaps(affected_range):
            # affected token, assign new id
            token.token_id = next_id()
            token.last_edited = edit_time
        else:
            # only tokens that start after the
            # end of the affected range need
            # to be adjusted
            if token.start >= affected_range[1]:
                # we want to use the same if if
                # this token exists in the old token
                # set
                old_range = token.shift(shift).range()
                if old_tokens.contains(old_range):
                    previous_token = old_tokens.at(old_range)
                    token.id = previous_token.id
                    assert token.start == previous_token.start - shift
                    assert token.end == previous_token.end - shift
                else:
                    # newly inserted token
                    # this should actually never happen?
                    token.id = next_id()

                token.last_edited = edit_time
    return new_tokens

