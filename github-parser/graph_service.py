from graph_tool.all import *


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


