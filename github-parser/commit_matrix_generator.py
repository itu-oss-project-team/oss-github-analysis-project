from datetime import datetime
import time

from database_service import DatabaseService

class CommitMatrixGenerator:

    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def crate_matrix(self, repo_id):
        start_time = time.time()

        # commit_matrix is a 2D dict matrix
        commit_matrix = {}
        repo_files = self.__databaseService.getFilesOfRepo(repo_id, get_only_file_names=True)

        # For every file in repo
        for file_name in repo_files:
            file_commits = self.__databaseService.getCommitsOfFile(repo_id, file_name, get_only_ids=True)
            for file_commit_1 in file_commits:
                for file_commit_2 in file_commits:
                    # For every commit pair that edits this same file
                    self.__increment_file_count(commit_matrix, file_commit_1, file_commit_2)

        with open(str(repo_id) + "_commitmatrix.txt", "w") as out_file:
            repo_commits = self.__databaseService.getCommitsOfRepo(repo_id, get_only_ids=True)
            for commit_id in repo_commits:
                out_file.write("%s\n" % commit_id)

            out_file.write("\n")

            for commit_1 in repo_commits:
                for commit_2 in repo_commits:
                    if commit_1 not in commit_matrix:
                        out_file.write("%2d " % 0)
                    elif commit_2 not in commit_matrix[commit_1]:
                        out_file.write("%2d " % 0)
                    else:
                        out_file.write("%2d " % commit_matrix[commit_1][commit_2])
                out_file.write("\n")

        elapsed_time = time.time() - start_time
        print("---> Commit matrix generated for repo (" + str(repo_id) + ") in " + str(elapsed_time) + " seconds.")

    def __increment_file_count(self, commit_matrix, commit_sha_1, commit_sha_2):
        if commit_sha_1 not in commit_matrix:
            commit_matrix[commit_sha_1] = {}
        if commit_sha_2 in commit_matrix[commit_sha_1]:
            commit_matrix[commit_sha_1][commit_sha_2] += 1
        else:
            commit_matrix[commit_sha_1][commit_sha_2] = 1