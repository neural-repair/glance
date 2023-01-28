#!/bin/bash

set -x

rm -rf ./buggy-dot-files/test
rm -rf ./buggy-dot-files/val

mkdir -p ./buggy-dot-files/test
mkdir -p ./buggy-dot-files/val

python generate_buggy_file_dot.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/test  --split_name test
python generate_buggy_file_dot.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/val   --split_name val
