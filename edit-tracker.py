import pandas as pd
from argparse import ArgumentParser
import os
import json
from typing import List
from common import Id
from identifiers import TokenSet, Token, token_info_for_delete, token_info_for_insert
from copy import deepcopy


def cmd_args():
    parser = ArgumentParser()

    parser.add_argument("--gaze", help="path to gaze file")
    parser.add_argument("--edits", help="path to edits file")
    parser.add_argument("--source", help="path to source file")


def add_identifier_ids(gazes, edits, versions: List[TokenSet]):
    """Adds identifier ids to gazes. These stay consistent over time.
       
        You can use these ids to aggregate gazes over any specific identifier in the code.
    Args:
        gazes ([type]): [description]
        edits ([type]): [description]
        versions (List[TokenSet]): [description]
    """
    next_edit_i = 0
    current_version = 0
    gazes = deepcopy(gazes)

    for gaze in gazes:
        if gaze["system_time"] > edits[next_edit_i]["timestamp"]:
            assert current_version + 1 < len(
                versions
            ), "Inconsistency between changelog & number of source versions"
            current_version += 1
            if next_edit_i + 1 < len(edits):
                next_edit_i += 1

        # TODO: for once we add filenames to change logs
        # if gaze["filename"] == edits[next_edit_i - 1]["filename"]:

        line, col = gaze["source_file_line"], gaze["source_file_col"]
        token_set = versions[current_version]
        index = token_set.pti[line][col]
        token = token_set.token_at(index)

        if token:
            gaze["syntax_node"] = token.syntax_node
            gaze["syntax_node_id"] = token.id
        else:
            gaze["syntax_node"] = "invalid"
            gaze["syntax_node_id"] = "nan"

        if next_edit_i - 1 < 0:
            gaze["last_edit"] = "none"
        else:
            gaze["last_edit"] = edits[next_edit_i - 1]["timestamp"]

    return gazes


def get_source_versions(source, edits, extension):
    next_id = Id()
    current_version = TokenSet(source, extension)

    versions = [current_version]
    current_version.assign_ids(next_id)

    for edit in edits:

        offset = current_version.pti[edit["row"]][edit["col"]]
        edit = {**edit, "offset": offset}
        if edit["type"] == "insert":
            start = edit["offset"]
            text = edit["text"]
            next_version = token_info_for_insert(current_version, start, text, next_id)
            assert next_version.source[start] == text
            versions.append(next_version)
            current_version = next_version
        elif edit["type"] == "delete":
            start = edit["offset"]
            size = edit["len"]

            next_version = token_info_for_delete(current_version, start, size, next_id)
            versions.append(next_version)
            current_version = next_version

    return versions


def main():
    # example usage
    root = "/home/devjeetroy/Research/itrace/sandbox/demo-data2"
    gaze_file_name = "fixations.json"
    with open(os.path.join(root, gaze_file_name)) as f:
        gazes = json.load(f)
    with open(os.path.join(root, "changelog.json")) as f:
        change_log = json.load(f)["log"]

    with open(os.path.join(root, "sourceOutput-Sample-Data-1602690815285.cpp")) as f:
        source = f.read()  # .replace("\r\n", "\n")

    extension = "cpp"
    change_log = list(filter(len, change_log))
    versions = get_source_versions(source, change_log, extension)
    annotated_gazes = add_identifier_ids(gazes, change_log, versions)
    i = 0
    for version in versions:
        changed = version.get_changed()
        if changed:
            i += 1
        for token in changed:
            print(token.text(version.source))

    with open("test-output.json", "w") as f:
        json.dump([gaze for gaze in annotated_gazes], f)


if __name__ == "__main__":
    main()
