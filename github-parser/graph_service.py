from graph_tool.all import *


# End point for harvesting GitHub API
class StringKeyGraph:
    def __init__(self, graph=None):
        if not graph:
            self.graph = Graph(directed=False)
        else:
            self.graph = graph

        string_prop = self.graph.new_vertex_property("string")  # Create vertex property
        self.graph.vp.key = string_prop                         # Set vertex property
        self.vertexDict = {}

    def getVertex(self, key):
        if key not in self.vertexDict:
            vertex = self.graph.add_vertex()
            self.vertexDict[key] = vertex
            self.setKey(vertex, key)
            return vertex
        return self.vertexDict[key]

    def addEdge(self, key1, key2):
        self.graph.add_edge(self.getVertex(key1), self.getVertex(key2))

    def getKey(self, vertex):
        if not vertex:
            return None
        return self.graph.vp.key[vertex]

    def setKey(self, vertex, key):
        self.graph.vp.key[vertex] = key


