set -x
start_time="$(date -u +%s)"

rm -rf final-dataset
mkdir final-dataset

rm -rf merged-dataset
mkdir merged-dataset

./generate_dot_files-train.sh
./generate_dot_files-val-test.sh
find ./buggy-dot-files/train/ -type f -name "*.dot" -exec cp -p {} merged-dataset/ \; -print
find ./buggy-dot-files/test/ -type f -name "*.dot" -exec cp -p {} merged-dataset/ \; -print
find ./buggy-dot-files/val/ -type f -name "*.dot" -exec cp -p {} merged-dataset/ \; -print
#mv ./buggy-dot-files/train/*.dot merged-dataset/
#mv ./buggy-dot-files/test/*.dot merged-dataset/
#mv ./buggy-dot-files/val/*.dot merged-dataset/

# free mac memory
#sudo purge

./generate_correct_file_line_diff.sh
find correct-lines/train-correct/ -type f -name "*.txt" -exec cp -p {} merged-dataset/ \; -print
find correct-lines/test-correct/ -type f -name "*.txt" -exec cp -p {} merged-dataset/ \; -print
find correct-lines/val-correct/ -type f -name "*.txt" -exec cp -p {} merged-dataset/ \; -print
#mv correct-lines/train-correct/*.txt merged-dataset/
#mv correct-lines/test-correct/*.txt merged-dataset/
#mv correct-lines/val-correct/*.txt merged-dataset/

mv merged-dataset/ final-dataset/merged-dataset/

mkdir final-dataset/raw
cp -p dataset/test.txt final-dataset/raw
cp -p dataset/train.txt final-dataset/raw
cp -p dataset/val.txt final-dataset/raw

rm final-dataset.tar.gz
tar -czvf final-dataset.tar.gz final-dataset/

# also keep a copy of the dataset in the slice4context-dataset folder
cp -p final-dataset.tar.gz /Volumes/wd-ssd-2tb/ubc-works/repos/slice4context-dataset/

# free mac memory
# sudo purge

# DATASET
num_train_samples=$(wc -l dataset/train.txt)
num_test_samples=$(wc -l dataset/test.txt)
num_val_samples=$(wc -l dataset/val.txt)

# DOT file stats
count_train_dot=$(find buggy-dot-files/train -type f -name '*.dot' -exec echo \;  | wc -l)
count_test_dot=$(find buggy-dot-files/test -type f -name '*.dot' -exec echo \;  | wc -l)
count_val_dot=$(find buggy-dot-files/val -type f -name '*.dot' -exec echo \;  | wc -l)

# CORRECT file stats
count_train_correct=$(find correct-lines/train-correct/ -type f -name '*-correct.txt' -exec echo \;  | wc -l)
count_test_correct=$(find correct-lines/test-correct/ -type f -name '*-correct.txt' -exec echo \;  | wc -l)
count_val_correct=$(find correct-lines/val-correct/ -type f -name '*-correct.txt' -exec echo \;  | wc -l)

# PRINT ALL STATS
echo "num_train_samples=${num_train_samples}"
echo "num_test_samples=${num_test_samples}"
echo "num_val_samples=${num_val_samples}"

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
elapsed="$(($end_time-$start_time))"
echo "script took = $elapsed seconds"
