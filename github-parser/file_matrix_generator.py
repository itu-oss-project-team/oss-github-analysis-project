from database_service import DatabaseService
from db_coloumn_constants import Coloumns
import os.path
import sys
import yaml

class FileMatrixGenerator:

    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def crate_matrix(self, repo_id):
        # file_matrix is a 2D dict matrix
        file_matrix = {}
        commits = self.__databaseService.getCommitsOfRepo(repo_id, get_only_shas=True)
        repo_files = set()
        # For every commit in repo
        for commit_sha in commits:
            files = self.__databaseService.getFilesChangesOfCommit(commit_sha)
            commit_files = [file[Coloumns.FileChanges.path] for file in files]
            repo_files.update(commit_files)
            for file_path_1 in commit_files:
                for file_path_2 in commit_files:
                    # For every files changed togehter
                    self.__increment_commit_count(file_matrix, file_path_1, file_path_2)

        with open(str(repo_id) + "_filematrix.csv", "w") as out_file:
            out_file.write(";")
            for file in repo_files:
                out_file.write("%s;" % file)
            out_file.write("\n")
            for file_1 in repo_files:
                out_file.write("%s;" % file_1)
                for file_2 in repo_files:
                    if not file_2 in file_matrix[file_1]:
                        out_file.write("%d;" % 0)
                    else:
                        out_file.write("%d;" % file_matrix[file_1][file_2])
                out_file.write("\n")

    def __increment_commit_count(self, file_matrix, file_path_1, file_path_2):
        if file_path_1 not in file_matrix:
            file_matrix[file_path_1] = {}
        if file_path_2 in file_matrix[file_path_1]:
            file_matrix[file_path_1][file_path_2] += 1
        else:
            file_matrix[file_path_1][file_path_2] = 1

def main():

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config.yaml'), 'r') as ymlfile:
        config = yaml.load(ymlfile)

    with open(os.path.join(os.path.dirname(__file__), os.pardir, 'config_secret.yaml'), 'r') as ymlfile:
        secret_config = yaml.load(ymlfile)

    f = FileMatrixGenerator(secret_config)
    f.crate_matrix(71659875)

main()
