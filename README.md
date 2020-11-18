## Check edit-tracker main() for example

TokenSets form versions of a file.

`edit_tracker.get_source_versions` constructs a array of tokenset that can be traversed through edits.

at index 0 is original file, index 1 is file after first edit.

At each version, you can get a list of tokens that changed using 

`changed_tokens = token_set.get_changed()` which returns a list of tokens.

each token has an `id`, `syntax_node` and `changed`. Changed tells you if this token is newly inserted.


you can also use the `versions` array with `add_identifier_ids` to annotate gaze data with token information. You can then use the resulting json to aggregate fixations across edits or track tokens across edits using the token ids.