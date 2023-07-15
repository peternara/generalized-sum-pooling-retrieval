import torch
from .. import net
import torch.nn as nn
from .utils import weights_init_kaiming, weights_init_classifier

def load_net(dataset, nb_classes, mode, net_type, sz_embedding=512,
             last_stride=0, neck=0, pretrained_path='no', red=1, emb_head='gp'):
    if net_type == 'bn_inception':
        sz_embed = 1024
        model = net.bn_inception(pretrained=True)
        #model.last_linear = nn.Linear(1024, nb_classes)

        model = net.Inception_embed(model, 1024, sz_embedding, num_classes=nb_classes, neck=neck,
                                    emb_head=emb_head)
        sz_embed = sz_embedding

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path), strict=False)
            
    elif net_type == 'resnet18':
        red = 1
        sz_embed = int(512/red)
        model = net.resnet18(pretrained=True, last_stride=last_stride, neck=neck, red=1)
        dim = int(512/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.fc = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.fc.apply(weights_init_classifier)
        else:
            model.fc = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'resnet34':
        red = 1
        sz_embed = int(512/red)
        model = net.resnet34(pretrained=True, last_stride=last_stride, neck=neck, red=1)
        dim = int(512/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.fc = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.fc.apply(weights_init_classifier)
        else:
            model.fc = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'resnet50':
        sz_embed = int(2048/red)
        model = net.resnet50(pretrained=True, last_stride=last_stride, neck=neck, red=red, num_classes=nb_classes,
                             emb_head=emb_head)

        dim = int(2048/red)
        '''if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.fc = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.fc.apply(weights_init_classifier)
        else: 
            model.fc = nn.Linear(dim, nb_classes)'''

        if pretrained_path != 'no':
            if not torch.cuda.is_available(): 
                model.load_state_dict(torch.load(pretrained_path, map_location=torch.device('cpu')),
                                      strict=False)
            else:
                model.load_state_dict(torch.load(pretrained_path), strict=False)

    elif net_type == 'resnet101':
        sz_embed = int(2048/red)
        model = net.resnet101(pretrained=True, last_stride=last_stride, neck=neck, red=red)

        dim = int(2048/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.fc = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.fc.apply(weights_init_classifier)
        else:
            model.fc = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'resnet152':
        sz_embed = int(2048/red)
        model = net.resnet152(pretrained=True, last_stride=last_stride, neck=neck, red=red)
        dim = int(2048/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.fc = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.fc.apply(weights_init_classifier)
        else:
            model.fc = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'densenet121':
        sz_embed = int(1024/red)
        model = net.densenet121(pretrained=True, last_stride=last_stride, neck=neck, red=red)
        dim = int(1024/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.classifier = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.classifier.apply(weights_init_classifier)
        else:
            model.classifier = nn.Linear(dim, nb_classes)
        
        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'densenet161':
        sz_embed = int(2208/red)
        model = net.densenet161(pretrained=True, last_stride=last_stride, neck=neck, red=red)
        dim = int(2208/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.classifier = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.classifier.apply(weights_init_classifier)
        else:
            model.classifier = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'densenet169':
        sz_embed = int(1664/red)
        model = net.densenet169(pretrained=True, last_stride=last_stride, neck=neck, red=red)
        dim = int(1664/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.classifier = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.classifier.apply(weights_init_classifier)
        else:
            model.classifier = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    elif net_type == 'densenet201':
        sz_embed = int(1920)
        model = net.densenet201(pretrained=True, last_stride=last_stride, neck=neck, red=red)
        dim = int(1920/red)
        if neck:
            model.bottleneck = nn.BatchNorm1d(dim)
            model.bottleneck.bias.requires_grad_(False)  # no shift
            model.classifier = nn.Linear(dim, nb_classes, bias=False)

            model.bottleneck.apply(weights_init_kaiming)
            model.classifier.apply(weights_init_classifier)
        else:
            model.classifier = nn.Linear(dim, nb_classes)

        if pretrained_path != 'no':
            model.load_state_dict(torch.load(pretrained_path))

    return model, sz_embed


