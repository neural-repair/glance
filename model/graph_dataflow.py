import json
import traceback
from graph4nlp.pytorch.data import GraphData
from tokenization import tokenize, stem
from typing import List, NamedTuple

def tokenize_and_stem(input):
    input = ' '.join(tokenize(input.strip()))
    input = stem(input)
    return input


def load_file_as_json(input_file_name):
    with open(input_file_name, 'r') as input_file:
        file_as_json = json.load(input_file)
    return file_as_json


class Variable:
    def __init__(self, name, defineIn, usebyArray, callbyArray, setbyArray):
        self.name = name
        self.defineIn = defineIn
        self.usebyArray = usebyArray
        self.callbyArray = callbyArray
        self.setbyArray = setbyArray


def dataflow_graph_token_based(file_name, is_all=True, selective_lines=None):
    try:
        buggy_src = load_file_as_json(file_name)

        source_code_lines = buggy_src["source"]
        graph_data: GraphData = GraphData()

        index = 0
        buggy_line_num = buggy_src["buggy_line_num"]
        buggy_line_found = False
        if str(buggy_line_num) not in source_code_lines:
            buggy_line_num = list(source_code_lines.keys())[-1]

        # extract data_flow information
        is_variable = {}
        is_variable_defined_in_line_N = {}
        is_variable_used_in_line_N = {}
        is_variable_called_in_line_N = {}
        is_variable_set_in_line_N = {}
        variables = {}  # not used so far - kept it for the time being
        data_flow = buggy_src["data_flow"]
        for variable in data_flow:
            is_variable[variable] = True
            def_use_all = data_flow[variable]
            def_by = []
            use_by = []
            call_by = []
            set_by = []
            if len(def_use_all) > 0:
                for def_use_attribute in def_use_all:
                    if def_use_attribute["edge"] == "Definein":
                        def_by.append(def_use_attribute["edge"])
                        def_line_no = def_use_attribute["line"]
                        def_key = str(f"{variable}-{def_line_no}")
                        is_variable_defined_in_line_N[def_key] = True
                    elif def_use_attribute["edge"] == "Useby":
                        use_by.append(def_use_attribute["line"])
                        use_line_no = def_use_attribute["line"]
                        use_key = str(f"{variable}-{use_line_no}")
                        is_variable_used_in_line_N[use_key] = True
                    elif def_use_attribute["edge"] == "Callby":
                        call_by.append(def_use_attribute["line"])
                        call_line_no = def_use_attribute["line"]
                        call_key = str(f"{variable}-{call_line_no}")
                        is_variable_called_in_line_N[call_key] = True
                    elif def_use_attribute["edge"] == "Setby":
                        set_by.append(def_use_attribute["line"])
                        set_line_no = def_use_attribute["line"]
                        set_key = str(f"{variable}-{set_line_no}")
                        is_variable_set_in_line_N[set_key] = True
                v = Variable(variable, def_by, use_by, call_by, set_by)
                variables[variable] = v

        line_to_index = {}
        data_flow_edges = []
        variable_defined_to_index = {}
        num_tokens = 0
        # for source_code_line in source_code_lines:
        for line_number, source_code_line in source_code_lines.items():
            line_to_index[line_number] = index

            # wrap buggy line with START_BUG and END_BUG
            if str(buggy_line_num) == str(line_number):
                buggy_line_found = True

                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = "START_BUG"
                index += 1

                tokens = tokenize_and_stem(source_code_line).split()
                for token in tokens:
                    graph_data.add_nodes(1)
                    graph_data.node_attributes[index]["token"] = token
                    index += 1

                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = "END_BUG"
                index += 1

            # graph_data.add_nodes(1)
            # graph_data.node_attributes[index]["token"] = tokenize_and_stem(source_code_line)
            tokens = tokenize_and_stem(source_code_line).split()
            num_tokens += len(tokens)
            for token in tokens:
                graph_data.add_nodes(1)
                graph_data.node_attributes[index]["token"] = token

                key = str(f"{token}-{line_number}")
                if key in is_variable_defined_in_line_N:
                    variable_defined_to_index[token] = index

                if is_all or line_number in selective_lines:
                    if key in is_variable_used_in_line_N:
                        if token in variable_defined_to_index:
                            def_index = variable_defined_to_index[token]
                            df_edge = (def_index, index, "useby")
                            data_flow_edges.append(df_edge)
                    if key in is_variable_called_in_line_N:
                        if token in variable_defined_to_index:
                            def_index = variable_defined_to_index[token]
                            df_edge = (def_index, index, "callby")
                            data_flow_edges.append(df_edge)
                    if key in is_variable_set_in_line_N:
                        if token in variable_defined_to_index:
                            def_index = variable_defined_to_index[token]
                            df_edge = (def_index, index, "setby")
                            data_flow_edges.append(df_edge)
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

        # control-flow edge to the start of the line
        num_cf_edges = 0
        for cf in control_flow_edges:
            from_line_no = cf[0]
            to_line_no = cf[1]
            if (from_line_no in line_to_index) and (to_line_no in line_to_index):
                from_line_index = line_to_index[from_line_no]
                to_line_index = line_to_index[to_line_no]
                graph_data.add_edge(from_line_index, to_line_index)
                num_cf_edges += 1

        # data-flow edge
        """
        alternative implementation: 
        - scan for variable from start to the end 
        - stitch with useBy based on auxiliary data structure 
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
        num_df_edges = 0
        for df in data_flow_edges:
            from_index = df[0]
            to_index = df[1]
            graph_data.add_edge(from_index, to_index)
            # if (from_line_no in line_to_index) and (to_line_no in line_to_index):
            #    from_line_index = line_to_index[from_line_no]
            #    to_line_index = line_to_index[to_line_no]
            #    graph_data.add_edge(from_line_index, to_line_index)
            num_df_edges += 1

        if not buggy_line_found:
            print(f"cannot find buggy_line in file {file_name}")

        class GraphStats(NamedTuple):
            file_name: str
            num_lines: int
            num_nodes: int
            num_edges: int
            num_cf_edges: int
            num_df_edges: int

        stats = GraphStats(file_name=file_name,
                            num_lines=len(source_code_lines),
                            num_nodes=graph_data.get_node_num(),
                            num_edges=graph_data.get_edge_num(),
                            num_cf_edges=num_cf_edges,
                            num_df_edges=num_df_edges)
        print(f"processed file:{stats.file_name},"
              f"num_lines:{stats.num_lines},"
              f"num_nodes:{stats.num_nodes},"
              f"num_edges:{stats.num_edges},"
              f"num_cf_edges: {stats.num_cf_edges},"
              f"num_df_edges:{stats.num_df_edges}")

        graph_data.node_attributes[0]["file_name"] = file_name
        return graph_data, stats
    except Exception as e:
        print("error processing: file: {}, {}".format(file_name, e))
        traceback.print_exc()


def dataflow_graph_unsliced(unsliced_file, sliced_file, is_all):
    sliced_buggy_src = load_file_as_json(sliced_file)

    sliced_source_code_lines = sliced_buggy_src["source"]
    sliced_lines = sliced_source_code_lines.keys()

    graph, stats = dataflow_graph_token_based(file_name=unsliced_file, is_all=is_all, selective_lines=sliced_lines)
    return graph
