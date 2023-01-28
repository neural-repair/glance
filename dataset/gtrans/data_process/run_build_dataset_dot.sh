#!/bin/bash

set -x

data_root=/Volumes/t5-ssd/ubc-works/repos/Slice4Context/hoppity-data/ml_astJSON
data_name=deep-context
save_dir=/Volumes/t5-ssd/ubc-works/repos/Slice4Context/hoppity-data/ml_astPKL
max_ast_nodes=500
num_cores=1
gpu=0
save_dir_dot_file=/Volumes/t5-ssd/ubc-works/repos/Slice4Context/hoppity-data/slice4context_dot

data_root=/Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset/slice4context//model-sliced/hoppity-data/ml_astJSON
data_name=deep-context
save_dir=/Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset/slice4context//model-sliced/hoppity-data/ml_astPKL
max_ast_nodes=500
num_cores=1
gpu=0
save_dir_dot_file=/Volumes/t5-ssd/ubc-works/repos/slice4context/hoppity-data/slice4context_dot

python main_build_dataset_dot.py \
    -data_root $data_root \
    -data_name $data_name \
    -save_dir $save_dir \
    -max_ast_nodes 500 \
    -num_cores 4 \
    -gpu 1 \
    -save_dir_dot_file $save_dir_dot_file \
    $@



