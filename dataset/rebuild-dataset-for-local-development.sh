# set -x
start_time="$(date -u +%s)"

rm -rf final-dataset-dev
mkdir final-dataset-dev

rm -rf merged-dataset
mkdir merged-dataset

# generate_dot_files - train, test, dev
rm -rf ./buggy-dot-files/train && mkdir -p ./buggy-dot-files/train
rm -rf ./buggy-dot-files/test && mkdir -p ./buggy-dot-files/test
rm -rf ./buggy-dot-files/val && mkdir -p ./buggy-dot-files/val
python generate_buggy_file_dot_dev.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/train --split_name train
python generate_buggy_file_dot_dev.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/test  --split_name test
python generate_buggy_file_dot_dev.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/val   --split_name val

# get stats only
# python generate_buggy_file_dot_dev_descriptive_stats.py --read_path /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset-s3/slice4context/model-sliced/hoppity-data/ml_astJSON --output_dir ./buggy-dot-files/train --split_name train

find ./buggy-dot-files/train/ -type f -name "*.dot" -exec cp -p {} merged-dataset/ \; -print
find ./buggy-dot-files/test/ -type f -name "*.dot" -exec cp -p {} merged-dataset/ \; -print
find ./buggy-dot-files/val/ -type f -name "*.dot" -exec cp -p {} merged-dataset/ \; -print

./generate_correct_file_line_diff_dev.sh
find correct-lines/train-correct/ -type f -name "*.txt" -exec cp -p {} merged-dataset/ \; -print
find correct-lines/test-correct/ -type f -name "*.txt" -exec cp -p {} merged-dataset/ \; -print
find correct-lines/val-correct/ -type f -name "*.txt" -exec cp -p {} merged-dataset/ \; -print
mv merged-dataset/ final-dataset-dev/merged-dataset/

mkdir final-dataset-dev/raw
cp -p dataset-dev/test.txt final-dataset-dev/raw
cp -p dataset-dev/train.txt final-dataset-dev/raw
cp -p dataset-dev/val.txt final-dataset-dev/raw

rm final-dataset-dev.tar.gz
tar -czvf final-dataset-dev.tar.gz final-dataset-dev/

# also keep a copy of the dataset in the slice4context-dataset folder
cp -p final-dataset-dev.tar.gz /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset/

# free mac memory
# sudo purge

# DATASET
num_train_samples=$(wc -l dataset-dev/train.txt)
num_test_samples=$(wc -l dataset-dev/test.txt)
num_val_samples=$(wc -l dataset-dev/val.txt)

# DOT file stats
count_train_dot=$(find buggy-dot-files/train -type f -name '*.dot' -exec echo \; | wc -l)
count_test_dot=$(find buggy-dot-files/test -type f -name '*.dot' -exec echo \; | wc -l)
count_val_dot=$(find buggy-dot-files/val -type f -name '*.dot' -exec echo \; | wc -l)

# CORRECT file stats
count_train_correct=$(find correct-lines/train-correct/ -type f -name '*-correct.txt' -exec echo \; | wc -l)
count_test_correct=$(find correct-lines/test-correct/ -type f -name '*-correct.txt' -exec echo \; | wc -l)
count_val_correct=$(find correct-lines/val-correct/ -type f -name '*-correct.txt' -exec echo \; | wc -l)

# PRINT ALL STATS
echo "num_train_samples=${num_train_samples}"
echo "num_test_samples=${num_test_samples}"
echo "num_val_samples=${num_val_samples}"

echo "CHECK THE NUMBERS FOR DOT FILES ARE MATCHING WITH num_train_samples, num_test_samples, num_val_samples."
echo "count_train_dot=${count_train_dot}"
echo "count_test_dot=${count_test_dot}"
echo "count_val_dot=${count_val_dot}"
if [ "${num_train_samples}" -ne "${count_train_dot}" ]; then
  echo "warning: count not matching."
fi
if [ "${num_test_samples}" -ne "${count_test_dot}" ]; then
  echo "warning: count not matching."
fi
if [ "${num_val_samples}" -ne "${count_val_dot}" ]; then
  echo "warning: count not matching."
fi

echo "CHECK THE NUMBERS FOR CORRECT FILES ARE MATCHING WITH num_train_samples, num_test_samples, num_val_samples."
echo "count_train_correct=${count_train_correct}"
echo "count_test_correct=${count_test_correct}"
echo "count_val_correct=${count_val_correct}"
if [ "${num_train_samples}" -ne "${count_train_correct}" ]; then
  echo "warning: count not matching."
fi
if [ "${num_test_samples}" -ne "${count_test_correct}" ]; then
  echo "warning: count not matching."
fi
if [ "${num_val_samples}" -ne "${count_val_correct}" ]; then
  echo "warning: count not matching."
fi

end_time="$(date -u +%s)"
elapsed="$(($end_time - $start_time))"
echo "script took = $elapsed seconds for building dev dataset"
