"""
Graph Attention Networks in Grap4NLP using SPMV optimization.
Multiple heads are also batched together for faster training.
References
----------
DGL GAT example: https://github.com/dmlc/dgl/tree/master/examples/pytorch/gat
"""
import os
import time
import argparse
import numpy as np
import networkx as nx
from collections import namedtuple
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.backends.cudnn as cudnn
import dgl
from dgl import DGLGraph
from dgl.data import register_data_args, load_data

from .utils import EarlyStopping
from ...modules.utils.generic_utils import *
from ...modules.graph_embedding.gat import GAT
from ...data.data import GraphData
from graph4nlp.pytorch.modules.utils.logger import Logger


def accuracy(logits, labels):
    _, indices = torch.max(logits, dim=1)
    correct = torch.sum(indices == labels)
    return correct.item() * 1.0 / len(labels)

def evaluate(model, g, labels, mask):
    model.eval()
    with torch.no_grad():
        logits = model(g)
        logits = logits[mask]
        labels = labels[mask]
        return accuracy(logits, labels)

class GNNClassifier(nn.Module):
    def __init__(self,
                num_layers,
                input_size,
                hidden_size,
                output_size,
                num_heads,
                num_out_heads,
                direction_option,
                feat_drop=0.6,
                attn_drop=0.6,
                negative_slope=0.2,
                residual=False,
                activation=F.elu):
        super(GNNClassifier, self).__init__()
        self.direction_option = direction_option
        heads = [num_heads] * (num_layers - 1) + [num_out_heads]
        self.model = GAT(num_layers,
                    input_size,
                    hidden_size,
                    output_size,
                    heads,
                    direction_option=direction_option,
                    feat_drop=feat_drop,
                    attn_drop=attn_drop,
                    negative_slope=negative_slope,
                    residual=residual,
                    activation=activation)

        if self.direction_option == 'bi_sep':
            self.fc = nn.Linear(2 * output_size, output_size)

    def forward(self, graph):
        graph = self.model(graph)
        logits = graph.node_features['node_emb']
        if self.direction_option == 'bi_sep':
            logits = self.fc(F.elu(logits))

        return logits

def prepare_dgl_graph_data(args):
    data = load_data(args)
    features = torch.FloatTensor(data.features)
    labels = torch.LongTensor(data.labels)
    if hasattr(torch, 'BoolTensor'):
        train_mask = torch.BoolTensor(data.train_mask)
        val_mask = torch.BoolTensor(data.val_mask)
        test_mask = torch.BoolTensor(data.test_mask)
    else:
        train_mask = torch.ByteTensor(data.train_mask)
        val_mask = torch.ByteTensor(data.val_mask)
        test_mask = torch.ByteTensor(data.test_mask)

    num_feats = features.shape[1]
    n_classes = data.num_labels
    n_edges = data.graph.number_of_edges()
    print("""----Data statistics------'
      #Edges %d
      #Classes %d
      #Train samples %d
      #Val samples %d
      #Test samples %d""" %
          (n_edges, n_classes,
           train_mask.int().sum().item(),
           val_mask.int().sum().item(),
           test_mask.int().sum().item()))

    g = data.graph
    # add self loop
    g.remove_edges_from(nx.selfloop_edges(g))
    g = DGLGraph(g)
    g.add_edges(g.nodes(), g.nodes())
    n_edges = g.number_of_edges()

    data = {'features': features,
            'graph': g,
            'train_mask': train_mask,
            'val_mask': val_mask,
            'test_mask': test_mask,
            'labels': labels,
            'num_feats': num_feats,
            'n_classes': n_classes,
            'n_edges': n_edges}

    return data

def prepare_ogbn_graph_data(args):
    from ogb.nodeproppred import DglNodePropPredDataset

    dataset = DglNodePropPredDataset(name=args.dataset)

    split_idx = dataset.get_idx_split()
    train_idx, val_idx, test_idx = torch.LongTensor(split_idx['train']), torch.LongTensor(split_idx['valid']), torch.LongTensor(split_idx['test'])
    g, labels = dataset[0] # graph: dgl graph object, label: torch tensor of shape (num_nodes, num_tasks)
    features = torch.Tensor(g.ndata['feat'])
    labels = torch.LongTensor(labels).squeeze(-1)

    if args.to_undirected:
        inv_edge_index = (g.edges()[1], g.edges()[0])
        g = dgl.add_edges(g, inv_edge_index[0], inv_edge_index[1])
        print('convert the input graph to undirected graph')


    # add self loop
    # no duplicate self loop will be added for nodes already having self loops
    new_g = dgl.transform.add_self_loop(g)


    num_feats = features.shape[1]
    n_classes = labels.max().item() + 1
    n_edges = new_g.number_of_edges()
    print("""----Data statistics------'
      #Edges %d
      #Classes %d
      #Train samples %d
      #Val samples %d
      #Test samples %d""" %
          (n_edges, n_classes,
           train_idx.shape[0],
           val_idx.shape[0],
           test_idx.shape[0]))

    data = {'features': features,
            'graph': new_g,
            'train_mask': train_idx,
            'val_mask': val_idx,
            'test_mask': test_idx,
            'labels': labels,
            'num_feats': num_feats,
            'n_classes': n_classes,
            'n_edges': n_edges}

    return data

def main(args, seed):
    # load and preprocess dataset
    if args.dataset.startswith('ogbn'):
        # Open Graph Benchmark datasets
        data = prepare_ogbn_graph_data(args)
    else:
        # DGL datasets
        data = prepare_dgl_graph_data(args)

    features, dgl_graph, train_mask, val_mask, test_mask, labels, num_feats, n_classes, n_edges\
                             = data['features'], data['graph'], data['train_mask'], \
                             data['val_mask'], data['test_mask'], data['labels'], \
                             data['num_feats'], data['n_classes'], data['n_edges']


    # Configure
    np.random.seed(seed)
    torch.manual_seed(seed)

    if not args.no_cuda and torch.cuda.is_available():
        print('[ Using CUDA ]')
        device = torch.device('cuda' if args.gpu < 0 else 'cuda:%d' % args.gpu)
        cudnn.benchmark = True
        torch.cuda.manual_seed(seed)
    else:
        device = torch.device('cpu')

    features = features.to(device)
    labels = labels.to(device)
    train_mask = train_mask.to(device)
    val_mask = val_mask.to(device)
    test_mask = test_mask.to(device)

    dgl_graph.ndata['node_feat'] = features

    # convert DGLGraph to GraphData
    g = GraphData()
    g.from_dgl(dgl_graph)

    # create model
    model = GNNClassifier(args.num_layers,
                    num_feats,
                    args.num_hidden,
                    n_classes,
                    args.num_heads,
                    args.num_out_heads,
                    direction_option=args.direction_option,
                    feat_drop=args.in_drop,
                    attn_drop=args.attn_drop,
                    negative_slope=args.negative_slope,
                    residual=args.residual,
                    activation=F.elu)


    print(model)
    model.to(device)

    if args.early_stop:
        stopper = EarlyStopping('{}.{}'.format(args.save_model_path, seed), patience=args.patience)

    if args.use_log_softmax_nll:
        loss_fcn = torch.nn.NLLLoss()
    else:
        loss_fcn = torch.nn.CrossEntropyLoss()

    # use optimizer
    optimizer = torch.optim.Adam(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    # initialize graph
    dur = []
    for epoch in range(args.epochs):
        model.train()
        if epoch >= 3:
            t0 = time.time()
        # forward
        logits = model(g)
        if args.use_log_softmax_nll:
            logits = logits.log_softmax(dim=-1)

        loss = loss_fcn(logits[train_mask], labels[train_mask])

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if epoch >= 3:
            dur.append(time.time() - t0)

        train_acc = accuracy(logits[train_mask], labels[train_mask])

        if args.fastmode:
            val_acc = accuracy(logits[val_mask], labels[val_mask])
        else:
            val_acc = evaluate(model, g, labels, val_mask)

        val_loss = loss_fcn(logits[val_mask], labels[val_mask])

        if args.early_stop:
            if stopper.step(-val_loss, model):
                break

        print("Epoch {:05d} | Time(s) {:.4f} | Loss {:.4f} | TrainAcc {:.4f} |"
              " ValLoss {:.4f} | ValAcc {:.4f} | ETputs(KTEPS) {:.2f}".
              format(epoch, np.mean(dur), loss.item(), train_acc,
                     val_loss, val_acc, n_edges / np.mean(dur) / 1000))

    print()
    if args.early_stop:
        model = stopper.load_checkpoint(model)
        print('Restored best saved model')
        os.remove(stopper.save_model_path)
        print('Removed best saved model file to save disk space')

    acc = evaluate(model, g, labels, test_mask)
    print("Test Accuracy {:.4f}".format(acc))

    return acc

def multi_run(config):
    config['save_model_path'] = '{}_{}_{}_{}'.format(config['save_model_path'], config['dataset'], 'gcn', config['direction_option'])
    print_config(config)

    logger = Logger(config['save_model_path'], config=config, overwrite=True)

    config = dict_to_namedtuple(config)
    np.random.seed(config.random_seed)
    scores = []
    for _ in range(config.num_runs):
        seed = np.random.randint(10000)
        scores.append(main(config, seed))

    print("\nTest Accuracy ({} runs): mean {:.4f}, std {:.4f}".format(config.num_runs, np.mean(scores), np.std(scores)))
    logger.write("\nTest Accuracy ({} runs): mean {:.4f}, std {:.4f}".format(config.num_runs, np.mean(scores), np.std(scores)))
    logger.close()

def grid_search_main(config):
    print_config(config)
    grid_search_hyperparams = []
    for k, v in config.items():
        if isinstance(v, list):
            grid_search_hyperparams.append(k)


    logger = Logger(config['save_model_path'], config=config, overwrite=True)

    best_config = None
    best_score = -1
    configs = grid(config)
    for cnf in configs:
        print('\n')
        for k in grid_search_hyperparams:
            cnf['save_model_path'] += '_{}_{}'.format(k, cnf[k])
        print(cnf['save_model_path'])
        logger.write(cnf['save_model_path'])


        score = main(dict_to_namedtuple(cnf), cnf['random_seed'])
        if best_score < score:
            best_score = score
            best_config = cnf
            print('Found a better configuration: {}'.format(best_score))
            logger.write('Found a better configuration: {}'.format(best_score))

    print('\nBest configuration:')
    logger.write('\nBest configuration:')

    for k in grid_search_hyperparams:
        print('{}: {}'.format(k, best_config[k]))
        logger.write('{}: {}'.format(k, best_config[k]))


    print('Best test score: {}'.format(best_score))
    logger.write('Best test score: {}'.format(best_score))
    logger.close()

def dict_to_namedtuple(data, typename='config'):
    return namedtuple(typename, data.keys())(
        *(dict_to_namedtuple(typename + '_' + k, v) if isinstance(v, dict) else v for k, v in data.items())
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-config', type=str, help='path to the config file')
    parser.add_argument('--grid_search', action='store_true', help='flag: grid search')
    cfg = vars(parser.parse_args())

    config = get_config(cfg['config'])
    if cfg['grid_search']:
        grid_search_main(config)
    else:
        multi_run(config)



# if __name__ == '__main__':

#     parser = argparse.ArgumentParser(description='GAT')
#     register_data_args(parser)
#     parser.add_argument("--num-runs", type=int, default=5,
#                         help="number of runs")
#     parser.add_argument("--no-cuda", action="store_true", default=False,
#                         help="use CPU")
#     parser.add_argument("--gpu", type=int, default=-1,
#                         help="which GPU to use.")
#     parser.add_argument("--epochs", type=int, default=200,
#                         help="number of training epochs")
#     parser.add_argument("--to_undirected", action="store_true", default=False,
#                         help="convert to undirected graph")
#     parser.add_argument("--direction-option", type=str, default='bi_sep',
#                         help="direction type (`'undirected'`, `'bi_fuse'`, `'bi_sep'`)")
#     parser.add_argument("--num-heads", type=int, default=8,
#                         help="number of hidden attention heads")
#     parser.add_argument("--num-out-heads", type=int, default=1,
#                         help="number of output attention heads")
#     parser.add_argument("--num-layers", type=int, default=2,
#                         help="number of hidden layers")
#     parser.add_argument("--num-hidden", type=int, default=8,
#                         help="number of hidden units")
#     parser.add_argument("--residual", action="store_true", default=False,
#                         help="use residual connection")
#     parser.add_argument("--in-drop", type=float, default=.6,
#                         help="input feature dropout")
#     parser.add_argument("--attn-drop", type=float, default=.6,
#                         help="attention dropout")
#     parser.add_argument("--lr", type=float, default=0.005,
#                         help="learning rate")
#     parser.add_argument('--weight-decay', type=float, default=5e-4,
#                         help="weight decay")
#     parser.add_argument('--negative-slope', type=float, default=0.2,
#                         help="the negative slope of leaky relu")
#     parser.add_argument('--early-stop', action='store_true', default=False,
#                         help="indicates whether to use early stop or not")
#     parser.add_argument("--patience", type=int, default=100,
#                         help="early stopping patience")
#     parser.add_argument('--fastmode', action="store_true", default=False,
#                         help="skip re-evaluate the validation set")
#     parser.add_argument('--save-model-path', type=str, default="checkpoint",
#                         help="path to the best saved model")
#     args = parser.parse_args()
#     args.save_model_path = '{}_{}_{}_{}'.format(args.save_model_path, args.dataset, 'gat', args.direction_option)
#     print(args)

#     np.random.seed(123)
#     scores = []
#     for _ in range(args.num_runs):
#         seed = np.random.randint(10000)
#         scores.append(main(args, seed))

#     print("\nTest Accuracy ({} runs): mean {:.4f}, std {:.4f}".format(args.num_runs, np.mean(scores), np.std(scores)))
