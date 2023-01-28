import os
import resource
import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from graph4nlp.pytorch.models.graph2seq import Graph2Seq
from graph4nlp.pytorch.models.graph2seq_loss import Graph2SeqLoss
from graph4nlp.pytorch.modules.evaluation import BLEU
from graph4nlp.pytorch.modules.graph_construction.node_embedding_based_refined_graph_construction import (  # noqa
    NodeEmbeddingBasedRefinedGraphConstruction,
)

from args import get_args
from build_model import get_model
from ast_dataset import collate_fn
from generic_graph_construction import GenericGraphConstruction
from utils import WarmupCosineSchedule, get_log, wordid2str

rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)
import csv

class NMT:
    def __init__(self, opt):
        super(NMT, self).__init__()
        self.opt = opt
        self.use_copy = self.opt["decoder_args"]["rnn_decoder_share"]["use_copy"]
        assert self.use_copy is False, print("Copy is not fit to NMT")
        self.use_coverage = self.opt["decoder_args"]["rnn_decoder_share"]["use_coverage"]
        self._build_device(self.opt)
        self._build_logger(self.opt["log_dir"])
        self._build_dataloader()
        self._build_model()
        self._build_optimizer()
        self._build_evaluation()
        self._build_loss_function()

    def _build_device(self, opt):
        seed = opt["seed"]
        np.random.seed(seed)
        if opt["use_gpu"] != 0 and torch.cuda.is_available():
            print("[ Using CUDA ]")
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            from torch.backends import cudnn

            cudnn.benchmark = True
            device = torch.device("cuda" if opt["gpu"] < 0 else "cuda:%d" % opt["gpu"])
        else:
            print("[ Using CPU ]")
            device = torch.device("cpu")
        self.device = device

    def _build_logger(self, log_dir):
        log_path = os.path.join(log_dir, self.opt["name"])
        logger_path = os.path.join(log_path, "txt")
        tensorboard_path = os.path.join(log_path, "tensorboard")
        if not os.path.exists(logger_path):
            os.makedirs(logger_path)
        if not os.path.exists(tensorboard_path):
            os.makedirs(tensorboard_path)
        self.logger = get_log(logger_path + "log.txt")
        self.writer = SummaryWriter(log_dir=tensorboard_path)

    def _build_dataloader(self):
        if (
            self.opt["graph_construction_args"]["graph_construction_share"]["graph_type"]
            == "dependency"
        ):
            topology_builder = GenericGraphConstruction
            graph_type = "static-ast"
            dynamic_init_topology_builder = None
        else:
            raise NotImplementedError("Define your topology builder.")

        from ast_dataset import ASTDataset
        dataset = ASTDataset(
            root_dir=self.opt["graph_construction_args"]["graph_construction_share"]["root_dir"],
            val_split_ratio=self.opt["val_split_ratio"],
            merge_strategy=self.opt["graph_construction_args"]["graph_construction_private"][
                "merge_strategy"
            ],
            edge_strategy=self.opt["graph_construction_args"]["graph_construction_private"][
                "edge_strategy"
            ],
            seed=self.opt["seed"],
            word_emb_size=self.opt["word_emb_size"],
            share_vocab=self.opt["share_vocab"],
            graph_type=graph_type,
            topology_builder=topology_builder,
            topology_subdir=self.opt["graph_construction_args"]["graph_construction_share"][
                "topology_subdir"
            ],
            dynamic_graph_type=None,
            dynamic_init_topology_builder=None,
            dynamic_init_topology_aux_args=None,
        )

        self.test_dataloader = DataLoader(
            dataset.test,
            batch_size=self.opt["batch_size"],
            shuffle=False,
            num_workers=8,
            collate_fn=collate_fn,
        )
        self.vocab = dataset.vocab_model

    def _build_model(self):
        self.model = Graph2Seq.load_checkpoint(
            os.path.join(opt["checkpoint_save_path"], self.opt["name"]), "best.pth"
        ).to(self.device)

    def _build_optimizer(self):
        parameters = [p for p in self.model.parameters() if p.requires_grad]
        self.optimizer = optim.Adam(parameters, lr=self.opt["learning_rate"])
        self.scheduler = WarmupCosineSchedule(
            self.optimizer, warmup_steps=self.opt["warmup_steps"], t_total=self.opt["max_steps"]
        )

    def _build_evaluation(self):
        self.metrics = {"BLEU": BLEU(n_grams=[1, 2, 3, 4])}

    def _build_loss_function(self):
        self.loss = Graph2SeqLoss(
            ignore_index=self.vocab.out_word_vocab.PAD,
            use_coverage=self.use_coverage,
            coverage_weight=0.3,
        )

    def remove_bpe(self, str_with_subword):
        if isinstance(str_with_subword, list):
            return [self.remove_bpe(ss) for ss in str_with_subword]
        symbol = "@@ "
        return str_with_subword.replace(symbol, "").strip()

    def evaluate(self, epoch, split="val"):
        self.model.eval()
        pred_collect = []
        gt_collect = []
        assert split in ["val", "test"]
        dataloader = self.val_dataloader if split == "val" else self.test_dataloader
        for data in dataloader:
            graph, gt_str = data["graph_data"], data["output_str"]
            graph = graph.to(self.device)

            oov_dict = None
            ref_dict = self.vocab.out_word_vocab

            prob, _, _ = self.model(graph, oov_dict=oov_dict)
            pred = prob.argmax(dim=-1)

            pred_str = wordid2str(pred.detach().cpu(), ref_dict)
            pred_collect.extend(self.remove_bpe(pred_str))
            gt_collect.extend(self.remove_bpe(gt_str))

        score = self.metrics["BLEU"].calculate_scores(ground_truth=gt_collect, predict=pred_collect)
        self.logger.info(
            "Evaluation results in `{}` split: BLEU-1:{:.4f}\tBLEU-2:{:.4f}\tBLEU-3:{:.4f}\t"
            "BLEU-4:{:.4f}".format(split, score[0][0], score[0][1], score[0][2], score[0][3])
        )
        self.writer.add_scalar(split + "/BLEU@1", score[0][0] * 100, global_step=epoch)
        self.writer.add_scalar(split + "/BLEU@2", score[0][1] * 100, global_step=epoch)
        self.writer.add_scalar(split + "/BLEU@3", score[0][2] * 100, global_step=epoch)
        self.writer.add_scalar(split + "/BLEU@4", score[0][3] * 100, global_step=epoch)
        return score[0][-1]

    @torch.no_grad()
    def translate(self):
        self.model.eval()

        pred_collect = []
        gt_collect = []
        dataloader = self.test_dataloader
        for data in dataloader:
            batch_graph, gt_str = data["graph_data"], data["output_str"]

            oov_dict = None
            ref_dict = self.vocab.out_word_vocab
            batch_graph = batch_graph.to(self.device)

            pred = self.model.translate(
                batch_graph=batch_graph, oov_dict=oov_dict, beam_size=3, topk=1
            )

            pred_ids = pred[:, 0, :]  # we just use the top-1

            pred_str = wordid2str(pred_ids.detach().cpu(), ref_dict)

            pred_collect.extend(pred_str)
            gt_collect.extend(gt_str)

            print("gt_str:{}||||pred_str:{}".format(gt_str, pred_str))

        score = self.metrics["BLEU"].calculate_scores(ground_truth=gt_collect, predict=pred_collect)
        self.logger.info(
            "Evaluation results in `{}` split: BLEU-1:{:.4f}\tBLEU-2:{:.4f}\tBLEU-3:{:.4f}\t"
            "BLEU-4:{:.4f}".format("test", score[0][0], score[0][1], score[0][2], score[0][3])
        )
        self.writer.add_scalar("test" + "/BLEU@1", score[0][0] * 100, global_step=0)
        self.writer.add_scalar("test" + "/BLEU@2", score[0][1] * 100, global_step=0)
        self.writer.add_scalar("test" + "/BLEU@3", score[0][2] * 100, global_step=0)
        self.writer.add_scalar("test" + "/BLEU@4", score[0][3] * 100, global_step=0)

        with open('inference.csv', mode='w') as inference_file:
            inference_writer = csv.writer(inference_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            count = 0
            for (g, p) in zip(gt_collect, pred_collect):
                inference_writer.writerow([g, p])
                p = p.replace("$ string $", "$string$")
                p = p.replace("$ number $", "$number$")
                if g == p:
                    count = count + 1
            print("Accuracy: {}".format(100 * count / len(gt_collect)))
        return score


if __name__ == "__main__":
    opt = get_args()
    runner = NMT(opt)
    runner.logger.info("\tRunner name: {}".format(opt["name"]))
    runner.translate()
    runner.logger.info("Done.")
