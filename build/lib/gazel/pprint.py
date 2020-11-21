import pampy
from gazel.core_types import Position, TokenChange, Token, Snapshot, SnapshotDiff, Range


def get_range_text(r: Range, text: str) -> str:
    return text[r.start.index : r.end.index]


def __pprint_position(p: Position) -> str:
    return f"({p.point.line},{p.point.col})"


def _pprint_token(token: Token) -> str:
    text = get_range_text(token.range, token.source)

    return f'Token(text="{text}", pos={__pprint_position(token.range.start)}'


def _pprint_token_change(change: TokenChange) -> str:

    if change.type == "deleted":
        return f"deleted {_pprint_token(change.old)}"
    elif change.type == "edited":
        return f"edited {_pprint_token(change.old)} to {_pprint_token(change.new)}"
    elif change.type == "inserted":
        return f"inserted {_pprint_token(change.new)} @{__pprint_position(change.new.range.start)}"
    elif change.type == "moved":
        return f"moved {_pprint_token(change.new)} from {__pprint_position(change.old.range.start)} to {__pprint_position(change.new.range.start)}"


def _pprint(entity):
    # fmt: off
    return pampy.match(
        entity,
        Token, _pprint_token,
        TokenChange, _pprint_token_change,
        Position, __pprint_position,
        list, lambda l: "\n".join([_pprint(item) for item in l]),
        tuple, lambda l: "\n".join([_pprint(item) for item in l])
    )
    # fmt: on


def pprint(entity):
    output = _pprint(entity)

    print(output)
