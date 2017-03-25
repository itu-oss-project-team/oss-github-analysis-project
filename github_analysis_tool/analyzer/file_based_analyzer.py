import collections

from github_analysis_tool.analyzer.abstract_analyzer import AbstractAnalyzer
from github_analysis_tool.services.db_column_constants import Columns


class FileBasedAnalyzer(AbstractAnalyzer):

    def __init__(self):
        AbstractAnalyzer.__init__(self, "file")

    def create_matrix(self, repo_id):
        # file_matrix is a 2D dict matrix
        file_matrix = collections.OrderedDict()
        commits = self._databaseService.get_commits_of_repo(repo_id, get_only_ids=True)
        repo_files = set()
        # For every commit in repo
        for commit_id in commits:
            files = self._databaseService.get_files_changes_of_commit(commit_id)
            commit_files = [file[Columns.FileChanges.path] for file in files]
            repo_files.update(commit_files)
            for file_path_1 in commit_files:
                for file_path_2 in commit_files:
                    # avoid self-loops
                    if file_path_1 != file_path_2:
                        # For every files changed together
                        self.__increment_commit_count(file_matrix, file_path_1, file_path_2)
        return file_matrix

    def __increment_commit_count(self, file_matrix, file_path_1, file_path_2):
        if file_path_1 not in file_matrix:
            file_matrix[file_path_1] = {}
        if file_path_2 in file_matrix[file_path_1]:
            file_matrix[file_path_1][file_path_2] += 1
        else:
            file_matrix[file_path_1][file_path_2] = 1