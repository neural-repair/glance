from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import json
import sys
from gtrans.common.code_graph import AST, AstNode
from gtrans.common.consts import SEPARATOR
from gtrans.data_process.tokenization import tokenize

sys.setrecursionlimit(1500)


def create_child(node, ast):
    src = ast.new_node(node.node_type, node.value)
    if len(node.children) == 0:
        return src

    count = 0
    for child in node.children:
        src.add_child(create_child(child, ast), count)
        count += 1

    return src


def build_shift_node_ast_from_json(json_node, parent_node, ast):
    if isinstance(json_node, dict):
        assert 'type' in json_node
        value = str(json_node['value']) if 'value' in json_node else None
        ast_node = ast.new_node(node_type=json_node['type'], value=value)
        for key in json_node:
            if key == 'type' or key == 'value':
                continue
            if isinstance(json_node[key], dict):
                ch_node = build_shift_node_ast_from_json(json_node[key], ast_node, ast)
                ch_node.node_type = key + SEPARATOR + ch_node.node_type
            elif isinstance(json_node[key], list):
                ch_node = ast.new_node(key, value=None)
                build_shift_node_ast_from_json(json_node[key], ch_node, ast)
            else:
                value = None if json_node[key] is None else str(json_node[key])
                ch_node = ast.new_node(key, value=value)
            ast_node.add_child(ch_node)
        return ast_node
    elif isinstance(json_node, list):
        assert parent_node is not None
        for d in json_node:
            if isinstance(d, dict):
                ch_node = build_shift_node_ast_from_json(d, None, ast)
            else:
                assert d is None
                ch_node = ast.new_node('None', value=None)
            parent_node.add_child(ch_node)
    else:
        raise NotImplementedError


def build_shift_node_ast(fname):
    with open(fname, 'r') as f:
        try:
            root_node = json.load(f)
        except (json.decoder.JSONDecodeError, RecursionError) as e:
            return None

        ast = AST()
        root = build_shift_node_ast_from_json(root_node, None, ast)
        ast.root_node = root
    return ast


def shift_node_ast_to_dot(ast: AST, diff):
    # print('AST:{}'.format(ast))
    from collections import deque

    q = deque()
    q.append(ast.root_node)
    dot_representation = ""
    prev_node_type = None

    num_nodes = 0
    num_edges = 0
    while len(q) > 0:
        parent = q.pop()

        # node_value and node_type
        node_attribute = ""
 
        parent_node_type = parent.node_type
        if "LiteralRegExpExpression" in parent_node_type or "LiteralStringExpression" in parent_node_type:
            node_attribute = "$STRING$"
        elif "LiteralNumericExpression" in parent_node_type:
            node_attribute = "$NUMBER$"
        elif parent_node_type == "rawValue" and prev_node_type == "TemplateElement":
            node_attribute = "$STRING$"
        elif SEPARATOR in parent_node_type:
            parent_node_types = parent_node_type.split(SEPARATOR)
            node_attribute = parent.value if parent.value else parent_node_types[1]
        else:
            node_attribute = parent.value if parent.value else parent_node_type

        parent_node_type = parent.node_type
        parent_node_value = "".join((",", parent.value)) if parent.value else ""
        dot_representation = "\n".join((
            dot_representation,
            "\"{}\" [ label = \"{}\" ];".format(parent.id, node_attribute),
        ))
        num_nodes += 1

        for child in parent.children:
            # print("child={}, id={}, node_type={}, value={}, index={}, parent={}"
            #       .format(child, child.id,
            #               child.node_type, child.value,
            #               child.index, child.index))
            dot_representation = "\n".join((
                dot_representation,
                "\"{}\" -> \"{}\";".format(parent.id, child.id)
            ))
            num_edges = num_edges + 1
            q.append(child)
        
        prev_node_type = parent_node_type

    wrap_dot_representation = "\n".join((
        "digraph G {",
        dot_representation,
        "}"
    ))
    # print(wrap_dot_representation)
    return num_nodes, num_edges, wrap_dot_representation, ' '.join(tokenize(diff[1]))

#def shift_node_ast_to_dot_simplification_abstraction(ast: AST):
def shift_node_ast_to_dot_original(ast: AST):
    print('AST:{}'.format(ast))

    from collections import deque

    q = deque()
    q.append(ast.root_node)
    dot_representation = ""

    num_nodes = 0
    num_edges = 0
    while len(q) > 0:
        parent = q.pop()

        parent_node_type = parent.node_type
        parent_node_value = "".join((",", parent.value)) if parent.value else ""
        dot_representation = "\n".join((
            dot_representation,
            "\"{}\" [ label = \"{}{}\" ];".format(parent.id, parent_node_type, parent_node_value),
        ))
        num_nodes += 1

        for child in parent.children:
            print("child={}, id={}, node_type={}, value={}, index={}, parent={}"
                  .format(child, child.id,
                          child.node_type, child.value,
                          child.index, child.index))
            dot_representation = "\n".join((
                dot_representation,
                "\"{}\" -> \"{}\";".format(parent.id, child.id)
            ))
            num_edges = num_edges + 1
            q.append(child)

    wrap_dot_representation = "\n".join((
        "digraph G {",
        dot_representation,
        "}"
    ))
    # print(wrap_dot_representation)
    return num_nodes, num_edges, wrap_dot_representation

def shift_node_ast_to_dot_debug(ast: AST):
    print('AST:{}'.format(ast))

    from collections import deque

    q = deque()
    q.append(ast.root_node)
    dot_representation = ""

    num_nodes = 0
    num_edges = 0
    while len(q) > 0:
        parent = q.pop()

        parent_node_type = parent.node_type
        parent_node_value = "".join((",", parent.value)) if parent.value else ""
        dot_representation = "\n".join((
            dot_representation,
            "\"{}\" [ label = \"{}{}\" ];".format(parent.id, parent_node_type, parent_node_value),
        ))
        num_nodes += 1

        for child in parent.children:
            print("child={}, id={}, node_type={}, value={}, index={}, parent={}"
                  .format(child, child.id,
                          child.node_type, child.value,
                          child.index, child.index))
            dot_representation = "\n".join((
                dot_representation,
                "\"{}\" -> \"{}\";".format(parent.id, child.id)
            ))
            num_edges = num_edges + 1
            q.append(child)

    wrap_dot_representation = "\n".join((
        "digraph G {",
        dot_representation,
        "}"
    ))
    # print(wrap_dot_representation)
    return num_nodes, num_edges, wrap_dot_representation
