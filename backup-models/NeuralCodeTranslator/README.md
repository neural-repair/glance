Steps how to run [NeuralCodeTranslator](https://arxiv.org/pdf/1812.08693.pdf).

# HOW TO CREATE A NEW CONDA ENVIRONMENT?
```
conda create -n neuralcodetranslator python=3.6
conda activate neuralcodetranslator
```

# Setup Google Seq2Seq
```
git clone https://github.com/google/seq2seq
cd seq2seq

conda install -y -c conda-forge tensorflow=1.5.1
conda install pyyaml==5.1

# Install package and dependencies
pip install -e .

# test the installation is successful
python -m unittest seq2seq.test.pipeline_test
```

# COMMANDS TO RUN TRAINING AND TEST
Before training, remove old artifacts:
``` 
rm -rf model
```

Run training and evaluation:
```
cd seq2seq
mkdir -p ../model/bug-fixes/s4r/

# 50K steps
./train_test.sh ../dataset-slice4repair/bug-fixes/s4r/ 50000 ../model/bug-fixes/s4r/ best_configuration
```

Arguments:
- `dataset_path` : path to the dataset containing the folders: train, eval, test.
- `num_iterations` : number of training iterations.
- `model_path` : path where to save the model's checkpoints and predictions.
- `config_ID` : ID of the configuration to be used. The IDs are the file names (without the `.yml` extension) available in the folder `config`.

# RUNNING FOR SPECIFIC BEAM WIDTH
```
bash inference.sh ../dataset-slice4repair/bug-fixes/s4r/ ../model/bug-fixes/s4r/
```