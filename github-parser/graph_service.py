from graph_tool.all import *
import numpy as np
import os.path
import collections

# End point for harvesting GitHub API
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
        print("Number of vertices: ", no_of_vertices)
        print("Number of edges: ", no_of_edges)
        print("\n")

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

        '''
        print("\t\t\t\t\t\t\tPagerank\tCloseness\tV_Betweeness\tEigenvector\tKatz\tAuthority\tHub")
        for v in self.graph.vertices():
            print(self.getVertexKey(v), "%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f" %
                  (pagerank[v], closeness[v], vertex_betweenness[v], eigenvector[v], katz_centrality[v],
                   authority[v], hub[v], local_clustering_coefficients[v], ))
        print("\n")
        '''

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

        return statistics
        # graph_draw(self.sg.graph, vertex_text=self.sg.graph.vertex_index, vertex_font_size=18,
        # output_size=(1000, 1000), output="two-nodes.png")


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








