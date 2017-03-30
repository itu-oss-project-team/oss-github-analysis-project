import collections

from github_analysis_tool.analyzer.abstract_analyzer import AbstractAnalyzer
from github_analysis_tool.services.db_column_constants import Columns

class CommitBasedAnalyzer(AbstractAnalyzer):
    def __init__(self):
        AbstractAnalyzer.__init__(self, "commit")

    def create_matrix(self, repo_id):
        commit_matrix = collections.OrderedDict()          # {<commit1>:{<commit2>:<shared_file_changes>}
        commit_file_counts = collections.OrderedDict()     # {<commit>:<file_count>}

        repo_files = self._databaseService.get_files_of_repo(repo_id, get_only_file_paths=True)

        # For every file in repo
        for file_name in repo_files:
            commits_of_file = self._databaseService.get_commits_of_file(repo_id, file_name, get_only_ids=True)

            for commit in commits_of_file:
                # Count how many files are there in each commit so we can normalize our matrix later with these counts
                self.__increment_commit_file_count(commit_file_counts, commit)

            for commit_1 in commits_of_file:
                for commit_2 in commits_of_file:
                    # For every commit pair that edits this same file
                    self.__increment_file_count(commit_matrix, commit_1, commit_2)

        self.__normalize_matrix(commit_matrix, commit_file_counts)
        return commit_matrix

    def __increment_file_count(self, commit_matrix, commit_1, commit_2):
        if commit_1 == commit_2:
            return

        if commit_1 not in commit_matrix:
            commit_matrix[commit_1] = {}
        if commit_2 in commit_matrix[commit_1]:
            commit_matrix[commit_1][commit_2] += 1
        else:
            commit_matrix[commit_1][commit_2] = 1

    def __increment_commit_file_count(self, commit_file_counts, commit):
        if commit not in commit_file_counts:
            commit_file_counts[commit] = 1
        else:
            commit_file_counts[commit] += 1

    def __normalize_matrix(self, commit_matrix, commit_file_counts):
        for commit_1 in commit_matrix.keys():
            for commit_2 in commit_matrix.keys():
                if commit_2 not in commit_matrix[commit_1]:
                    continue
                intersectCount = commit_matrix[commit_1][commit_2]
                unionCount = commit_file_counts[commit_1] + commit_file_counts[commit_2] - intersectCount
                test = intersectCount / unionCount
                commit_matrix[commit_1][commit_2] = intersectCount / unionCount
