#!/bin/bash

set -x

rm train_bugs_info.csv
rm val_bugs_info.csv
rm test_bugs_info.csv

rm -rf train-correct
mkdir train-correct
python generate_correct_file_line_diff.py --path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_raw --split_name train

rm -rf val-correct
mkdir val-correct
python generate_correct_file_line_diff.py --path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_raw --split_name val

rm -rf test-correct
mkdir test-correct
python generate_correct_file_line_diff.py --path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_raw --split_name test

rm -rf correct-lines
mkdir correct-lines
mv train-correct correct-lines/
mv val-correct correct-lines/
mv test-correct correct-lines/