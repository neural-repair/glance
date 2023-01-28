# Steps - setup and run the Graph2Seq model. 

### Prerequisite

- Install conda
```
curl -O https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh
bash Anaconda3-2019.03-Linux-x86_64.sh
```

### CREATE CONDA ENVIRONMENT AND INSTALL DEPENDENCIES
Create a new conda environment `gcn-nmt`:

```
conda create -n gcn-nmt python=3.9
conda activate gcn-nmt

cd graph4nlp/
conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch
pip install torchtext
pip install tensorboard
conda install pydot

./configure
python setup.py install
```

### RUN TRAINING
Run training with the following command:

```
./training-gcn.sh
```



