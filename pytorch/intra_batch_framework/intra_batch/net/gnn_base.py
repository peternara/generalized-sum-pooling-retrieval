from torch_scatter import scatter_mean, scatter_max, scatter_add
import torch
from torch import nn
import math
import torch.nn.functional as F
import numpy as np
import torch
import logging
from .utils import *
from .attentions import MultiHeadDotProduct
import torch.utils.checkpoint as checkpoint
logger = logging.getLogger('GNNReID.GNNModule')


class MetaLayer(torch.nn.Module):
    """
        Core Message Passing Network Class. Extracted from torch_geometric, with minor modifications.
        (https://github.com/rusty1s/pytorch_geometric/blob/master/torch_geometric/nn/meta.py)
    """

    def __init__(self, edge_model=None, node_model=None):
        super(MetaLayer, self).__init__()
        self.edge_model = edge_model # possible to add edge model
        self.node_model = node_model

        self.reset_parameters()

    def reset_parameters(self):
        for item in [self.node_model, self.edge_model]:
            if hasattr(item, 'reset_parameters'):
                item.reset_parameters()

    def forward(self, feats, edge_index, edge_attr=None):

        r, c = edge_index[:, 0], edge_index[:, 1]

        if self.edge_model is not None:
            edge_attr = torch.cat([feats[r], feats[c], edge_attr], dim=1)
            edge_attr = self.edge_model(edge_attr)

        if self.node_model is not None:
            feats, edge_index, edge_attr = self.node_model(feats, edge_index,
                                                           edge_attr)

        return feats, edge_index, edge_attr

    def __repr__(self):
        if self.edge_model:
            return ('{}(\n'
                    '    edge_model={},\n'
                    '    node_model={},\n'
                    ')').format(self.__class__.__name__, self.edge_model,
                                self.node_model)
        else:
            return ('{}(\n'
                '    node_model={},\n'
                ')').format(self.__class__.__name__, self.node_model)



class GNNReID(nn.Module):
    def __init__(self, dev, params: dict = None, embed_dim: int = 2048):
        super(GNNReID, self).__init__()
        num_classes = params['classifier']['num_classes']
        self.dev = dev
        self.params = params
        self.gnn_params = params['gnn']
        
        self.dim_red = nn.Linear(embed_dim, int(embed_dim/params['red']))
        logger.info("Embed dim old {}, new".format(embed_dim, embed_dim/params['red'])) 
        embed_dim = int(embed_dim/params['red'])
        logger.info("Embed dim {}".format(embed_dim))

        self.gnn_model = self._build_GNN_Net(embed_dim=embed_dim)

        # classifier
        self.neck = params['classifier']['neck']
        dim = self.gnn_params['num_layers'] * embed_dim if self.params['cat'] else embed_dim
        every = self.params['every']
        if self.neck:
            layers = [nn.BatchNorm1d(dim) for _ in range(self.gnn_params['num_layers'])] if every else [nn.BatchNorm1d(dim)]
            self.bottleneck = Sequential(*layers)
            for layer in self.bottleneck:
                layer.bias.requires_grad_(False)
                layer.apply(weights_init_kaiming)
            
            layers = [nn.Linear(dim, num_classes, bias=False) for _ in range(self.gnn_params['num_layers'])] if every else [nn.Linear(dim, num_classes, bias=False)]
            self.fc = Sequential(*layers)
            for layer in self.fc:
                layer.apply(weights_init_classifier)
        else:
            layers = [nn.Linear(dim, num_classes) for _ in range(self.gnn_params['num_layers'])] if every else [nn.Linear(dim, num_classes)]
            self.fc = Sequential(*layers)

    def _build_GNN_Net(self, embed_dim: int = 2048):
        # init aggregator
        if self.gnn_params['aggregator'] == "add":
            self.aggr = lambda out, row, dim, x_size: scatter_add(out, row,
                                                                  dim=dim,
                                                                  dim_size=x_size)
        if self.gnn_params['aggregator'] == "mean":
            self.aggr = lambda out, row, dim, x_size: scatter_mean(out,
                                                                   row,
                                                                   dim=dim,
                                                                   dim_size=x_size)
        if self.gnn_params['aggregator'] == "max":
            self.aggr = lambda out, row, dim, x_size: scatter_max(out, row,
                                                                  dim=dim,
                                                                  dim_size=x_size)
        
        gnn = GNNNetwork(embed_dim, self.aggr, self.dev,
                                    self.gnn_params, self.gnn_params['num_layers'] )

        return MetaLayer(node_model=gnn)

    def forward(self, feats, edge_index, edge_attr=None, output_option='norm'):
        r, c = edge_index[:, 0], edge_index[:, 1]
        
        if self.dim_red is not None:
            feats = self.dim_red(feats)

        feats, _, _ = self.gnn_model(feats, edge_index, edge_attr)
        
        if self.params['cat']:
            feats = [torch.cat(feats, dim=1).to(self.dev)]
        elif self.params['every']:
            feats = feats
        else:
            feats = [feats[-1]]
        
        if self.neck:
            features = list()
            for i, layer in enumerate(self.bottleneck):
                f = layer(feats[i])
                features.append(f)
        else:
            features = feats 

        x = list()
        for i, layer in enumerate(self.fc):
            f = layer(features[i])
            x.append(f)
        
        if output_option == 'norm':
            return x, feats
        elif output_option == 'plain':
            return x, [F.normalize(f, p=2, dim=1) for f in feats]
        elif output_option == 'neck' and self.neck:
            return x, features
        elif output_option == 'neck' and not self.neck:
            print("Output option neck only avaiable if bottleneck (neck) is "
                  "enabeled - giving back x and fc7")
            return x, feats

        return x, feats


class GNNNetwork(nn.Module):
    def __init__(self, embed_dim, aggr, dev, gnn_params, num_layers):
        super(GNNNetwork, self).__init__()
        
        layers = [DotAttentionLayer(embed_dim, aggr, dev,
                                    gnn_params) for _
                  in range(num_layers)]

        self.layers = Sequential(*layers)

    def forward(self, feats, edge_index, edge_attr):
        out = list()
        for layer in self.layers:
            feats, egde_index, edge_attr = layer(feats, edge_index, edge_attr)
            out.append(feats)
        return out, edge_index, edge_attr

class DotAttentionLayer(nn.Module):
    def __init__(self, embed_dim, aggr, dev, params, d_hid=None):
        super(DotAttentionLayer, self).__init__()
        num_heads = params['num_heads']
        self.res1 = params['res1']
        self.res2 = params['res2']

        self.att = MultiHeadDotProduct(embed_dim, num_heads, aggr,
                                        mult_attr=params['mult_attr']).to(dev)
        
        d_hid = 4 * embed_dim if d_hid is None else d_hid
        self.mlp = params['mlp']

        self.linear1 = nn.Linear(embed_dim, d_hid) if params['mlp'] else None
        self.dropout = nn.Dropout(params['dropout_mlp'])
        self.linear2 = nn.Linear(d_hid, embed_dim) if params['mlp'] else None

        self.norm1 = LayerNorm(embed_dim) if params['norm1'] else None
        self.norm2 = LayerNorm(embed_dim) if params['norm2'] else None
        self.dropout1 = nn.Dropout(params['dropout_1'])
        self.dropout2 = nn.Dropout(params['dropout_2'])

        self.act = F.relu

        self.dummy_tensor = torch.ones(1, requires_grad=True)

    def custom(self):
        def custom_forward(*inputs):
            feats2 = self.att(inputs[0], inputs[1], inputs[2])
            return feats2
        return custom_forward
    
    def forward(self, feats, egde_index, edge_attr):
        feats2  = self.att(feats, egde_index, edge_attr)
        # if gradient checkpointing should be apllied for the gnn, comment line above and uncomment line below
        #feats2 = checkpoint.checkpoint(self.custom(), feats, egde_index, edge_attr, preserve_rng_state=True)

        feats2 = self.dropout1(feats2)
        feats = feats + feats2 if self.res1 else feats2
        feats = self.norm1(feats) if self.norm1 is not None else feats

        if self.mlp:
            feats2 = self.linear2(self.dropout(self.act(self.linear1(feats))))
        else:
            feats2 = feats

        feats2 = self.dropout2(feats2)
        feats = feats + feats2 if self.res2 else feats2
        feats = self.norm2(feats) if self.norm2 is not None else feats

        return feats, egde_index, edge_attr


