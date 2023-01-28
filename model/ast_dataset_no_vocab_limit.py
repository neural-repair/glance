import pickle
from typing import List, Any

import nltk
import torch
from graph4nlp.pytorch.data import GraphData
import os
import pathlib
from graph4nlp.pytorch.data.dataset import Text2TextDataItem, Text2TextDataset
from graph4nlp.pytorch.modules.utils.padding_utils import pad_2d_vals_no_size
from tokenization import tokenize, stem

def tokenize_and_stem(input):
    input = ' '.join(tokenize(input.strip()))
    input = stem(input)
    return input

class ASTDataset(Text2TextDataset):
    @property
    def raw_file_names(self):
        """3 reserved keys: 'train', 'val' (optional), 'test'. Represent the split of dataset."""
        if self.for_inference:
            return {"test": "test.pkl"}
        else:
            return {"train": "train.txt",
                    "val": "val.txt",
                    "test": "test.txt"}

    @property
    def processed_file_names(self):
        """At least 3 reserved keys should be fiiled: 'vocab', 'data' and 'split_ids'."""
        return {"vocab": "vocab.pt", "data": "data.pt"}

    def download(self):
        return

    def parse_file(self, file_path) -> list:
        """
        Read and parse the file specified by `file_path`.
        The file format is specified by each individual task-specific
        base class. Returns all the indices of data items in this file w.r.t. the whole dataset.

        For Text2TextDataset, the format of the input file should contain lines of input,
        each line representing one record of data. The input and output is separated by a tab(\t).

        Examples
        --------
        input: list job use languageid0 job ( ANS ) , language ( ANS , languageid0 )

        DataItem: input_text="list job use languageid0", output_text="job ( ANS ) ,
        language ( ANS , languageid0 )"

        Parameters
        ----------
        file_path: str
            The path of the input file.

        Returns
        -------
        list
            The indices of data items in the file w.r.t. the whole dataset.
        """
        data = []
        with open(file_path) as f:
            lines = f.readlines()

        for line in lines:
            line_text = line.strip()
            # input, output = line_text[0], line_text[1]
            # with this changed input format output fie need to be loaded from file
            data_dir = pathlib.Path(r"{}".format(file_path)).parent.parent

            output_file_name = "{}-correct.txt".format(line_text)
            output_file_name = "{}/merged-dataset/{}".format(data_dir, output_file_name)
            print("loading correct file: {}".format(output_file_name))

            #output_file_name = line_text.split(".")[0].replace('-buggy', '')
            #output_file_name = "{}-correct.txt".format(output_file_name)
            #output_file_name = "{}/dot-files/{}".format(data_dir, output_file_name)

            output = ""
            if os.path.exists(output_file_name):
                with open(output_file_name, 'r') as file:
                    output = file.read().rstrip()
                    output = tokenize_and_stem(output)
            else:
                output = "dummy"
                print("correct file:{} does not exist".format(output_file_name))

            input, output = line_text, output
            if input.strip() == "" or output.strip() == "":
                continue
            input_len = len(input.split())
            output_len = len(output.split())
            if input_len > 50 or output_len > 50:
                print("input length or output_len length is > 50")
                continue

            data_item = Text2TextDataItem(
                input_text=input,
                output_text=output,
                tokenizer=self.tokenizer,
                share_vocab=self.share_vocab,
            )
            data.append(data_item)

        print("stats: file={}, number of entries={}".format(file_path, len(data)))
        return data

    def __init__(
            self,
            root_dir,
            topology_builder,
            topology_subdir,
            #tokenizer=nltk.RegexpTokenizer(" ", gaps=True).tokenize,
            tokenizer=nltk.wordpunct_tokenize,
            pretrained_word_emb_name=None,
            pretrained_word_emb_url=None,
            target_pretrained_word_emb_name=None,
            target_pretrained_word_emb_url=None,
            pretrained_word_emb_cache_dir=".vector_cache/",
            val_split_ratio=None,
            use_val_for_vocab=False,
            graph_type="static",
            merge_strategy="tailhead",
            edge_strategy=None,
            seed=None,
            word_emb_size=300,
            share_vocab=False,
            dynamic_graph_type=None,
            dynamic_init_topology_builder=None,
            dynamic_init_topology_aux_args=None,
            for_inference=False,
            reused_vocab_model=None,
    ):
        """

        Parameters
        ----------
        root_dir: str
            The path of dataset.
        topology_builder: GraphConstructionBase
            The graph construction class.
        topology_subdir: str
            The directory name of processed path.
        graph_type: str, default='static'
            The graph type. Expected in ('static', 'dynamic')
        edge_strategy: str, default=None
            The edge strategy. Expected in (None, 'homogeneous', 'as_node').
            If set `None`, it will be 'homogeneous'.
        merge_strategy: str, default=None
            The strategy to merge sub-graphs. Expected in (None, 'tailhead', 'user_define').
            If set `None`, it will be 'tailhead'.
        share_vocab: bool, default=False
            Whether to share the input vocabulary with the output vocabulary.
        dynamic_graph_type: str, default=None
            The dynamic graph type. It is only available when `graph_type` is set 'dynamic'.
            Expected in (None, 'node_emb', 'node_emb_refined').
        init_graph_type: str, default=None
            The initial graph topology. It is only available when `graph_type` is set 'dynamic'.
            Expected in (None, 'dependency', 'constituency')
        """
        # Initialize the dataset.
        # If the preprocessed files are not found, then do the preprocessing and save them.
        super(ASTDataset, self).__init__(
            root_dir=root_dir,
            topology_builder=topology_builder,
            topology_subdir=topology_subdir,
            graph_type=graph_type,
            edge_strategy=edge_strategy,
            merge_strategy=merge_strategy,
            share_vocab=share_vocab,
            pretrained_word_emb_name=pretrained_word_emb_name,
            pretrained_word_emb_url=pretrained_word_emb_url,
            target_pretrained_word_emb_name=target_pretrained_word_emb_name,
            target_pretrained_word_emb_url=target_pretrained_word_emb_url,
            pretrained_word_emb_cache_dir=pretrained_word_emb_cache_dir,
            val_split_ratio=val_split_ratio,
            seed=seed,
            word_emb_size=word_emb_size,
            tokenizer=tokenizer,
            use_val_for_vocab=use_val_for_vocab,
            dynamic_graph_type=dynamic_graph_type,
            dynamic_init_topology_builder=dynamic_init_topology_builder,
            dynamic_init_topology_aux_args=dynamic_init_topology_aux_args,
            for_inference=for_inference,
            reused_vocab_model=reused_vocab_model,
        )


def collate_fn(data_list):
    graph_data = [item.graph for item in data_list]
    from graph4nlp.pytorch.data.data import to_batch

    big_graph = to_batch(graph_data)

    output_numpy = [item.output_np for item in data_list]
    output_str = [item.output_text.lower().strip() for item in data_list]
    output_pad = pad_2d_vals_no_size(output_numpy)

    tgt_seq = torch.from_numpy(output_pad).long()
    return {"graph_data": big_graph, "tgt_seq": tgt_seq, "output_str": output_str}
