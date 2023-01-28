#!/bin/bash

set -x

rm -rf ./buggy-dot-files/train
mkdir -p ./buggy-dot-files/train

python generate_buggy_file_dot.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/train --split_name train
