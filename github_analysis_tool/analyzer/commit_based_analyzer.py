import time

from graph_tool.all import *
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.services.graph_service import StringKeyGraph


class CommitMatrixGenerator:
    def __init__(self):
        self.__databaseService = DatabaseService()

    def crate_matrix(self, repo_id):
        start_time = time.time()

        commit_matrix = {}          # {<commit1>:{<commit2>:<shared_file_changes>}
        commit_file_counts = {}     # {<commit>:<file_count>}

        repo_files = self.__databaseService.get_files_of_repo(repo_id, get_only_file_paths=True)

        # For every file in repo
        for file_name in repo_files:
            commits_of_file = self.__databaseService.get_commits_of_file(repo_id, file_name, get_only_ids=True)

            for commit in commits_of_file:
                # Count how many files are there in each commit so we can normalize our matrix later with these counts
                self.__increment_commit_file_count(commit_file_counts, commit)

            for commit_1 in commits_of_file:
                for commit_2 in commits_of_file:
                    # For every commit pair that edits this same file
                    self.__increment_file_count(commit_matrix, commit_1, commit_2)

        self.__normalize_matrix(commit_matrix, commit_file_counts)

        self.__exportCsv(repo_id, commit_matrix)

        graph = self.__creaateGraph(commit_matrix)

        self.__analyzeGraph(graph)


        elapsed_time = time.time() - start_time
        print("---> Commit matrix generated for repo (" + str(repo_id) + ") in " + str(elapsed_time) + " seconds.")

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
            for commit_2 in  commit_matrix.keys():
                if commit_2 not in commit_matrix[commit_1]:
                    continue
                intersectCount = commit_matrix[commit_1][commit_2]
                unionCount = commit_file_counts[commit_1] + commit_file_counts[commit_2] - intersectCount
                test = intersectCount / unionCount
                commit_matrix[commit_1][commit_2] = intersectCount / unionCount
    '''
        We'are generating a CSV file which is in following format: (A,B,C... are commit ids)
        ;A;B;C;D;E
        A;0;1;0;1;0
        B;1;0;0;0;0
        C;0;0;1;0;0
        D;0;1;0;1;0
        E;0;0;0;0;0
    '''
    def __exportCsv(self, repo_id, commit_matrix):
        with open(str(repo_id) + "_commitmatrix.csv", "w") as out_file:
            out_file.write(";")
            repo_commits = self.__databaseService.get_commits_of_repo(repo_id, get_only_ids=True)
            for commit_id in repo_commits:
                out_file.write("%s;" % commit_id)

            out_file.write("\n")

            for commit_1 in repo_commits:
                out_file.write("%s;" % commit_1)
                for commit_2 in repo_commits:
                    if commit_1 not in commit_matrix:
                        out_file.write("%d;" % 0)
                    elif commit_2 not in commit_matrix[commit_1]:
                        out_file.write("%d;" % 0)
                    else:
                        out_file.write("%f;" % commit_matrix[commit_1][commit_2])

                out_file.write("\n")

    def __creaateGraph(self, commit_matrix):
        sg = StringKeyGraph()
        for commit1 in commit_matrix.keys():
            for commit2 in commit_matrix[commit1].keys():
                if commit_matrix[commit1][commit2] == 0:
                    continue
                sg.addEdge(commit1, commit2, commit_matrix[commit1][commit2])

        return sg

    def __analyzeGraph(self, graph):
        pagerank = graph_tool.centrality.pagerank(graph.graph, weight=graph.graph.ep.weight)
        closeness = graph_tool.centrality.closeness(graph.graph, weight=graph.graph.ep.weight)
        vertex_betweenness, edge_betweenness = graph_tool.centrality.betweenness(graph.graph, weight=graph.graph.ep.weight)
        print("\t\t\t\tPagerank\t\tCloseness\t\tV_Betweeness")
        for v in graph.graph.vertices():
            print(graph.getVertexKey(v), pagerank[v], closeness[v], vertex_betweenness[v])
