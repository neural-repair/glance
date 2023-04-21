## GLANCE
This repository accompanies the GLANCE paper, which is currently under review. The code is provided as a supplementary material to the paper. Deep learning-based program repair has received significant attention from the research community lately. Most existing techniques treat source code as a sequence of tokens or abstract syntax trees. Consequently, they cannot incorporate semantic contextual information pertaining to a buggy line of code and its fix. In this work, we propose a program repair technique called GLANCE that combines static program analysis with graph-to-sequence learning for capturing contextual information. To represent contextual information, we introduce a graph representation that can encode information about the buggy code and its repair ingredients by embedding control and data flow information.  We employ a fine-grained graphical code representation, which explicitly describes code change context and embeds semantic relationships between code elements. GLANCE leverages a graph neural network and a sequence-based decoder to learn from this semantic code representation. We evaluated our work against six state-of-the-art techniques and our results show that GLANCE fixes 52\% more bugs than the best-performing technique.

## Paper
[Embedding Context as Code Dependencies for Neural Program Repair](https://people.ece.ubc.ca/amesbah/resources/papers/icst23.pdf), Published at IEEE International Conference on Software Testing, Verification and Validation (ICST), 2023.

## Directory Structure
Each of the following folders contains instructions in their individual README.md files:

- `data-collection`: contains the scripts for collecting dataset from GitHub. Follow the instructions in the [README.md](./data-collection/README.md) file in this folder to collect the dataset.
- `dataset/`: contains the data used in the paper. This [README.md](./dataset/README.md) file describes the format of the dataset.
- `model/` : contains the code for the GNN model. Follow the instructions in the [README.md](./model/README.md) file for model training and inference.
- `program-analysis`: contains the scripts to do the static backward analysis. Follow the instructions in the [README.md](./program-analysis/README.md) file in this folder to run the static analysis.
