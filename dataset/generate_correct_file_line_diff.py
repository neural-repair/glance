import csv
import sys
import os
import mmap
import queue
import difflib
import argparse
import datetime
import traceback
from os import listdir
from os.path import isfile, join
from concurrent.futures import ThreadPoolExecutor

def produce(i, mypath, output_folder, item):
    #print('processing item {} - file prefix {}'.format(i, item[0]))
    data = generate_file(mypath, output_folder, item)
    queue.put(data)
    #print('submitted to queue item {}'.format(i))


def bin2str(text, encoding='utf-8'):
    return text.decode(encoding)


def mmap_io(mypath, filename):
    lines = []
    try:
        with open(mypath + '/' + filename, "rb", buffering=0) as f:
            m = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
            m.madvise(mmap.MADV_SEQUENTIAL)
            while True:
                line = m.readline()
                if line:
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


def find_diff(mypath, fileAName, fileBName):
    try:
        # fileA = open(mypath + '/' + fileAName, "rt", encoding="utf-8").readlines()
        fileA = mmap_io(mypath, fileAName)
        # fileB = open(mypath + '/' + fileBName, "rt", encoding="utf-8").readlines()
        fileB = mmap_io(mypath, fileBName)
    except:
        return None, None, None

    if len(fileA) != len(fileB) or len(fileA) == 0 or len(fileB) == 0:
        return None, None, None
    d = difflib.Differ()
    diffs = d.compare(fileA, fileB)

    lineNum = 0

    final_line_num = None
    patch_line = None
    buggy_line = None

    for line in diffs:
        code = line[:2]
        # print(code)
        # if the  line is in both files or just b, increment the line number.
        if code in ("  ", "+ "):
            lineNum += 1
        # if this line is only in b, print the line number and the text on the line
        if code == "- ":
            buggy_line = line[2:].strip('\n').strip()
        if code == "+ ":
            final_line_num = lineNum
            patch_line = line[2:].strip('\n').strip()

    return final_line_num, patch_line, buggy_line


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


def generate_file(mypath, output_dir, item):
    time_start = datetime.datetime.now()
    line_num, fixed_line, buggy_line = find_diff(mypath, item[1]['buggy_file'], item[1]['fixed_file'])
    if line_num and not is_whitespace_diff(buggy_line, fixed_line):
        time_elapsed = datetime.datetime.now() - time_start
        # print('Elapsed time in seconds for file {}:'.format(item[0]), time_elapsed.seconds)
        data = [item[1]['buggy_file'], item[1]['fixed_file'], line_num, buggy_line, fixed_line]

        prefix_correct_file_name = _get_prefix(item[1]['fixed_file'])
        correct_output_file_name = os.path.join(output_dir, '{}-correct.txt'.format(prefix_correct_file_name))
        with open(correct_output_file_name, 'w') as f:
            f.write(fixed_line)
            if fixed_line == "" or fixed_line is None:
                print("empty line difference:buggy_file{}, fixed_file:{}".format(item[1]['buggy_file'], item[1]['fixed_file']))
        return data
    else:
        print("empty line difference:buggy_file{}, fixed_file:{}".format(item[1]['buggy_file'], item[1]['fixed_file']))
        prefix_correct_file_name = _get_prefix(item[1]['fixed_file'])
        correct_output_file_name = os.path.join(output_dir, '{}-correct.txt'.format(prefix_correct_file_name))
        with open(correct_output_file_name, 'w') as f:
            f.write("dummy")


def get_file_info(ml_raw, list_of_files):
    onlyfiles = []
    for f in listdir(ml_raw):
        if isfile(join(ml_raw, f)) and f.endswith('.js'):
            prefix = _get_prefix(f)
            prefix = "SHIFT_{}".format(prefix)
            if prefix in list_of_files:
                onlyfiles.append(f)

    file_map = {}
    for file in onlyfiles:
        prefix = _get_prefix(file)
        if 'xml' in file:
            continue

        if '_buggy' in file:
            if prefix not in file_map:
                file_map[prefix] = {'buggy_file': file}
            else:
                file_map[prefix]['buggy_file'] = file
        elif '_fixed' in file:
            if prefix in file_map:
                file_map[prefix]['fixed_file'] = file
            else:
                file_map[prefix] = {'fixed_file': file}

    print('Number of datapoints', len(file_map))
    return file_map


def init_queue(queue):
    globals()['queue'] = queue

parser = argparse.ArgumentParser()
parser.add_argument('--path', help='Folder path of files', required=False)
parser.add_argument('--split_name', help='Name of dataset split i.e. train, val, or test', required=False)

if __name__ == '__main__':
    args = parser.parse_args()
    path = args.path
    split_name = args.split_name
    output_folder = "./{}-correct".format(split_name)

    time_start = datetime.datetime.now()
    test_file_prefixes = []
    with open("./dataset/{}.txt".format(split_name)) as file:
        for line in file:
            line = line.strip()
            test_file_prefixes.append(line)

    print('start loading file info')
    test_file_map = get_file_info(path, test_file_prefixes)
    print('done loading file_info')

    time_elapsed = datetime.datetime.now() - time_start
    print('Elapsed time in seconds {} to load files'.format(time_elapsed.seconds))
    time_start = datetime.datetime.now()
    queue = queue.Queue()
    with ThreadPoolExecutor(max_workers=10,
                            initializer=init_queue,
                            initargs=(queue,)) as executor:
        for i, item in enumerate(test_file_map.items()):
            executor.submit(produce, i, path, output_folder, item)

    print('done producing items')
    print('queue size:{}'.format(queue.qsize()))
    output_file_name = "./{}_bugs_info.csv".format(split_name)
    with open(output_file_name, 'w', encoding='utf-8', newline='') as f:
        csv.field_size_limit(sys.maxsize)
        writer = csv.writer(f)
        while not queue.empty():
            data = queue.get()
            if data:
                writer.writerow(data)
            else:
                print("warning: no data!")

    time_elapsed = datetime.datetime.now() - time_start
    print('Elapsed time in seconds {} for writing to file: {}'.format(time_elapsed.seconds, output_file_name))
