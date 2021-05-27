from typing import Callable, List, Literal, Optional, Tuple, Union

import pampy

from gazel.common import Id
from gazel.core_constructors import make_snapshot
from gazel.core_types import Snapshot, Token, TokenChange
from gazel.range import (
    _shift_range,
    get_token_at_range,
    range_contains,
    range_overlaps,
    same_point_range,
)


def insert(source: str, start: int, text: str) -> str:
    return source[:start] + text + source[start:]


def delete(source: str, start: int, size: int) -> str:
    return source[:start] + source[start + size :]


def get_change(old: Token = None, new: Token = None) -> Optional[TokenChange]:
    if old and new:
        if not same_point_range(old.range, new.range):
            return TokenChange(type="moved", old=old, new=new)
    elif not old and new:
        return TokenChange(type="inserted", old=old, new=new)
    elif old and not new:
        return TokenChange(type="deleted", old=old, new=new)

    return None


def _adjust_tokens_for_edit(
    old_snapshot: Snapshot,
    new_snapshot: Snapshot,
    direction: Literal["left", "right"],
    affected_index_range: Tuple[int, int],
    next_id=Id(),
):
    shift = affected_index_range[1] - affected_index_range[0]
    shift = pampy.match(direction, "left", -shift, "right", shift)
    adjusted_tokens: List[Token] = []
    changes: List[TokenChange] = []

    # FIXME
    # deleted tokens do not get reported to
    # the change list.
    for token in new_snapshot.tokens:
        if range_overlaps(
            affected_index_range, (token.range.start.index, token.range.end.index)
        ):
            old_token = get_token_at_range(old_snapshot, affected_index_range)
            new_token = Token(token.range, token.source, next_id(), token.syntax_node)
            change = None
            if old_token:
                old_token_index_range = (
                    old_token.range.start.index,
                    old_token.range.end.index,
                )
                if range_contains(
                    old_token_index_range, affected_index_range
                ):  # means we deleted, and hence
                    new_token = Token(
                        new_token.range,
                        new_token.source,
                        old_token.id,
                        new_token.syntax_node,
                    )

                    change = TokenChange(type="edited", old=old_token, new=new_token)
            else:
                change = get_change(old=None, new=new_token)

            adjusted_tokens.append(new_token)
            if change:
                changes.append(change)
        else:
            # only tokens that start after the
            # end of the affected range need
            # to be adjusted
            if token.range.start.index >= affected_index_range[1]:
                old_range = _shift_range(
                    token.range, -shift, old_snapshot.source.mapping
                )
                if old_range in old_snapshot._token_by_range:
                    old_token = old_snapshot._token_by_range[old_range]
                    new_token = Token(
                        source=token.source,
                        range=token.range,
                        syntax_node=token.syntax_node,
                        id=old_token.id,
                    )
                    adjusted_tokens.append(new_token)
                    change = get_change(old_token, new_token)
                    if change:
                        changes.append(change)

    return adjusted_tokens, changes


def token_info_for_delete(
    old_snapshot: Snapshot, line: int, col: int, size: int, next_id=Id(), id=0, time=0.0
):
    start = old_snapshot.source.mapping[line, col]
    affected_range = (start, start + size)
    new_source = delete(old_snapshot.source.text, start, size)

    new_snapshot = make_snapshot(new_source, old_snapshot.source.language, index=id,)

    tokens, changes = _adjust_tokens_for_edit(
        old_snapshot, new_snapshot, "left", affected_range, next_id
    )

    return Snapshot(
        id=new_snapshot.id,
        source=new_snapshot.source,
        tokens=tokens,
        changes=changes,
        _token_by_range=new_snapshot._token_by_range,
        time=time,
    )


def token_info_for_insert(
    old_snapshot: Snapshot, line: int, col: int, text: str, next_id=Id(), id=0, time=0.0
):
    start = old_snapshot.source.mapping[line, col]
    new_source = insert(old_snapshot.source.text, start, text)

    new_snapshot = make_snapshot(new_source, old_snapshot.source.language, index=id,)
    affected_range = (start, start + len(text))

    tokens, changes = _adjust_tokens_for_edit(
        old_snapshot, new_snapshot, "right", affected_range, next_id
    )
    return Snapshot(
        id=new_snapshot.id,
        source=new_snapshot.source,
        tokens=tokens,
        changes=changes,
        _token_by_range=new_snapshot._token_by_range,
        time=time,
    )


def _perform_aggregated_edit(
    snapshot: Snapshot, edits: dict, next_id: Callable[[], Union[str, float, int]], id=0
) -> Snapshot:
    current_snapshot = snapshot
    changes: List[TokenChange] = []

    for edit in edits["edits"]:
        current_snapshot = edit_source(current_snapshot, edit, next_id, id=id)
        changes.extend(current_snapshot.changes)

    return Snapshot(
        id=id,
        source=current_snapshot.source,
        tokens=current_snapshot.tokens,
        time=edits["edits"][0]["timestamp"],
        changes=tuple(changes),
        _token_by_range=current_snapshot._token_by_range,
    )


def edit_source(
    snapshot: Snapshot, edit: dict, next_id: Callable[[], Union[str, float, int]], id=0
) -> Snapshot:
    return pampy.match(
        edit,
        {"type": "insert"},
        lambda edit: token_info_for_insert(
            snapshot,
            line=edit["row"],
            col=edit["col"],
            text=edit["text"],
            next_id=next_id,
            id=id,
            time=edit["timestamp"],
        ),
        {"type": "delete"},
        lambda edit: token_info_for_delete(
            snapshot,
            line=edit["row"],
            col=edit["col"],
            size=edit["len"],
            next_id=next_id,
            id=id,
            time=edit["timestamp"],
        ),
        {"type": "aggregated"},
        lambda edit: _perform_aggregated_edit(snapshot, edit, next_id, id=id),
    )

