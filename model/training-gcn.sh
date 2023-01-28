set -x

root_dir="./model-artifacts"
model_save_dir="./model-artifacts/model"

rm -rf ./model-artifacts/processed/NodeEmbGraph/
rm -rf $root_dir/processed
rm -rf ./model/save/

rm -rf $model_save_dir
mkdir $model_save_dir

start_time="$(date -u +%s)"
python ast_main_with_copy.py --name gcn --num-epoch 5 --gpu 1 --dataset_yaml config/dynamic_gcn_ronin.yaml | tee model-training.log
end_time="$(date -u +%s)"

elapsed="$(($end_time-$start_time))"
echo "model training and inference runtime=$elapsed seconds"

