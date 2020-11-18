from typing import List, Tuple
from edit_tracker import get_source_versions, add_identifier_ids
from TokenSet import TokenSet


class Tracker:
    def __init__(
        self,
        source: str,
        gazes: List[dict],
        changelog: List[dict],
        source_language: str,
    ):
        self.source_versions = get_source_versions(source, changelog, source_language)
        self.gazes = add_identifier_ids(gazes, changelog, self.source_versions)
        self.changelog = changelog
        self.source_language = source_language

    @staticmethod
    def from_files(source_file: str, gaze_file: str, changelog_file: str) -> Tracker:
        pass

    def get_edit_window(self, time: int):
        pass

    def get_gazes_for_window(self, start_time: int, end_time: int):
        """Gets the gazes specified in that time window.

        Args:
            start_time (int): [description]
            end_time (int): [description]
        """
        pass

    def _get_version_at_time(self, time: int):
        # find the edit that occured before time
        for i, edit in enumerate(self.changelog):
            if edit["timestamp"] > time:
                return self.source_versions[i]

    def get_tokens_at_time(self, time: int) -> TokenSet:
        version = self._get_version_at_time(time)

        return version

    def _get_first_version_idx_with_token_id(
        self,
        token_id: int,
        start_time: float = float("-inf"),
        end_time: float = float("inf"),
    ) -> int:

        for i, edit in enumerate(self.changelog):
            if edit["timestamp"] >= start_time and edit["timestamp"] < end_time:
                version = self.source_versions[i + 1]
                if version.contains_token_with_id(token_id):
                    return i + 1
        raise Exception(
            "Invalid token id: No token with the given id exists in tracker"
        )

    def get_token_history(
        self, token_id: int, start_time=float("-inf"), end_time=float("inf")
    ):
        """For a given token_id, it 

        Args:
            token_id (int): [description]
            time (int, optional): [description]. Defaults to None.
        """

        start_i = self._get_first_version_idx_with_token_id(
            token_id, start_time=start_time, end_time=end_time
        )
        
        for i in range(start_i + 1, len(self.source_versions)):
            current_version = self.source_versions[i]

            

