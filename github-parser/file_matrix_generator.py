from database_service import DatabaseService
from db_column_constants import Columns
import time
from graph_tool.all import *
from graph_service import StringKeyGraph

class FileMatrixGenerator:
    def __init__(self, secret_config):
        self.__databaseService = DatabaseService(secret_config['mysql'])
        self.sg = StringKeyGraph()

    def crate_matrix(self, repo_id):
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
                    if file_path_1 != file_path_2:
                        # For every files changed togehter
                        self.__increment_commit_count(file_matrix, file_path_1, file_path_2)

        # We'are generating a CSV file which is in following format: (A,B,C... are file paths)
        #   ;A;B;C;D;E
        #   A;0;1;0;1;0
        #   B;1;0;0;0;0
        #   C;0;0;1;0;0
        #   D;0;1;0;1;0
        #   E;0;0;0;0;0
        with open(str(repo_id) + "_filematrix.csv", "w") as out_file:
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
                        self.sg.addEdge(file_1, file_2, weight=file_matrix[file_1][file_2])

                out_file.write("\n")

        #printing edges.
        for e in self.sg.graph.edges():
            print(self.sg.getVertexKey(e.source()), self.sg.getVertexKey(e.target()), self.sg.graph.ep.weight[e])

        #vertex metrics.
        print("\n\n")
        pagerank = graph_tool.centrality.pagerank(self.sg.graph, weight=self.sg.graph.ep.weight)
        closeness = graph_tool.centrality.closeness(self.sg.graph, weight=self.sg.graph.ep.weight)
        vertex_betweenness, edge_betweenness = graph_tool.centrality.betweenness(self.sg.graph, weight=self.sg.graph.ep.weight)
        print("\t\t\t\tPagerank\t\tCloseness\t\tV_Betweeness")
        for v in self.sg.graph.vertices():
            print(self.sg.getVertexKey(v), pagerank[v], closeness[v], vertex_betweenness[v])


        #graph_draw(self.sg.graph, vertex_text=self.sg.graph.vertex_index, vertex_font_size=18, output_size=(1000, 1000), output="two-nodes.png")

        elapsed_time = time.time() - start_time
        print("---> File matrix generated for repo (" + str(repo_id) + ") in " + str(elapsed_time) + " seconds.")

    def __increment_commit_count(self, file_matrix, file_path_1, file_path_2):
        if file_path_1 not in file_matrix:
            file_matrix[file_path_1] = {}
        if file_path_2 in file_matrix[file_path_1]:
            file_matrix[file_path_1][file_path_2] += 1
        else:
            file_matrix[file_path_1][file_path_2] = 1
