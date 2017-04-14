import abc
import os.path
import time
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from github_analysis_tool import OUTPUT_DIR, secret_config
from github_analysis_tool.services.database_service import DatabaseService
from github_analysis_tool.services.graph_service import WeightedUndirectedGraph


class AbstractAnalyzer(object):
    """
    An abstract class for network based analysis
    All inherited classes should override create_matrix method
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self._name = name
        self._databaseService = DatabaseService()

        self._matrices_folder_path = os.path.join(OUTPUT_DIR, self._name + '_matrices')
        if not os.path.exists(self._matrices_folder_path):
            os.makedirs(self._matrices_folder_path)
        self._metrics_file_path = os.path.join(OUTPUT_DIR, self._name + "_metrics.csv")
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO,
                            filename=os.path.join(OUTPUT_DIR, "generate_matrices_log.log"))


    @abc.abstractmethod
    def create_matrix(self, repo_id) -> dict:
        pass

    def analyze_repo(self, repo_full_name):
        repository = self._databaseService.get_repo_by_full_name(repo_full_name)
        repo_id = repository['id']
        repo_name_underscored = str(repo_full_name).replace("/", "_")

        start_time = time.time()

        print("---> Starting " + self._name + " analysis for repo: " + repo_full_name)
        logging.info("---> Starting " + self._name + " analysis for repo: " + repo_full_name)

        network_matrix = self.create_matrix(repo_id)
        print("[" + repo_full_name + "]: " + self._name + " Matrix generated in " + "{0:.2f}".format(time.time() - start_time) + " seconds.")
        logging.info("[" + repo_full_name + "]: " + self._name + " Matrix generated in " + "{0:.2f}".format(time.time() - start_time) + " seconds.")
        checkpoint_time = time.time()

        graph = self.__create_graph(network_matrix)  # create graph of the matrix.
        print("[" + repo_full_name + "]: " + self._name + " Graph generated in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        logging.info("[" + repo_full_name + "]: " + self._name + " Graph generated in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        checkpoint_time = time.time()

        repo_metrics = graph.calculate_metrics()
        print("[" + repo_full_name + "]: " + self._name + " Graph analyzed in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        logging.info("[" + repo_full_name + "]: " + self._name + " Graph analyzed in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        checkpoint_time = time.time()

        network_file_path = os.path.join(self._matrices_folder_path, str(repo_name_underscored) + ".csv")
        self.__export_csv(network_matrix, network_file_path)
        print("[" + repo_full_name + "]: " + self._name + " Network matrix exported to CSV in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        logging.info("[" + repo_full_name + "]: " + self._name + " Network matrix exported to CSV in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        checkpoint_time = time.time()

        graph.export_metrics(repo_metrics, repo_full_name, self._metrics_file_path)
        print("[" + repo_full_name + "]: " + self._name + " Repo metrics exported to CSV in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")
        logging.info("[" + repo_full_name + "]: " + self._name + " Repo metrics exported to CSV in " + "{0:.2f}".format(time.time() - checkpoint_time) + " seconds.")

        elapsed_time = time.time() - start_time
        print("---> Finishing " + self._name + " analysis for repo: " + str(repo_full_name) + ") in " + "{0:.2f}".format(elapsed_time) + " seconds.")
        print()# Empty line
        directory_path = os.path.dirname(os.path.realpath(__file__))
        repositories_file_path = os.path.join(directory_path, 'finished_repositories.txt')

        with open('finished_repositories.txt', "a") as finished_repos:
            finished_repos.write(repo_full_name + "\n")


    def __create_graph(self, network_matrix):
        graph = WeightedUndirectedGraph()
        edge_list = set()
        weight_list = []

        for node_1 in network_matrix.keys():
            for node_2 in network_matrix[node_1].keys():
                if network_matrix[node_1][node_2] != 0:
                    # We need to add one single undirected edge
                    _edge = (node_1, node_2)
                    edge = tuple(sorted(_edge)) #sort the edge to get a single edge pair
                    if edge not in edge_list:
                        edge_list.add(edge)
                        weight_list.append(network_matrix[node_1][node_2])

        graph.g.add_edge_list(edge_list, hashed=True, eprops=None)
        graph.g.ep.weight.a = weight_list
        return graph

    def __export_csv(self, network_matrix, file_path):
        """
        Generating a CSV file which is in following format: (A,B,C... are node names)
           ;A;B;C;D;E
           A;0;1;0;1;0
           B;1;0;0;0;0
           C;0;0;1;0;0
           D;0;1;0;1;0
           E;0;0;0;0;0
        :param repo_id: In order to name file
        :param network_matrix: 2D dict for network matrix
        :return: None
        """

        nodes = network_matrix.keys()

        with open(file_path, "w") as out_file:
            out_file.write(";")
            for file in nodes:
                out_file.write("%s;" % file)
            out_file.write("\n")
            for node_1 in nodes:
                out_file.write("%s;" % node_1)
                for node_2 in nodes:
                    if node_1 not in network_matrix:
                        out_file.write("%d;" % 0)
                        continue

                    if not node_2 in network_matrix[node_1]:
                        out_file.write("%d;" % 0)
                    else:
                        out_file.write("%f;" % network_matrix[node_1][node_2])

                out_file.write("\n")