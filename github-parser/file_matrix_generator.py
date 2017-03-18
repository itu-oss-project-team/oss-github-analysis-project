from database_service import DatabaseService
from db_column_constants import Columns
import time
from graph_tool.all import *
from graph_service import StringKeyGraph
import os.path
import gc

class FileMatrixGenerator:
    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def create_matrix(self, repo_id, repo_full_name):
        start_time = time.time()

        # file_matrix is a 2D dict matrix
        file_matrix = {}
        commits = self.__databaseService.getCommitsOfRepo(repo_id, get_only_ids=True)
        repo_files = set()
        # For every commit in repo
        for commit_id in commits:
            files = self.__databaseService.getFilesChangesOfCommit(commit_id)
            commit_files = [file[Columns.FileChanges.path] for file in files]
            repo_files.update(commit_files)
            for file_path_1 in commit_files:
                for file_path_2 in commit_files:
                    #avoid self-loops
                    if file_path_1 != file_path_2:
                        # For every files changed togehter
                        self.__increment_commit_count(file_matrix, file_path_1, file_path_2)

        print("------> Matrix generation in " +  time.time() - start_time + " seconds.")
        checkpoint_time = time.time()

        graph = self.__createGraph(file_matrix) #create graph of the matrix.
        print("------> Graph generation in " +  time.time() - checkpoint_time + " seconds.")
        check_point_time = time.time()

        repo_metrics = graph.analyzeGraph()
        print("------> Graph analyzing in " +  time.time() - checkpoint_time + " seconds.")
        check_point_time = time.time()

        self.__exportCsv(repo_id, repo_files, file_matrix)
        print("------> CSV exporting in " +  time.time() - checkpoint_time + " seconds.")
        check_point_time = time.time()

        file_name = "file_metrics.csv"
        graph.exportRepoMetrics(repo_metrics,  repo_full_name, file_name)
        print("------> Exporting repo metrics in " +  time.time() - checkpoint_time + " seconds.")
        check_point_time = time.time()


        elapsed_time = time.time() - start_time
        print("---> File matrix generated for repo (" + str(repo_full_name) + ") in " + str(elapsed_time) + " seconds.")
        gc.collect()


    def __createGraph(self, file_matrix):
        sg = StringKeyGraph()
        for file_1 in file_matrix.keys():
            for file_2 in file_matrix[file_1].keys():
                if file_matrix[file_1][file_2] == 0:
                    continue
                sg.addEdge(file_1, file_2, file_matrix[file_1][file_2])

        return sg

    def __exportCsv(self, repo_id, repo_files, file_matrix):
        # We'are generating a CSV file which is in following format: (A,B,C... are file paths)
        #   ;A;B;C;D;E
        #   A;0;1;0;1;0
        #   B;1;0;0;0;0
        #   C;0;0;1;0;0
        #   D;0;1;0;1;0
        #   E;0;0;0;0;0

        #export to subfolder file_matrices
        head_dir = os.path.dirname(os.path.abspath(__file__))
        export_dir = os.path.join(head_dir, 'file_matrices') # naming file_matrices subfolder

        if not os.path.exists(export_dir): #if file_matrices subfolder does not exist
            os.makedirs(export_dir)

        filename = str(repo_id) + "_filematrix.csv"

        with open(os.path.join(export_dir, filename), "w") as out_file:
            out_file.write(";")
            for file in repo_files:
                out_file.write("%s;" % file)
            out_file.write("\n")
            for file_1 in repo_files:
                out_file.write("%s;" % file_1)
                for file_2 in repo_files:
                    if file_1 not in file_matrix:
                        out_file.write("%d;" % 0)
                        continue

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
