import json
import pydot
from graph4nlp.pytorch.data import GraphData
from nltk.tokenize import wordpunct_tokenize


def line_to_graph(file_name):
    try:
        buggy_src = ""
        with open(file_name, 'r') as file:
            buggy_src = file.read().replace('\n', '')

        tokens = wordpunct_tokenize(buggy_src)
        # tokens = buggy_src.strip().join(" ")
        graph_data: GraphData = GraphData()
        graph_data.add_nodes(len(tokens))

        index = 0
        for token in tokens:
            graph_data.node_attributes[index]["token"] = token
            index = index + 1

        first_node = 0
        second_node = 1
        while second_node < len(tokens):
            graph_data.add_edge(first_node, second_node)
            first_node += 1
            second_node += 1

        print("processed file:{}".format(file_name))
        return graph_data
    except Exception as e:
        print("file: {}, {}".format(file_name, e))


def json_to_cfg(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
        print(data)

        control_flows = []
        cf_blocks = data["control_flow"]

        nodes = []
        cf_graph = pydot.Dot('cfg_graph', graph_type='digraph')
        for node, code_statements in data["source"].items():
            print(code_statements)
            cf_graph.add_node(pydot.Node(node, label=(code_statements), shape='rectangle'))
            nodes.append(node)

        edges = []
        for block, branches in cf_blocks.items():
            from_block = block
            if "type" in branches:
                if branches["type"] != "passive":
                    if "next_line" in branches:
                        edge = (from_block, str(branches["next_line"]), branches["next_line"])
                        edges.append(edge)
                        cf_graph.add_edge(pydot.Edge(src=from_block, dst=str(branches["next_line"]), color='magenta',
                                                     label="end-loop"))
            if "yes" in branches:
                edge = (from_block, branches["yes"], "yes")
                edges.append(edge)
                cf_graph.add_edge(pydot.Edge(src=from_block, dst=str(branches["yes"]), color='blue', label="yes"))
            if "no" in branches:
                edge = (from_block, branches["no"], "no")
                edges.append(edge)
                cf_graph.add_edge(pydot.Edge(src=from_block, dst=str(branches["no"]), color='blue', label="no"))

        # connect consecutive statements
        if len(nodes) > 0:
            prev_node = nodes[0]
            prev_index = 0
            next_index = 1
            while next_index < len(nodes):
                cf_graph.add_edge(pydot.Edge(src=str(nodes[prev_index]), dst=str(nodes[next_index]), color='green'))
                prev_index += 1
                next_index += 1

        # cf_graph.write_png('./cfg-jsons/cf_graph.png', encoding="utf-8")

        cf_graph.write_png(output_file, encoding="utf-8")


json_to_cfg(input_file='./latest-cfg-jsons/loops-for-back-slice-new.json',
            output_file='./latest-cfg-jsons/loops-for-back-slice-new.png')
