from typing import Tuple, Union, Iterable, List
from common import create_position_index_mapping, Id, insert, delete
from parsing import get_tokens

# start index, end index
# start line/col, end line/col


class Token:
    def __init__(self, indices, syntax_node, token_id, changed=False):
        self.start, self.end = indices
        self.syntax_node = syntax_node
        self.id = token_id
        self.changed = changed
        
    @staticmethod
    def from_capture_tuple(capture, token_id=None):
        (start, end), syntax_node = capture
        return Token((start, end), syntax_node, token_id)

    def range(self):
        return (self.start, self.end)

    def shift(self, n=0):
        return Token(
            (self.start + n, self.end + n),
            self.syntax_node,
            self.id,
            changed=self.changed,
        )

    def __repr__(self,):
        return f"range: [{self.start}, {self.end}], syntax_node: {self.syntax_node}, id: {self.id}, changed: {self.changed}"

    def overlaps(self, token_range):
        if isinstance(token_range, (tuple, list)):
            start, end = token_range
            if self.start >= start and self.start < end:
                return True
            if self.end > start and self.end <= end:
                return True
        elif isinstance(token_range, int):
            # print("is int")
            if token_range >= self.start and token_range < self.end:
                return True
        return False

    def text(self, source: str):
        return source[self.start : self.end]


class TokenSet:
    def __init__(self, source, language, tokens=None, itp=None, pti=None):
        self.source = source
        self.language = language

        if not itp or not pti:
            itp, pti = create_position_index_mapping(source)

        self.itp, self.pti = itp, pti

        if tokens is None:
            tokens = [
                Token.from_capture_tuple(capture)
                for capture in get_tokens(source, language, pti)
            ]
        self.tokens = tokens
        self.token_map = {}

        for i, token in enumerate(self.tokens):
            self.token_map[token.range()] = i

    def assign_ids(self, next_id):
        if not next_id:
            return

        for token in self.tokens:
            token.id = next_id()

    def contains(self, token_range):
        return token_range in self.token_map

    def token_at(self, index):
        for token in self.tokens:
            if token.overlaps(index):
                return token
        return False

    def at(self, token_range) -> Token:
        if token_range in self.token_map:
            return self.tokens[self.token_map[token_range]]
        raise Exception("Invalid token range")

    def get_changed(self) -> List[Token]:
        return [token for token in self.tokens if token.changed]

    def __repr__(self):
        items = []

        for token in self.tokens:
            items.append(f"{token.text(self.source)}: {token.id}")

        return "\n".join(items)


from dataclasses import dataclass


def token_info_for_insert(old_tokens: TokenSet, start, text, next_id=Id()):
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
    return new_tokens


def token_info_for_delete(old_tokens: TokenSet, start, size, next_id=Id()):
    new_source, _ = delete(old_tokens.source, start, size)

    new_tokens = TokenSet(new_source, old_tokens.language)
    affected_range = (start, start + size)
    shift = size
    for token in new_tokens.tokens:
        if token.overlaps(affected_range):
            # affected token, assign new id
            token.token_id = next_id()
        else:
            if token.start >= affected_range[1]:
                old_range = token.shift(shift).range()
                if old_tokens.contains(old_range):
                    previous_token = old_tokens.at(old_range)
                    token.id = previous_token.id
                    assert token.start == previous_token.start - shift
                    assert token.end == previous_token.end - shift
                else:
                    token.id = next_id()

    return new_tokens

