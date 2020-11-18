from Token import Token
from common import create_position_index_mapping
from parsing import get_tokens
from typing import List


class TokenSet:
    def __init__(self, source: str, language, tokens=None, itp=None, pti=None):
        self.source = source
        self.language = language

        if not itp or not pti:
            itp, pti = create_position_index_mapping(source)

        self.itp, self.pti = itp, pti

        if tokens is None:
            tokens = [
                Token.from_capture_tuple(capture, source)
                for capture in get_tokens(source, language, pti)
            ]

        self.tokens = tokens
        self.token_map = {}

        for i, token in enumerate(self.tokens):
            self.token_map[token.range()] = i

    def contains_token_with_id(self, token_id: int) -> bool:
        for token in self.tokens:
            if token.id == token_id:
                return True
        return False

    def get_token_with_id(self, token_id):
        pass

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
            items.append(f"{token.text()}: {token.id}")

        return "\n".join(items)

