import json
import traceback

from graph4nlp.pytorch.data import GraphData
from nltk.tokenize import wordpunct_tokenize

from tokenization import tokenize, stem


def tokenize_and_stem(input):
    input = ' '.join(tokenize(input.strip()))
    input = stem(input)
    return input


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


def json_cfg_to_graph(file_name):
    try:
        buggy_src = ""
        with open(file_name, 'r') as file:
            buggy_src = json.load(file)  # file.read().replace('\n', '')

        # tokens_as_line_node = wordpunct_tokenize(buggy_src)
        source_code_lines = buggy_src["sourceDecomment"]

        # tokens = buggy_src.strip().join(" ")
        graph_data: GraphData = GraphData()
        graph_data.add_nodes(len(source_code_lines) + 2)

        index = 0
        buggy_line_num = buggy_src["buggy_line_num"]
        buggy_line_found = False
        mismatch = 0
        if str(buggy_line_num) not in source_code_lines:
            buggy_line_num = list(source_code_lines.keys())[-1]

        # for source_code_line in source_code_lines:
        for line_number, source_code_line in source_code_lines.items():
            if str(buggy_line_num) == str(line_number):
                buggy_line_found = True
                graph_data.node_attributes[index]["token"] = "START_BUG"
                index = index + 1
                graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
                index = index + 1
                graph_data.node_attributes[index]["token"] = "END_BUG"
            else:
                graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
            index += 1

        first_node = 0
        second_node = 1
        while second_node < (len(source_code_lines) + 2):
            graph_data.add_edge(first_node, second_node)
            first_node += 1
            second_node += 1

        if not buggy_line_found:
            mismatch += 1
            print("===> mismatch")

        print("processed file:{}, nodes:{}, edges:{}".format(file_name, graph_data.get_node_num(),
                                                             graph_data.get_edge_num()))
        return graph_data
    except Exception as e:
        print("error: file: {}, {}".format(file_name, e))
        traceback.print_exc()


def json_cfg_to_graph_token_based(file_name):
    try:
        buggy_src = ""
        with open(file_name, 'r') as file:
            buggy_src = json.load(file)  # file.read().replace('\n', '')

        # tokens_as_line_node = wordpunct_tokenize(buggy_src)
        #source_code_lines = buggy_src["sourceDecomment"]
        source_code_lines = buggy_src["source"]

        # tokens = buggy_src.strip().join(" ")
        graph_data: GraphData = GraphData()
        # graph_data.add_nodes(len(source_code_lines) + 2)

        index = 0
        buggy_line_num = buggy_src["buggy_line_num"]
        buggy_line_found = False
        mismatch = 0
        if str(buggy_line_num) not in source_code_lines:
            buggy_line_num = list(source_code_lines.keys())[-1]

        line_to_index = {}
        # for source_code_line in source_code_lines:
        for line_number, source_code_line in source_code_lines.items():
            line_to_index[line_number] = index
            if str(buggy_line_num) == str(line_number):
                buggy_line_found = True

                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = "START_BUG"
                index += 1

                # graph_data.add_nodes(1)
                # graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
                tokens = tokenize_and_stem(source_code_line).split()
                for token in tokens:
                    graph_data.add_nodes(1)
                    graph_data.node_attributes[index]["token"] = token
                    index += 1

                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = "END_BUG"
                index += 1
            else:
                # graph_data.add_nodes(1)
                # graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
                tokens = tokenize_and_stem(source_code_line).split()
                for token in tokens:
                    graph_data.add_nodes(1)
                    graph_data.node_attributes[index]["token"] = token
                    index += 1
            # index += 1

        # control_flow edges
        control_flow_edges = []
        cf_blocks = buggy_src["control_flow"]
        for block, branches in cf_blocks.items():
            from_line = block
            if "type" in branches:
                if branches["type"] != "passive":
                    if "next_line" in branches:
                        edge = (from_line, str(branches["next_line"]), branches["next_line"])
                        control_flow_edges.append(edge)
            if "yes" in branches:
                edge = (from_line, branches["yes"], "yes")
                control_flow_edges.append(edge)
            if "no" in branches:
                edge = (from_line, branches["no"], "no")
                control_flow_edges.append(edge)

        edge_num = 0
        # control-flow edges
        for cf in control_flow_edges:
            print(cf)
            from_line_no = cf[0]
            to_line_no = cf[1]
            if (from_line_no in line_to_index) and (to_line_no in line_to_index):
                from_line_index = line_to_index[from_line_no]
                to_line_index = line_to_index[to_line_no]
                graph_data.add_edge(from_line_index, to_line_index)
                graph_data.edge_attributes[edge_num]['token'] = 'yes'# temporary value for experiment
                edge_num += 1
                print("added control-flow edge.")


        # next token edges
        first_node = 0
        second_node = 1
        while second_node < graph_data.get_node_num():
            # bidirectional edge
            graph_data.add_edge(first_node, second_node)
            graph_data.add_edge(second_node, first_node)
            first_node += 1
            second_node += 1

        if not buggy_line_found:
            mismatch += 1
            print("===> mismatch")

        print("processed file:{}, nodes:{}, edges:{}".format(file_name, graph_data.get_node_num(),
                                                             graph_data.get_edge_num()))
        return graph_data
    except Exception as e:
        print("error: file: {}, {}".format(file_name, e))
        traceback.print_exc()


class Variable:
    def __init__(self, name, defineIn, usebyArray):
        self.name = name
        self.defineIn = defineIn
        self.usebyArray = usebyArray


def json_cfg_and_dataflow_to_graph_token_based(file_name):
    try:
        buggy_src = ""
        with open(file_name, 'r') as file:
            buggy_src = json.load(file)  # file.read().replace('\n', '')

        # tokens_as_line_node = wordpunct_tokenize(buggy_src)
        source_code_lines = buggy_src["sourceDecomment"]

        # tokens = buggy_src.strip().join(" ")
        graph_data: GraphData = GraphData()
        # graph_data.add_nodes(len(source_code_lines) + 2)

        index = 0
        buggy_line_num = buggy_src["buggy_line_num"]
        buggy_line_found = False
        mismatch = 0
        if str(buggy_line_num) not in source_code_lines:
            buggy_line_num = list(source_code_lines.keys())[-1]

        # extract data_flow information
        variables = {}
        data_flow = buggy_src["data_flow"]
        data_flow_edges = []
        for variable in data_flow:
            def_use_all = data_flow[variable]
            def_by = []
            use_by = []
            if len(def_use_all) > 0:
                for def_use_attribute in def_use_all:
                    if def_use_attribute["edge"] == "Definein":
                        if len(def_by) > 1:
                            print(f"same variable defined and redefined, variable = {variable}, code = {source_code_lines}")
                        def_by.append(def_use_attribute["edge"])
                        last_def_by = def_use_attribute["line"]
                    elif def_use_attribute["edge"] == "Useby":
                        use_by.append(def_use_attribute["line"])
                        edge = (last_def_by, def_use_attribute["line"])
                        data_flow_edges.append(edge)
                v = Variable(variable, def_by, use_by)
                variables[variable] = v

        line_to_index = {}
        # for source_code_line in source_code_lines:
        for line_number, source_code_line in source_code_lines.items():
            line_to_index[line_number] = index
            if str(buggy_line_num) == str(line_number):
                buggy_line_found = True

                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = "START_BUG"
                index += 1

                # graph_data.add_nodes(1)
                # graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
                tokens = tokenize_and_stem(source_code_line).split()
                for token in tokens:
                    graph_data.add_nodes(1)
                    graph_data.node_attributes[index]["token"] = token
                    index += 1

                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = "END_BUG"
                index += 1
            else:
                # graph_data.add_nodes(1)
                # graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
                tokens = tokenize_and_stem(source_code_line).split()
                for token in tokens:
                    graph_data.add_nodes(1)
                    graph_data.node_attributes[index]["token"] = token
                    index += 1
            # index += 1

        # control_flow edges
        control_flow_edges = []
        cf_blocks = buggy_src["control_flow"]
        for block, branches in cf_blocks.items():
            from_line = block
            if "type" in branches:
                if branches["type"] != "passive":
                    if "next_line" in branches:
                        edge = (from_line, str(branches["next_line"]), branches["next_line"])
                        control_flow_edges.append(edge)
            if "yes" in branches:
                edge = (from_line, branches["yes"], "yes")
                control_flow_edges.append(edge)
            if "no" in branches:
                edge = (from_line, branches["no"], "no")
                control_flow_edges.append(edge)

        # next token edges
        first_node = 0
        second_node = 1
        while second_node < graph_data.get_node_num():
            graph_data.add_edge(first_node, second_node)
            first_node += 1
            second_node += 1

        # control-flow edges
        for cf in control_flow_edges:
            print(cf)
            from_line_no = cf[0]
            to_line_no = cf[1]
            if (from_line_no in line_to_index) and (to_line_no in line_to_index):
                from_line_index = line_to_index[from_line_no]
                to_line_index = line_to_index[to_line_no]
                graph_data.add_edge(from_line_index, to_line_index)
                print("added control-flow edge.")

        # data-flow edges
        """
        start = 0
        end_index = graph_data.get_node_num()
        for variable in data_flow:
            print(variable)
            if graph_data.nodes[start] == variable:
                for i in range(start, end_index):
                    for j in range(start + 1, end_index, 1):
                        if graph_data.nodes[j] == variable:
                            pass
        """
        for df in data_flow_edges:
            print(df)
            from_line_no = str(df[0])
            to_line_no = str(df[1])
            if (from_line_no in line_to_index) and (to_line_no in line_to_index):
                from_line_index = line_to_index[from_line_no]
                to_line_index = line_to_index[to_line_no]
                graph_data.add_edge(from_line_index, to_line_index)
                print("added data-flow edge.")

        if not buggy_line_found:
            mismatch += 1
            print("===> mismatch")

        print("processed file:{}, nodes:{}, edges:{}".format(file_name, graph_data.get_node_num(),
                                                             graph_data.get_edge_num()))
        return graph_data
    except Exception as e:
        print("error: file: {}, {}".format(file_name, e))
        traceback.print_exc()
