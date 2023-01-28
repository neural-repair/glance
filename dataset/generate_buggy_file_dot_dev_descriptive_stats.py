import difflib
import datetime
import os
import mmap
import queue
import traceback
import argparse
from os import listdir
from os.path import isfile, join
from concurrent.futures import ThreadPoolExecutor
from gtrans.data_process import build_ast
from gtrans.data_process.ast_utils import shift_node_ast_to_dot


def produce(i, read_path, output_dir, item):
    #print('processing item {} - file prefix {}'.format(i, item[0]))
    data = generate_dot_file(read_path, output_dir, item)
    queue.put(data)
    #print('submitted to queue item {}'.format(i))


def bin2str(text, encoding='utf-8'):
    return text.decode(encoding)


def mmap_io(path, filename):
    lines = []
    try:
        with open(path + '/' + filename, "rb", buffering=0) as f:
            m = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
            m.madvise(mmap.MADV_SEQUENTIAL)
            while True:
                line = m.readline()
                if line:
                    if len(line) > 180:
                        print('Large lines in file {} --- Skipping!!'.format(filename))
                        return []
                    lines.append(bin2str(line))
                else:
                    break
            m.close()
    except ValueError as e:
        # mmap generates value error for empty files
        print("error processing file:{}".format(filename, e))
        traceback.print_exc()
        lines = []
    return lines


def is_whitespace_diff(buggy_line, fixed_line):
    output_list = [li for li in difflib.ndiff(fixed_line, buggy_line) if li[0] != ' ']
    if len(output_list):
        return all(f.strip() in ['+', '-'] for f in output_list)
    return False


def _get_prefix(filename):
    if filename.endswith('_babel.js'):
        return filename.split('_buggy_babel.js')[0] if '_buggy_babel.js' in filename else \
            filename.split('_fixed_babel.js')[0]
    if filename.endswith('_buggy.js') or filename.endswith('_fixed.js'):
        return filename.split('_buggy.js')[0] if '_buggy.js' in filename else filename.split('_fixed.js')[0]


def generate_dot_file(read_path, output_dir, item):
    time_start_file_loading = datetime.datetime.now()
    read_file_name = item[1]['buggy_file']
    read_file_path = "{}/{}".format(read_path, item[1]['buggy_file'])

    output_file_name = read_file_name.split('.json')[0]
    ast_bug = build_ast(read_file_path)
    (num_nodes, num_edges) = shift_node_ast_to_dot(ast_bug)

    buggy_dot = os.path.join(output_dir, '{}.dot'.format(output_file_name))
    #with open(buggy_dot, 'w') as f:
    #    f.write(ast_bug_dot)

    time_elapsed_file_loading = datetime.datetime.now() - time_start
    if num_nodes <= 50:
        print('stats(less than 50): file:{}, num_nodes:{}, num_edges:{}'.format(output_file_name, num_nodes, num_edges))
    if 50 < num_nodes <= 100:
        print('stats(less than 100): file:{}, num_nodes:{}, num_edges:{}'.format(output_file_name, num_nodes, num_edges))
    if 100 < num_nodes <= 200:
        print('stats(less than 200): file:{}, num_nodes:{}, num_edges:{}'.format(output_file_name, num_nodes, num_edges))
    if 200 < num_nodes <= 300:
        print('stats(less than 300): file:{}, num_nodes:{}, num_edges:{}'.format(output_file_name, num_nodes, num_edges))
    if num_nodes > 300:
        print('stats(more than 300): file:{}, num_nodes:{}, num_edges:{}'.format(output_file_name, num_nodes, num_edges))

    #print('Writing file:{}, took time in seconds'.format(output_file_name, time_elapsed_file_loading.seconds))
    return buggy_dot


def get_file_info(ml_ast_json, list_of_files):
    onlyfiles = []
    for f in listdir(ml_ast_json):
        if isfile(join(ml_ast_json, f)) and f.endswith('.js'):
            prefix = _get_prefix(f)
            prefix = "SHIFT_{}".format(prefix)
            if prefix in list_of_files:
                onlyfiles.append(f)

    file_map = {}
    for file in onlyfiles:
        prefix = _get_prefix(file)
        if '_buggy' in file:
            buggy_json_file_name = "SHIFT_{}_buggy.json".format(prefix)
            file_map[prefix] = {'buggy_file': buggy_json_file_name}

    print('Number of datapoints', len(file_map))
    return file_map


def init_queue(queue):
    globals()['queue'] = queue


parser = argparse.ArgumentParser()
parser.add_argument('--read_path', help='Folder path of files', required=False)
parser.add_argument('--split_name', help='Name of dataset split i.e. train, val, or test', required=False)
parser.add_argument('--output_dir', help='output directory for the dot files', required=False)

if __name__ == '__main__':
    args = parser.parse_args()
    read_path = args.read_path
    split_name = args.split_name
    output_dir = args.output_dir

    time_start = datetime.datetime.now()
    test_file_prefixes = []
    with open("./dataset-dev/{}.txt".format(split_name)) as file:
        for line in file:
            line = line.strip()
            test_file_prefixes.append(line)

    print('start loading file info')
    test_file_map = get_file_info(read_path, test_file_prefixes)
    print('done loading file_info')

    queue = queue.Queue()
    with ThreadPoolExecutor(max_workers=10,
                            initializer=init_queue,
                            initargs=(queue,)) as executor:
        print('produce items')
        for i, item in enumerate(test_file_map.items()):
            executor.submit(produce, i, read_path, output_dir, item)

    print('done producing items')
    print('queue size:{}'.format(queue.qsize()))

    time_elapsed = datetime.datetime.now() - time_start
    print('Execution time in seconds {} for writing dot files.'.format(time_elapsed.seconds))
