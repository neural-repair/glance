import networkx as nx
from graph4nlp.pytorch.data import GraphData
from networkx import Graph
from networkx.drawing.nx_pydot import read_dot
from networkx.drawing.nx_pydot import to_pydot


def parse_dot_file(file_name):
    try:
        raw_graph: Graph = nx.Graph(read_dot(file_name))
        graph = to_pydot(raw_graph)

        graph_data: GraphData = GraphData()
        graph_data.add_nodes(len(graph.get_node_list()))

        # add leaf nodes attributes
        name_to_node_index = {}
        index = 0
        for node in graph.get_node_list():
            graph_data.node_attributes[index]["token"] = str(node.get_label())
            name_to_node_index[node.get_name()] = index
            index = index + 1

        edge_index = 0
        for edge in graph.get_edge_list():
            graph_data.add_edge(name_to_node_index[edge.get_source()], name_to_node_index[edge.get_destination()])
            graph_data.edge_attributes[edge_index]['edge_attr'] = edge.get_label()
            edge_index = edge_index + 1
        print("processed file:{}".format(file_name))
        return graph_data
    except Exception as e:
        print("file: {}, {}".format(file_name, e))
