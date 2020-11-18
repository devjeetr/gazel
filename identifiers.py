from typing import Tuple, Union, Iterable, List
from common import create_position_index_mapping, Id, insert, delete
from parsing import get_tokens

# start index, end index
# start line/col, end line/col


class Token:
    def __init__(self, indices, name, token_id):
        self.start, self.end = indices
        self.name = name
        self.id = token_id

    @staticmethod
    def from_capture_tuple(capture, token_id=None):
        (start, end), name = capture
        return Token((start, end), name, token_id)

    def range(self):
        return (self.start, self.end)

    def shift(self, n=0):
        return Token((self.start + n, self.end + n), self.name, self.id)

    def overlaps(self, token_range):
        start, end = token_range
        if self.start >= start and self.start < end:
            return True
        if self.end >= start and self.end < end:
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

    def at(self, token_range) -> Token:
        if token_range in self.token_map:
            return self.tokens[self.token_map[token_range]]
        raise Exception("Invalid token range")

    def __repr__(self):
        items = []

        for token in self.tokens:
            print(token)
            items.append(f"{token.text(self.source)}: {token.id}")

        return "\n".join(items)


def token_info_for_insert(old_tokens: TokenSet, start, text, next_id=Id()):
    new_source = insert(old_tokens.source, start, text)

    new_tokens = TokenSet(new_source, old_tokens.language)
    affected_range = (start, start + len(text))
    shift = len(text)

    for token in new_tokens.tokens:
        if token.overlaps(affected_range):
            # affected token, assign new id
            token.id = next_id()
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


def diff_token_sets(a: TokenSet, b: TokenSet):
    a_ids = {token.id: token for token in a.tokens}
    b_ids = {token.id: token for token in b.tokens}
    deleted = [token for tid, token in a_ids.items() if tid not in b_ids]
    added = [token for tid, token in b_ids.items() if tid not in a_ids]
    changed = []

    for token_id in a_ids.keys() & b_ids.keys():
        a_token = a_ids[token_id]
        b_token = b_ids[token_id]

        if a_token.range() != b_token.range():
            changed.append((a_token, b_token))

    return (added, deleted, changed)


def print_diff(diff, old_source, new_source):
    added, deleted, changed = diff

    print("Added: ")
    for token in added:
        print("* " + token.text(new_source))

    print("\ndeleted: ")
    for token in deleted:
        print("* " + token.text(old_source))

    # print("shifted: ")
    # for a, b in changed:
    #     print(f"* {a.text(old_source)} -> {b.text(new_source)}")


source = """
function getGrades() {
    var args = Array.prototype.slice.call(arguments, 1, 3);
    return args;
}

// Let's output this!
console.log(getGrades(90, 100, 75, 40, 89, 95));
"""
id_generator = Id()
token_set = TokenSet(source, "js")
token_set.assign_ids(id_generator)

new_tokens = token_info_for_delete(token_set, 11, 5, id_generator)
diff = diff_token_sets(token_set, new_tokens)

print("Printing diff")
print_diff(diff, token_set.source, new_tokens.source)

