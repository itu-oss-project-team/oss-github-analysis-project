from graph_tool.all import *
import numpy as np
import os.path
import collections


class StringKeyGraph:
    def __init__(self, graph=None):
        if not graph:
            self.graph = Graph(directed=False)
        else:
            self.graph = graph

        vp_key = self.graph.new_vertex_property("string")  # Create vertex property
        self.graph.vp.key = vp_key                         # Set vertex property

        ep_weight = self.graph.new_edge_property("float")  # Create edge property
        self.graph.ep.weight = ep_weight                   # Set edge property

        self.vertexDict = {}

    def getVertex(self, key):

        if key not in self.vertexDict:
            vertex = self.graph.add_vertex()
            self.vertexDict[key] = vertex
            self.setKey(vertex, key)
            return vertex
        return self.vertexDict[key]

    def getVertexKey(self, vertex):
        if not vertex:
            return None
        return self.graph.vp.key[vertex]

    # Adds an edge to graph, if update is true it overrides existing edge
    def addEdge(self, key1, key2, weight=1, update=True):
        v1 = self.getVertex(key1)
        v2 = self.getVertex(key2)
        edge = self.graph.edge(v1, v2)
        if not edge or not update:  # There were no edges or I'd like to create another edge anyways
            edge = self.graph.add_edge(self.getVertex(key1), self.getVertex(key2))
        self.graph.ep.weight[edge] = weight

    def getKey(self, vertex):
        if not vertex:
            return None
        return self.graph.vp.key[vertex]

    def setKey(self, vertex, key):
        self.graph.vp.key[vertex] = key

    def setWeight(self, edge, weight):
        self.graph.ep.weight[edge] = weight

    def analyzeGraph(self):
        # vertex metrics.
        no_of_vertices = len(list(self.graph.vertices()))
        no_of_edges = len(list(self.graph.edges()))

        # it should not try to analyze a graph with no vertex or edge.
        if no_of_vertices == 0 or no_of_edges == 0:
            return
        print("Number of vertices: ", no_of_vertices)
        print("Number of edges: ", no_of_edges)

        pagerank = graph_tool.centrality.pagerank(self.graph, weight=self.graph.ep.weight)
        closeness = graph_tool.centrality.closeness(self.graph, weight=self.graph.ep.weight, norm=True)
        vertex_betweenness, edge_betweenness = graph_tool.centrality.betweenness(self.graph,
                                                weight=self.graph.ep.weight, norm=True)

        eigenvalue_adjacency, eigenvector = graph_tool.centrality.eigenvector(self.graph,
                                                                              weight=self.graph.ep.weight)

        #katz_centrality = graph_tool.centrality.katz(self.graph, weight=self.graph.ep.weight, norm=True)
        eigenvalue_cocitation, authority, hub = graph_tool.centrality.hits(self.graph,
                                                weight=self.graph.ep.weight)

        central_point_dominance = graph_tool.centrality.central_point_dominance(self.graph, vertex_betweenness)
        local_clustering_coefficients = graph_tool.clustering.local_clustering(self.graph, undirected=True)

        degrees = self.graph.get_out_degrees(list(self.graph.vertices()))
        weighted_degrees = self.graph.get_out_degrees(list(self.graph.vertices()), self.graph.ep.weight)

        reaches, two_step_reaches = self.__calculateReaches()

        statistics = collections.OrderedDict()

        #statistics["no_of_nodes"] = no_of_vertices
        #statistics["no_of_edges"] = no_of_edges
        '''
        it might be better not to include no_of_nodes and no_of_edges to the analysis
        they overwhelm the results
        '''
        statistics["weight"] = self.__calculateRepoStatistics(self.graph.ep.weight)
        statistics["degree"] = self.__calculateRepoStatistics(degrees, isPropertyMap=False)
        statistics["weighted_degree"] = self.__calculateRepoStatistics(weighted_degrees, isPropertyMap=False)
        statistics["pagerank"] = self.__calculateRepoStatistics(pagerank)
        statistics["closeness"] = self.__calculateRepoStatistics(closeness)
        statistics["vertex_betweenness"] = self.__calculateRepoStatistics(vertex_betweenness)
        statistics["eigenvector"] = self.__calculateRepoStatistics(eigenvector)
        #statistics["katz_centrality"] = self.__calculateRepoStatistics(katz_centrality) #returns nan for some repos
        statistics["authority"] = self.__calculateRepoStatistics(authority)
        statistics["hub"] = self.__calculateRepoStatistics(hub)
        statistics["local_clustering_coefficients"] = self.__calculateRepoStatistics(local_clustering_coefficients)
        statistics["central_point_dominance"] = central_point_dominance
        statistics["reach"] = self.__calculateRepoStatistics(reaches, isPropertyMap=False)
        statistics["two_step_reach"] = self.__calculateRepoStatistics(two_step_reaches, isPropertyMap=False)

        return statistics

    def __calculateReaches(self):
        reaches = []
        two_step_reaches = []
        for vertex in self.graph.vertices():
            first_neighbours = self.graph.get_out_neighbours(vertex)
            reaches.append(first_neighbours.size)
            two_step_neighbours = set()
            for neighbour in first_neighbours:
                two_step_neighbours.add(neighbour)
                second_neighbours = self.graph.get_out_neighbours(neighbour)
                two_step_neighbours.update([elem for elem in second_neighbours])
            two_step_neighbours.remove(vertex)
            two_step_reaches.append(len(two_step_neighbours))

        return np.array(reaches), np.array(two_step_reaches)

    def __calculateRepoStatistics(self, metric, isPropertyMap = True):
        statistics = collections.OrderedDict()
        if isPropertyMap:
            metric = metric.get_array() # Get a numpy.ndarray subclass (PropertyArray)

        statistics["mean"] = metric.mean()
        statistics["min"] = metric.min()
        statistics["max"] = metric.max()
        statistics["median"] = np.median(metric)

        return statistics

    def exportRepoMetrics(self, repo_statistics, repo_full_name, file_name):
        isFileCreated = os.path.exists(file_name)
        with open(file_name, "a") as out_file:
            if not isFileCreated:
                for statistic in repo_statistics.keys():
                    if isinstance(repo_statistics[statistic], dict):
                        for key in repo_statistics[statistic].keys():
                            out_file.write(";" + statistic + "_" + key)
                    else:
                        out_file.write(";" + statistic)
                out_file.write("\n")

            out_file.write(repo_full_name)

            for statistic in repo_statistics.values():
                if isinstance(statistic, dict):
                    for value in statistic.values():
                        out_file.write(";" + str(value))
                else:
                    out_file.write(";" + str(statistic))
            out_file.write("\n")


class WeightedUndirectedGraph:
    def __init__(self):
        self.g = Graph(directed=False)

        ep_weight = self.g.new_edge_property("float")  # Create a float edge property
        self.g.ep.weight = ep_weight  # Set edge property as weight

    def calculate_metrics(self):
        # vertex metrics.
        no_of_vertices = len(list(self.g.vertices()))
        no_of_edges = len(list(self.g.edges()))

        # it should not try to analyze a graph with no vertex or edge.
        if no_of_vertices == 0 or no_of_edges == 0:
            return

        # print("Number of vertices: ", no_of_vertices)
        # print("Number of edges: ", no_of_edges)

        pagerank = graph_tool.centrality.pagerank(self.g, weight=self.g.ep.weight)
        closeness = graph_tool.centrality.closeness(self.g, weight=self.g.ep.weight, norm=True)
        vertex_betweenness, edge_betweenness = graph_tool.centrality.betweenness(self.g, weight=self.g.ep.weight, norm=True)
        eigenvalue_adjacency, eigenvector = graph_tool.centrality.eigenvector(self.g, weight=self.g.ep.weight)
        eigenvalue_cocitation, authority, hub = graph_tool.centrality.hits(self.g, weight=self.g.ep.weight)
        central_point_dominance = graph_tool.centrality.central_point_dominance(self.g, vertex_betweenness)
        local_clustering_coefficients = graph_tool.clustering.local_clustering(self.g, undirected=True)
        degrees = self.g.get_out_degrees(list(self.g.vertices()))
        #weighted_degrees = self.g.get_out_degrees(list(self.g.vertices()), self.g.ep.weight)
        reaches, two_step_reaches = self.__calculate_reaches()

        statistics = collections.OrderedDict()

        # it might be better to not include no_of_nodes and no_of_edges so they don't overwhelm the results
        # statistics["no_of_nodes"] = no_of_vertices
        # statistics["no_of_edges"] = no_of_edges

        statistics["weight"] = self.__reduce_vertex_metrics(self.g.ep.weight)
        statistics["degree"] = self.__reduce_vertex_metrics(degrees, is_property_map=False)
        #statistics["weighted_degree"] = self.__reduce_vertex_metrics(weighted_degrees, is_property_map=False)
        statistics["pagerank"] = self.__reduce_vertex_metrics(pagerank)
        statistics["closeness"] = self.__reduce_vertex_metrics(closeness)
        statistics["vertex_betweenness"] = self.__reduce_vertex_metrics(vertex_betweenness)
        statistics["eigenvector"] = self.__reduce_vertex_metrics(eigenvector)
        statistics["authority"] = self.__reduce_vertex_metrics(authority)
        statistics["hub"] = self.__reduce_vertex_metrics(hub)
        statistics["local_clustering_coefficients"] = self.__reduce_vertex_metrics(local_clustering_coefficients)
        statistics["reach"] = self.__reduce_vertex_metrics(reaches, is_property_map=False)
        statistics["two_step_reach"] = self.__reduce_vertex_metrics(two_step_reaches, is_property_map=False)
        statistics["central_point_dominance"] = central_point_dominance

        return statistics

    def __calculate_reaches(self):
        reaches = []
        two_step_reaches = []
        for vertex in self.g.vertices():
            first_neighbours = self.g.get_out_neighbours(vertex)
            reaches.append(first_neighbours.size)
            two_step_neighbours = set()
            for neighbour in first_neighbours:
                two_step_neighbours.add(neighbour)
                second_neighbours = self.g.get_out_neighbours(neighbour)
                two_step_neighbours.update([elem for elem in second_neighbours])
            two_step_neighbours.remove(vertex)
            two_step_reaches.append(len(two_step_neighbours))

        return np.array(reaches), np.array(two_step_reaches)

    def __reduce_vertex_metrics(self, metrics, is_property_map = True):
        """
        Calculate mean, min, max and median of given vertex metrics 
        :param metrics: Metric values of vertexes
        :param is_property_map: Is metrics PropertyMap (list otherwise)
        :return: Dict of reduced metrics
        """
        statistics = collections.OrderedDict()
        if is_property_map:
            metrics = metrics.get_array() # Get a numpy.ndarray subclass (PropertyArray)

        statistics["mean"] = metrics.mean()
        statistics["min"] = metrics.min()
        statistics["max"] = metrics.max()
        statistics["median"] = np.median(metrics)

        return statistics

    def export_metrics(self, metrics, name, file_path):
        """
        Append graph metrics to a file
        :param metrics: Metrics of a graph in dic format
        :param name: Name of the graph
        :param file_path: File to be appended
        :return: None
        """
        is_file_created = os.path.exists(file_path)
        with open(file_path, "a") as out_file:
            # If opening the file for first time, write the header line
            if not is_file_created:
                for statistic in metrics.keys():
                    if isinstance(metrics[statistic], dict):
                        for key in metrics[statistic].keys():
                            out_file.write(";" + statistic + "_" + key)
                    else:
                        out_file.write(";" + statistic)
                out_file.write("\n")

            out_file.write(name)

            for statistic in metrics.values():
                if isinstance(statistic, dict):
                    for value in statistic.values():
                        out_file.write(";" + str(value))
                else:
                    out_file.write(";" + str(statistic))
            out_file.write("\n")


