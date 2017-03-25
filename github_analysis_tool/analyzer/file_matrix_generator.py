import collections
import gc
import os.path
import time

from services.database_service import DatabaseService
from services.graph_service import StringKeyGraph

from github_analysis_tool.services.db_column_constants import Columns


class FileMatrixGenerator:
    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])

    def create_matrix(self, repo_id, repo_full_name):
        start_time = time.time()

        # file_matrix is a 2D dict matrix
        file_matrix = collections.OrderedDict()
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

        print("------> Matrix generation in " + str(time.time() - start_time) + " seconds.")
        checkpoint_time = time.time()

        graph = self.__createGraph(file_matrix) #create graph of the matrix.
        print("------> Graph generation in " + str(time.time() - checkpoint_time) + " seconds.")
        checkpoint_time = time.time()

        repo_metrics = graph.analyzeGraph()
        print("------> Graph analyzing in " + str(time.time() - checkpoint_time) + " seconds.")
        checkpoint_time = time.time()

        self.__exportCsv(repo_id, repo_files, file_matrix)
        print("------> CSV exporting in " + str(time.time() - checkpoint_time) + " seconds.")
        checkpoint_time = time.time()

        file_name = "file_metrics.csv"
        graph.exportRepoMetrics(repo_metrics,  repo_full_name, file_name)
        print("------> Exporting repo metrics in " + str(time.time() - checkpoint_time) + " seconds.")

        elapsed_time = time.time() - start_time
        print("---> File matrix generated for repo (" + str(repo_full_name) + ") in " + str(elapsed_time) + " seconds.")
        gc.collect() #force garbage collector to collect garbage.

    def __createGraph(self, file_matrix):
        sg = StringKeyGraph()
        edgeList = set()
        weightList = []
        for file_1 in file_matrix.keys():
            for file_2 in file_matrix[file_1].keys():
                if file_matrix[file_1][file_2] != 0:
                    ''' we need to add one single undirected edge '''
                    _edge = (file_1, file_2)
                    edge = tuple(sorted(_edge)) #sort the edge to get a single edge pair
                    if edge not in edgeList:
                        edgeList.add(edge)
                        weightList.append(file_matrix[file_1][file_2])

        sg.graph.add_edge_list(edgeList, hashed=True, eprops=None)
        sg.graph.ep.weight.a = weightList
        #graph_tool.stats.remove_parallel_edges(sg.graph)
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
        head_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #get the root directory
        export_dir = os.path.join(head_dir, 'outputs', 'file_matrices') # naming file_matrices subfolder

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
