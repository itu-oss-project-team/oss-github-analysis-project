from graph_tool.all import *
from graph_service import StringKeyGraph

sg = StringKeyGraph()

sg.addEdge("d1", "d2")
sg.addEdge("d1", "d3")

graph_draw(sg.graph, vertex_text=sg.graph.vertex_index, vertex_font_size=18, output_size=(200, 200), output="two-nodes.png")
print(sg.getVertex("d1").out_degree())