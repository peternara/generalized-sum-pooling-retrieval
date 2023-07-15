import torch
import torch.nn as nn
import torch.utils.model_zoo as model_zoo
import torch.nn.functional as F
from .utils import weights_init_kaiming, weights_init_classifier

from .embedding_heads import LinearNorm
from .gsp import GSP

__all__ = ['BNInception', 'bn_inception']

"""
Inception v2 was ported from Caffee to pytorch 0.2, see 
https://github.com/Cadene/pretrained-models.pytorch. I've ported it to 
PyTorch 0.4 for the Proxy-NCA implementation, see 
https://github.com/dichotomies/proxy-nca.
"""

def bn_inception(pretrained=False, **kwargs):
    model = BNInception(**kwargs)
    if pretrained:
        model.load_state_dict(torch.load('net/bn_inception_weights_pt04.pt'))
    else:
        weight = model_zoo.load_url('http://data.lip6.fr/cadene/pretrainedmodels/bn_inception-52deb4733.pth')
        weight = {k: v.squeeze(0) if v.size(0) == 1 else v for k, v in weight.items()}
        model.load_state_dict(weight)
    return model

class BNInception(nn.Module):

    def __init__(self, nb_classes=1000, is_pretrained=True):
        # super(self).__init__()
        nn.Module.__init__(self)
        inplace = True
        self.conv1_7x7_s2 = nn.Conv2d(
            3, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3)
        )
        self.conv1_7x7_s2_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.conv1_relu_7x7 = nn.ReLU(inplace)
        self.pool1_3x3_s2 = nn.MaxPool2d(
            (3, 3), stride=(2, 2), dilation=(1, 1), ceil_mode=True
        )
        self.conv2_3x3_reduce = nn.Conv2d(
            64, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.conv2_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.conv2_relu_3x3_reduce = nn.ReLU(
            inplace
        )
        self.conv2_3x3 = nn.Conv2d(
            64, 192, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.conv2_3x3_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.conv2_relu_3x3 = nn.ReLU(inplace)
        self.pool2_3x3_s2 = nn.MaxPool2d(
            (3, 3), stride=(2, 2), dilation=(1, 1), ceil_mode=True
        )
        self.inception_3a_1x1 = nn.Conv2d(
            192, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3a_1x1_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_1x1 = nn.ReLU(inplace)
        self.inception_3a_3x3_reduce = nn.Conv2d(
            192, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3a_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_3x3_reduce = nn.ReLU (inplace)
        self.inception_3a_3x3 = nn.Conv2d(
            64, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3a_3x3_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_3x3 = nn.ReLU(inplace)
        self.inception_3a_double_3x3_reduce = nn.Conv2d(
            192, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3a_double_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_3a_double_3x3_1 = nn.Conv2d(
            64, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3a_double_3x3_1_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_3a_double_3x3_2 = nn.Conv2d(
            96, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3a_double_3x3_2_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_3a_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_3a_pool_proj = nn.Conv2d(
            192, 32, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3a_pool_proj_bn = nn.BatchNorm2d(
            32, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3a_relu_pool_proj = nn.ReLU(inplace)
        self.inception_3b_1x1 = nn.Conv2d(
            256, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3b_1x1_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_1x1 = nn.ReLU(inplace)
        self.inception_3b_3x3_reduce = nn.Conv2d(
            256, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3b_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_3b_3x3 = nn.Conv2d(
            64, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3b_3x3_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_3x3 = nn.ReLU(inplace)
        self.inception_3b_double_3x3_reduce = nn.Conv2d(
            256, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3b_double_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_3b_double_3x3_1 = nn.Conv2d(
            64, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3b_double_3x3_1_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_3b_double_3x3_2 = nn.Conv2d(
            96, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3b_double_3x3_2_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_3b_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_3b_pool_proj = nn.Conv2d(
            256, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3b_pool_proj_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3b_relu_pool_proj = nn.ReLU(inplace)
        self.inception_3c_3x3_reduce = nn.Conv2d(
            320, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3c_3x3_reduce_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3c_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_3c_3x3 = nn.Conv2d(
            128, 160, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)
        )
        self.inception_3c_3x3_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3c_relu_3x3 = nn.ReLU(inplace)
        self.inception_3c_double_3x3_reduce = nn.Conv2d(
            320, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_3c_double_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3c_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_3c_double_3x3_1 = nn.Conv2d(
            64, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_3c_double_3x3_1_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3c_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_3c_double_3x3_2 = nn.Conv2d(
            96, 96, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)
        )
        self.inception_3c_double_3x3_2_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_3c_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_3c_pool = nn.MaxPool2d(
            (3, 3), stride=(2, 2), dilation=(1, 1), ceil_mode=True
        )
        self.inception_4a_1x1 = nn.Conv2d(
            576, 224, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4a_1x1_bn = nn.BatchNorm2d(
            224, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_1x1 = nn.ReLU(inplace)
        self.inception_4a_3x3_reduce = nn.Conv2d(
            576, 64, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4a_3x3_reduce_bn = nn.BatchNorm2d(
            64, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_4a_3x3 = nn.Conv2d(
            64, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4a_3x3_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_3x3 = nn.ReLU(inplace)
        self.inception_4a_double_3x3_reduce = nn.Conv2d(
            576, 96, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4a_double_3x3_reduce_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_4a_double_3x3_1 = nn.Conv2d(
            96, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4a_double_3x3_1_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_4a_double_3x3_2 = nn.Conv2d(
            128, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4a_double_3x3_2_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_4a_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_4a_pool_proj = nn.Conv2d(
            576, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4a_pool_proj_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4a_relu_pool_proj = nn.ReLU(inplace)
        self.inception_4b_1x1 = nn.Conv2d(
            576, 192, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4b_1x1_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_1x1 = nn.ReLU(inplace)
        self.inception_4b_3x3_reduce = nn.Conv2d(
            576, 96, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4b_3x3_reduce_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_4b_3x3 = nn.Conv2d(
            96, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4b_3x3_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_3x3 = nn.ReLU(inplace)
        self.inception_4b_double_3x3_reduce = nn.Conv2d(
            576, 96, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4b_double_3x3_reduce_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_4b_double_3x3_1 = nn.Conv2d(
            96, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4b_double_3x3_1_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_4b_double_3x3_2 = nn.Conv2d(
            128, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4b_double_3x3_2_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_4b_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_4b_pool_proj = nn.Conv2d(
            576, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4b_pool_proj_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4b_relu_pool_proj = nn.ReLU(inplace)
        self.inception_4c_1x1 = nn.Conv2d(
            576, 160, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4c_1x1_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_1x1 = nn.ReLU(inplace)
        self.inception_4c_3x3_reduce = nn.Conv2d(
            576, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4c_3x3_reduce_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_4c_3x3 = nn.Conv2d(
            128, 160, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4c_3x3_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_3x3 = nn.ReLU(inplace)
        self.inception_4c_double_3x3_reduce = nn.Conv2d(
            576, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4c_double_3x3_reduce_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_4c_double_3x3_1 = nn.Conv2d(
            128, 160, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4c_double_3x3_1_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_4c_double_3x3_2 = nn.Conv2d(
            160, 160, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4c_double_3x3_2_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_4c_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_4c_pool_proj = nn.Conv2d(
            576, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4c_pool_proj_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4c_relu_pool_proj = nn.ReLU(inplace)
        self.inception_4d_1x1 = nn.Conv2d(
            608, 96, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4d_1x1_bn = nn.BatchNorm2d(
            96, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_1x1 = nn.ReLU(inplace)
        self.inception_4d_3x3_reduce = nn.Conv2d(
            608, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4d_3x3_reduce_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_4d_3x3 = nn.Conv2d(
            128, 192, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4d_3x3_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_3x3 = nn.ReLU (inplace)
        self.inception_4d_double_3x3_reduce = nn.Conv2d(
            608, 160, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4d_double_3x3_reduce_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_double_3x3_reduce = nn.ReLU (inplace)
        self.inception_4d_double_3x3_1 = nn.Conv2d(
            160, 192, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4d_double_3x3_1_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_4d_double_3x3_2 = nn.Conv2d(
            192, 192, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4d_double_3x3_2_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_4d_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_4d_pool_proj = nn.Conv2d(
            608, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4d_pool_proj_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4d_relu_pool_proj = nn.ReLU(inplace)
        self.inception_4e_3x3_reduce = nn.Conv2d(
            608, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4e_3x3_reduce_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4e_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_4e_3x3 = nn.Conv2d(
            128, 192, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)
        )
        self.inception_4e_3x3_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4e_relu_3x3 = nn.ReLU(inplace)
        self.inception_4e_double_3x3_reduce = nn.Conv2d(
            608, 192, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_4e_double_3x3_reduce_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4e_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_4e_double_3x3_1 = nn.Conv2d(
            192, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_4e_double_3x3_1_bn = nn.BatchNorm2d(
            256, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4e_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_4e_double_3x3_2 = nn.Conv2d(
            256, 256, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)
        )
        self.inception_4e_double_3x3_2_bn = nn.BatchNorm2d(
            256, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_4e_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_4e_pool = nn.MaxPool2d(
            (3, 3), stride=(2, 2), dilation=(1, 1), ceil_mode=True
        )
        self.inception_5a_1x1 = nn.Conv2d(
            1056, 352, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5a_1x1_bn = nn.BatchNorm2d(
            352, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_1x1 = nn.ReLU(inplace)
        self.inception_5a_3x3_reduce = nn.Conv2d(
            1056, 192, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5a_3x3_reduce_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_5a_3x3 = nn.Conv2d(
            192, 320, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_5a_3x3_bn = nn.BatchNorm2d(
            320, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_3x3 = nn.ReLU(inplace)
        self.inception_5a_double_3x3_reduce = nn.Conv2d(
            1056, 160, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5a_double_3x3_reduce_bn = nn.BatchNorm2d(
            160, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_5a_double_3x3_1 = nn.Conv2d(
            160, 224, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_5a_double_3x3_1_bn = nn.BatchNorm2d(
            224, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_5a_double_3x3_2 = nn.Conv2d(
            224, 224, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_5a_double_3x3_2_bn = nn.BatchNorm2d(
            224, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_5a_pool = nn.AvgPool2d(
            3, stride=1, padding=1, ceil_mode=True, count_include_pad=True
        )
        self.inception_5a_pool_proj = nn.Conv2d(
            1056, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5a_pool_proj_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5a_relu_pool_proj = nn.ReLU(inplace)
        self.inception_5b_1x1 = nn.Conv2d(
            1024, 352, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5b_1x1_bn = nn.BatchNorm2d(
            352, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_1x1 = nn.ReLU(inplace)
        self.inception_5b_3x3_reduce = nn.Conv2d(
            1024, 192, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5b_3x3_reduce_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_3x3_reduce = nn.ReLU(inplace)
        self.inception_5b_3x3 = nn.Conv2d(
            192, 320, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_5b_3x3_bn = nn.BatchNorm2d(
            320, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_3x3 = nn.ReLU(inplace)
        self.inception_5b_double_3x3_reduce = nn.Conv2d(
            1024, 192, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5b_double_3x3_reduce_bn = nn.BatchNorm2d(
            192, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_double_3x3_reduce = nn.ReLU(inplace)
        self.inception_5b_double_3x3_1 = nn.Conv2d(
            192, 224, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_5b_double_3x3_1_bn = nn.BatchNorm2d(
            224, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_double_3x3_1 = nn.ReLU(inplace)
        self.inception_5b_double_3x3_2 = nn.Conv2d(
            224, 224, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)
        )
        self.inception_5b_double_3x3_2_bn = nn.BatchNorm2d(
            224, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_double_3x3_2 = nn.ReLU(inplace)
        self.inception_5b_pool = nn.MaxPool2d(
            (3, 3), stride=(1, 1), padding=(1, 1), dilation=(1, 1), 
            ceil_mode=True
        )
        self.inception_5b_pool_proj = nn.Conv2d(
            1024, 128, kernel_size=(1, 1), stride=(1, 1)
        )
        self.inception_5b_pool_proj_bn = nn.BatchNorm2d(
            128, eps=1e-05, momentum=0.9, affine=True
        )
        self.inception_5b_relu_pool_proj = nn.ReLU(inplace)
        self.avg_pool = nn.AvgPool2d(
            7, stride=1, padding=0, ceil_mode=True, count_include_pad=True
        )

        self.max_pool = nn.MaxPool2d(
            7, stride=1, padding=0, ceil_mode=True
        )

        self.last_linear = nn.Linear(1024, nb_classes)

    def features(self, input):
        conv1_7x7_s2_out = self.conv1_7x7_s2(input)
        conv1_7x7_s2_bn_out = self.conv1_7x7_s2_bn(conv1_7x7_s2_out)
        conv1_relu_7x7_out = self.conv1_relu_7x7(conv1_7x7_s2_bn_out)
        pool1_3x3_s2_out = self.pool1_3x3_s2(conv1_7x7_s2_bn_out)
        conv2_3x3_reduce_out = self.conv2_3x3_reduce(pool1_3x3_s2_out)
        conv2_3x3_reduce_bn_out = \
                self.conv2_3x3_reduce_bn(conv2_3x3_reduce_out)
        conv2_relu_3x3_reduce_out = \
                self.conv2_relu_3x3_reduce(conv2_3x3_reduce_bn_out)
        conv2_3x3_out = self.conv2_3x3(conv2_3x3_reduce_bn_out)
        conv2_3x3_bn_out = self.conv2_3x3_bn(conv2_3x3_out)
        conv2_relu_3x3_out = self.conv2_relu_3x3(conv2_3x3_bn_out)
        pool2_3x3_s2_out = self.pool2_3x3_s2(conv2_3x3_bn_out)
        inception_3a_1x1_out = self.inception_3a_1x1(pool2_3x3_s2_out)
        inception_3a_1x1_bn_out = \
                self.inception_3a_1x1_bn(inception_3a_1x1_out)
        inception_3a_relu_1x1_out = \
                self.inception_3a_relu_1x1(inception_3a_1x1_bn_out)
        inception_3a_3x3_reduce_out = \
                self.inception_3a_3x3_reduce(pool2_3x3_s2_out)
        inception_3a_3x3_reduce_bn_out = \
                self.inception_3a_3x3_reduce_bn(inception_3a_3x3_reduce_out)
        inception_3a_relu_3x3_reduce_out = \
                self.inception_3a_relu_3x3_reduce(
                    inception_3a_3x3_reduce_bn_out
                )
        inception_3a_3x3_out = \
                self.inception_3a_3x3(inception_3a_3x3_reduce_bn_out)
        inception_3a_3x3_bn_out = \
                self.inception_3a_3x3_bn(inception_3a_3x3_out)
        inception_3a_relu_3x3_out = \
                self.inception_3a_relu_3x3(inception_3a_3x3_bn_out)
        inception_3a_double_3x3_reduce_out = \
                self.inception_3a_double_3x3_reduce(pool2_3x3_s2_out)
        inception_3a_double_3x3_reduce_bn_out = \
                self.inception_3a_double_3x3_reduce_bn(
                    inception_3a_double_3x3_reduce_out
                )
        inception_3a_relu_double_3x3_reduce_out = \
                self.inception_3a_relu_double_3x3_reduce(
                    inception_3a_double_3x3_reduce_bn_out
                )
        inception_3a_double_3x3_1_out = self.inception_3a_double_3x3_1(
            inception_3a_double_3x3_reduce_bn_out
        )
        inception_3a_double_3x3_1_bn_out = self.inception_3a_double_3x3_1_bn(
            inception_3a_double_3x3_1_out
        )
        inception_3a_relu_double_3x3_1_out = \
                self.inception_3a_relu_double_3x3_1(
                    inception_3a_double_3x3_1_bn_out
                )
        inception_3a_double_3x3_2_out = self.inception_3a_double_3x3_2(
            inception_3a_double_3x3_1_bn_out
        )
        inception_3a_double_3x3_2_bn_out = self.inception_3a_double_3x3_2_bn(
            inception_3a_double_3x3_2_out
        )
        inception_3a_relu_double_3x3_2_out = \
                self.inception_3a_relu_double_3x3_2(
                    inception_3a_double_3x3_2_bn_out
                )
        inception_3a_pool_out = self.inception_3a_pool(pool2_3x3_s2_out)
        inception_3a_pool_proj_out = \
                self.inception_3a_pool_proj(inception_3a_pool_out)
        inception_3a_pool_proj_bn_out = \
                self.inception_3a_pool_proj_bn(inception_3a_pool_proj_out)
        inception_3a_relu_pool_proj_out = \
                self.inception_3a_relu_pool_proj(
                    inception_3a_pool_proj_bn_out
                )
        inception_3a_output_out = \
                torch.cat(
                    [
                        inception_3a_1x1_bn_out,
                        inception_3a_3x3_bn_out,
                        inception_3a_double_3x3_2_bn_out,
                        inception_3a_pool_proj_bn_out
                    ], 
                    1
                )
        inception_3b_1x1_out = self.inception_3b_1x1(inception_3a_output_out)
        inception_3b_1x1_bn_out = \
                self.inception_3b_1x1_bn(inception_3b_1x1_out)
        inception_3b_relu_1x1_out = \
                self.inception_3b_relu_1x1(inception_3b_1x1_bn_out)
        inception_3b_3x3_reduce_out = \
                self.inception_3b_3x3_reduce(inception_3a_output_out)
        inception_3b_3x3_reduce_bn_out = \
                self.inception_3b_3x3_reduce_bn(inception_3b_3x3_reduce_out)
        inception_3b_relu_3x3_reduce_out = \
                self.inception_3b_relu_3x3_reduce(
                    inception_3b_3x3_reduce_bn_out
                )
        inception_3b_3x3_out = \
                self.inception_3b_3x3(inception_3b_3x3_reduce_bn_out)
        inception_3b_3x3_bn_out = \
                self.inception_3b_3x3_bn(inception_3b_3x3_out)
        inception_3b_relu_3x3_out = \
                self.inception_3b_relu_3x3(inception_3b_3x3_bn_out)
        inception_3b_double_3x3_reduce_out = \
                self.inception_3b_double_3x3_reduce(inception_3a_output_out)
        inception_3b_double_3x3_reduce_bn_out = \
                self.inception_3b_double_3x3_reduce_bn(
                    inception_3b_double_3x3_reduce_out
                )
        inception_3b_relu_double_3x3_reduce_out = \
                self.inception_3b_relu_double_3x3_reduce(
                    inception_3b_double_3x3_reduce_bn_out
                )
        inception_3b_double_3x3_1_out = \
                self.inception_3b_double_3x3_1(
                    inception_3b_double_3x3_reduce_bn_out
                )
        inception_3b_double_3x3_1_bn_out = \
                self.inception_3b_double_3x3_1_bn(
                    inception_3b_double_3x3_1_out
                )
        inception_3b_relu_double_3x3_1_out = \
                self.inception_3b_relu_double_3x3_1(
                    inception_3b_double_3x3_1_bn_out
                )
        inception_3b_double_3x3_2_out = \
                self.inception_3b_double_3x3_2(
                    inception_3b_double_3x3_1_bn_out
                )
        inception_3b_double_3x3_2_bn_out = \
                self.inception_3b_double_3x3_2_bn(
                    inception_3b_double_3x3_2_out
                )
        inception_3b_relu_double_3x3_2_out = \
                self.inception_3b_relu_double_3x3_2(
                    inception_3b_double_3x3_2_bn_out
                )
        inception_3b_pool_out = \
                self.inception_3b_pool(inception_3a_output_out)
        inception_3b_pool_proj_out = \
                self.inception_3b_pool_proj(inception_3b_pool_out)
        inception_3b_pool_proj_bn_out = \
                self.inception_3b_pool_proj_bn(inception_3b_pool_proj_out)
        inception_3b_relu_pool_proj_out = \
                self.inception_3b_relu_pool_proj(
                    inception_3b_pool_proj_bn_out
                )
        inception_3b_output_out = \
                torch.cat(
                    [
                        inception_3b_1x1_bn_out,
                        inception_3b_3x3_bn_out,
                        inception_3b_double_3x3_2_bn_out,
                        inception_3b_pool_proj_bn_out
                    ], 
                    1
                )
        inception_3c_3x3_reduce_out = \
                self.inception_3c_3x3_reduce(inception_3b_output_out)
        inception_3c_3x3_reduce_bn_out = \
                self.inception_3c_3x3_reduce_bn(inception_3c_3x3_reduce_out)
        inception_3c_relu_3x3_reduce_out = \
                self.inception_3c_relu_3x3_reduce(
                    inception_3c_3x3_reduce_bn_out
                )
        inception_3c_3x3_out = \
                self.inception_3c_3x3(inception_3c_3x3_reduce_bn_out)
        inception_3c_3x3_bn_out = \
                self.inception_3c_3x3_bn(inception_3c_3x3_out)
        inception_3c_relu_3x3_out = \
                self.inception_3c_relu_3x3(inception_3c_3x3_bn_out)
        inception_3c_double_3x3_reduce_out = \
                self.inception_3c_double_3x3_reduce(inception_3b_output_out)
        inception_3c_double_3x3_reduce_bn_out = \
                self.inception_3c_double_3x3_reduce_bn(
                    inception_3c_double_3x3_reduce_out
                )
        inception_3c_relu_double_3x3_reduce_out = \
                self.inception_3c_relu_double_3x3_reduce(
                    inception_3c_double_3x3_reduce_bn_out
                )
        inception_3c_double_3x3_1_out = \
                self.inception_3c_double_3x3_1(
                    inception_3c_double_3x3_reduce_bn_out
                )
        inception_3c_double_3x3_1_bn_out = \
                self.inception_3c_double_3x3_1_bn(
                    inception_3c_double_3x3_1_out
                )
        inception_3c_relu_double_3x3_1_out = \
                self.inception_3c_relu_double_3x3_1(
                    inception_3c_double_3x3_1_bn_out
                )
        inception_3c_double_3x3_2_out = \
                self.inception_3c_double_3x3_2(
                    inception_3c_double_3x3_1_bn_out
                )
        inception_3c_double_3x3_2_bn_out = \
                self.inception_3c_double_3x3_2_bn(
                    inception_3c_double_3x3_2_out
                )
        inception_3c_relu_double_3x3_2_out = \
                self.inception_3c_relu_double_3x3_2(
                    inception_3c_double_3x3_2_bn_out
                )
        inception_3c_pool_out = self.inception_3c_pool(
            inception_3b_output_out
        )
        inception_3c_output_out = \
                torch.cat(
                    [
                        inception_3c_3x3_bn_out,
                        inception_3c_double_3x3_2_bn_out,
                        inception_3c_pool_out
                    ], 
                    1
                )
        inception_4a_1x1_out = self.inception_4a_1x1(inception_3c_output_out)
        inception_4a_1x1_bn_out = self.inception_4a_1x1_bn(
            inception_4a_1x1_out
        )
        inception_4a_relu_1x1_out = self.inception_4a_relu_1x1(
            inception_4a_1x1_bn_out
        )
        inception_4a_3x3_reduce_out = self.inception_4a_3x3_reduce(
            inception_3c_output_out
        )
        inception_4a_3x3_reduce_bn_out = self.inception_4a_3x3_reduce_bn(
            inception_4a_3x3_reduce_out
        )
        inception_4a_relu_3x3_reduce_out = self.inception_4a_relu_3x3_reduce(
            inception_4a_3x3_reduce_bn_out
        )
        inception_4a_3x3_out = self.inception_4a_3x3(
            inception_4a_3x3_reduce_bn_out
        )
        inception_4a_3x3_bn_out = self.inception_4a_3x3_bn(
            inception_4a_3x3_out
        )
        inception_4a_relu_3x3_out = self.inception_4a_relu_3x3(
            inception_4a_3x3_bn_out
        )
        inception_4a_double_3x3_reduce_out = \
                self.inception_4a_double_3x3_reduce(inception_3c_output_out)
        inception_4a_double_3x3_reduce_bn_out = \
                self.inception_4a_double_3x3_reduce_bn(
                    inception_4a_double_3x3_reduce_out
                )
        inception_4a_relu_double_3x3_reduce_out = \
                self.inception_4a_relu_double_3x3_reduce(
                    inception_4a_double_3x3_reduce_bn_out
                )
        inception_4a_double_3x3_1_out = self.inception_4a_double_3x3_1(
            inception_4a_double_3x3_reduce_bn_out
        )
        inception_4a_double_3x3_1_bn_out = self.inception_4a_double_3x3_1_bn(
            inception_4a_double_3x3_1_out
        )
        inception_4a_relu_double_3x3_1_out = \
                self.inception_4a_relu_double_3x3_1(
                    inception_4a_double_3x3_1_bn_out
                )
        inception_4a_double_3x3_2_out = self.inception_4a_double_3x3_2(
            inception_4a_double_3x3_1_bn_out
        )
        inception_4a_double_3x3_2_bn_out = self.inception_4a_double_3x3_2_bn(
            inception_4a_double_3x3_2_out
        )
        inception_4a_relu_double_3x3_2_out = \
                self.inception_4a_relu_double_3x3_2(
                    inception_4a_double_3x3_2_bn_out
                )
        inception_4a_pool_out = self.inception_4a_pool(
            inception_3c_output_out
        )
        inception_4a_pool_proj_out = self.inception_4a_pool_proj(
            inception_4a_pool_out
        )
        inception_4a_pool_proj_bn_out = self.inception_4a_pool_proj_bn(
            inception_4a_pool_proj_out
        )
        inception_4a_relu_pool_proj_out = self.inception_4a_relu_pool_proj(
            inception_4a_pool_proj_bn_out
        )
        inception_4a_output_out = torch.cat(
            [
                inception_4a_1x1_bn_out,
                inception_4a_3x3_bn_out,
                inception_4a_double_3x3_2_bn_out,
                inception_4a_pool_proj_bn_out
            ], 
            1
        )
        inception_4b_1x1_out = self.inception_4b_1x1(
            inception_4a_output_out
        )
        inception_4b_1x1_bn_out = self.inception_4b_1x1_bn(
            inception_4b_1x1_out
        )
        inception_4b_relu_1x1_out = self.inception_4b_relu_1x1(
            inception_4b_1x1_bn_out
        )
        inception_4b_3x3_reduce_out = self.inception_4b_3x3_reduce(
            inception_4a_output_out
        )
        inception_4b_3x3_reduce_bn_out = self.inception_4b_3x3_reduce_bn(
            inception_4b_3x3_reduce_out
        )
        inception_4b_relu_3x3_reduce_out = self.inception_4b_relu_3x3_reduce(
            inception_4b_3x3_reduce_bn_out
        )
        inception_4b_3x3_out = self.inception_4b_3x3(
            inception_4b_3x3_reduce_bn_out
        )
        inception_4b_3x3_bn_out = self.inception_4b_3x3_bn(
            inception_4b_3x3_out
        )
        inception_4b_relu_3x3_out = self.inception_4b_relu_3x3(
            inception_4b_3x3_bn_out
        )
        inception_4b_double_3x3_reduce_out = \
                self.inception_4b_double_3x3_reduce(inception_4a_output_out)
        inception_4b_double_3x3_reduce_bn_out = \
                self.inception_4b_double_3x3_reduce_bn(
                    inception_4b_double_3x3_reduce_out
                )
        inception_4b_relu_double_3x3_reduce_out = \
                self.inception_4b_relu_double_3x3_reduce(
                    inception_4b_double_3x3_reduce_bn_out
                )
        inception_4b_double_3x3_1_out = \
                self.inception_4b_double_3x3_1(
                    inception_4b_double_3x3_reduce_bn_out
                )
        inception_4b_double_3x3_1_bn_out = self.inception_4b_double_3x3_1_bn(
            inception_4b_double_3x3_1_out
        )
        inception_4b_relu_double_3x3_1_out = \
                self.inception_4b_relu_double_3x3_1(
                    inception_4b_double_3x3_1_bn_out
                )
        inception_4b_double_3x3_2_out = self.inception_4b_double_3x3_2(
            inception_4b_double_3x3_1_bn_out
        )
        inception_4b_double_3x3_2_bn_out = self.inception_4b_double_3x3_2_bn(
            inception_4b_double_3x3_2_out
        )
        inception_4b_relu_double_3x3_2_out = \
                self.inception_4b_relu_double_3x3_2(
                    inception_4b_double_3x3_2_bn_out
                )
        inception_4b_pool_out = self.inception_4b_pool(
            inception_4a_output_out
        )
        inception_4b_pool_proj_out = self.inception_4b_pool_proj(
            inception_4b_pool_out
        )
        inception_4b_pool_proj_bn_out = self.inception_4b_pool_proj_bn(
            inception_4b_pool_proj_out
        )
        inception_4b_relu_pool_proj_out = self.inception_4b_relu_pool_proj(
            inception_4b_pool_proj_bn_out
        )
        inception_4b_output_out = torch.cat(
            [
                inception_4b_1x1_bn_out,
                inception_4b_3x3_bn_out,
                inception_4b_double_3x3_2_bn_out,
                inception_4b_pool_proj_bn_out
            ], 
            1
        )
        inception_4c_1x1_out = self.inception_4c_1x1(
            inception_4b_output_out
        )
        inception_4c_1x1_bn_out = self.inception_4c_1x1_bn(
            inception_4c_1x1_out
        )
        inception_4c_relu_1x1_out = self.inception_4c_relu_1x1(
            inception_4c_1x1_bn_out
        )
        inception_4c_3x3_reduce_out = self.inception_4c_3x3_reduce(
            inception_4b_output_out
        )
        inception_4c_3x3_reduce_bn_out = self.inception_4c_3x3_reduce_bn(
            inception_4c_3x3_reduce_out
        )
        inception_4c_relu_3x3_reduce_out = \
                self.inception_4c_relu_3x3_reduce(
                    inception_4c_3x3_reduce_bn_out
                )
        inception_4c_3x3_out = self.inception_4c_3x3(
            inception_4c_3x3_reduce_bn_out
        )
        inception_4c_3x3_bn_out = self.inception_4c_3x3_bn(
            inception_4c_3x3_out
        )
        inception_4c_relu_3x3_out = self.inception_4c_relu_3x3(
            inception_4c_3x3_bn_out
        )
        inception_4c_double_3x3_reduce_out = \
                self.inception_4c_double_3x3_reduce(inception_4b_output_out)
        inception_4c_double_3x3_reduce_bn_out = \
                self.inception_4c_double_3x3_reduce_bn(
                    inception_4c_double_3x3_reduce_out
                )
        inception_4c_relu_double_3x3_reduce_out = \
                self.inception_4c_relu_double_3x3_reduce(
                    inception_4c_double_3x3_reduce_bn_out
                )
        inception_4c_double_3x3_1_out = self.inception_4c_double_3x3_1(
            inception_4c_double_3x3_reduce_bn_out
        )
        inception_4c_double_3x3_1_bn_out = self.inception_4c_double_3x3_1_bn(
            inception_4c_double_3x3_1_out
        )
        inception_4c_relu_double_3x3_1_out = \
                self.inception_4c_relu_double_3x3_1(
                    inception_4c_double_3x3_1_bn_out
                )
        inception_4c_double_3x3_2_out = self.inception_4c_double_3x3_2(
            inception_4c_double_3x3_1_bn_out
        )
        inception_4c_double_3x3_2_bn_out = self.inception_4c_double_3x3_2_bn(
            inception_4c_double_3x3_2_out
        )
        inception_4c_relu_double_3x3_2_out = \
                self.inception_4c_relu_double_3x3_2(
                    inception_4c_double_3x3_2_bn_out
                )
        inception_4c_pool_out = self.inception_4c_pool(
            inception_4b_output_out
        )
        inception_4c_pool_proj_out = self.inception_4c_pool_proj(
            inception_4c_pool_out
        )
        inception_4c_pool_proj_bn_out = self.inception_4c_pool_proj_bn(
            inception_4c_pool_proj_out
        )
        inception_4c_relu_pool_proj_out = self.inception_4c_relu_pool_proj(
            inception_4c_pool_proj_bn_out
        )
        inception_4c_output_out = torch.cat(
            [
                inception_4c_1x1_bn_out,
                inception_4c_3x3_bn_out,
                inception_4c_double_3x3_2_bn_out,
                inception_4c_pool_proj_bn_out
            ], 
            1)
        inception_4d_1x1_out = self.inception_4d_1x1(inception_4c_output_out)
        inception_4d_1x1_bn_out = self.inception_4d_1x1_bn(
            inception_4d_1x1_out
        )
        inception_4d_relu_1x1_out = self.inception_4d_relu_1x1(
            inception_4d_1x1_bn_out
        )
        inception_4d_3x3_reduce_out = self.inception_4d_3x3_reduce(
            inception_4c_output_out
        )
        inception_4d_3x3_reduce_bn_out = self.inception_4d_3x3_reduce_bn(
            inception_4d_3x3_reduce_out
        )
        inception_4d_relu_3x3_reduce_out = self.inception_4d_relu_3x3_reduce(
            inception_4d_3x3_reduce_bn_out
        )
        inception_4d_3x3_out = self.inception_4d_3x3(
            inception_4d_3x3_reduce_bn_out
        )
        inception_4d_3x3_bn_out = self.inception_4d_3x3_bn(
            inception_4d_3x3_out
        )
        inception_4d_relu_3x3_out = self.inception_4d_relu_3x3(
            inception_4d_3x3_bn_out
        )
        inception_4d_double_3x3_reduce_out = \
                self.inception_4d_double_3x3_reduce(inception_4c_output_out)
        inception_4d_double_3x3_reduce_bn_out = \
                self.inception_4d_double_3x3_reduce_bn(
                    inception_4d_double_3x3_reduce_out
                )
        inception_4d_relu_double_3x3_reduce_out = \
                self.inception_4d_relu_double_3x3_reduce(
                    inception_4d_double_3x3_reduce_bn_out
                )
        inception_4d_double_3x3_1_out = self.inception_4d_double_3x3_1(
            inception_4d_double_3x3_reduce_bn_out
        )
        inception_4d_double_3x3_1_bn_out = self.inception_4d_double_3x3_1_bn(
            inception_4d_double_3x3_1_out
        )
        inception_4d_relu_double_3x3_1_out = \
                self.inception_4d_relu_double_3x3_1(
                    inception_4d_double_3x3_1_bn_out
                )
        inception_4d_double_3x3_2_out = self.inception_4d_double_3x3_2(
            inception_4d_double_3x3_1_bn_out
        )
        inception_4d_double_3x3_2_bn_out = self.inception_4d_double_3x3_2_bn(
            inception_4d_double_3x3_2_out
        )
        inception_4d_relu_double_3x3_2_out = \
                self.inception_4d_relu_double_3x3_2(
                    inception_4d_double_3x3_2_bn_out
                )
        inception_4d_pool_out = self.inception_4d_pool(
            inception_4c_output_out
        )
        inception_4d_pool_proj_out = self.inception_4d_pool_proj(
            inception_4d_pool_out
        )
        inception_4d_pool_proj_bn_out = self.inception_4d_pool_proj_bn(
            inception_4d_pool_proj_out
        )
        inception_4d_relu_pool_proj_out = self.inception_4d_relu_pool_proj(
            inception_4d_pool_proj_bn_out
        )
        inception_4d_output_out = torch.cat(
            [
                inception_4d_1x1_bn_out,
                inception_4d_3x3_bn_out,
                inception_4d_double_3x3_2_bn_out,
                inception_4d_pool_proj_bn_out
            ], 
            1
        )
        inception_4e_3x3_reduce_out = self.inception_4e_3x3_reduce(
            inception_4d_output_out
        )
        inception_4e_3x3_reduce_bn_out = self.inception_4e_3x3_reduce_bn(
            inception_4e_3x3_reduce_out
        )
        inception_4e_relu_3x3_reduce_out = \
                self.inception_4e_relu_3x3_reduce(
                    inception_4e_3x3_reduce_bn_out
                )
        inception_4e_3x3_out = self.inception_4e_3x3(
            inception_4e_3x3_reduce_bn_out
        )
        inception_4e_3x3_bn_out = self.inception_4e_3x3_bn(
            inception_4e_3x3_out
        )
        inception_4e_relu_3x3_out = self.inception_4e_relu_3x3(
            inception_4e_3x3_bn_out
        )
        inception_4e_double_3x3_reduce_out = \
                self.inception_4e_double_3x3_reduce(inception_4d_output_out)
        inception_4e_double_3x3_reduce_bn_out = \
                self.inception_4e_double_3x3_reduce_bn(
                    inception_4e_double_3x3_reduce_out
                )
        inception_4e_relu_double_3x3_reduce_out = \
                self.inception_4e_relu_double_3x3_reduce(
                    inception_4e_double_3x3_reduce_bn_out
                )
        inception_4e_double_3x3_1_out = self.inception_4e_double_3x3_1(
            inception_4e_double_3x3_reduce_bn_out
        )
        inception_4e_double_3x3_1_bn_out = self.inception_4e_double_3x3_1_bn(
            inception_4e_double_3x3_1_out
        )
        inception_4e_relu_double_3x3_1_out = \
                self.inception_4e_relu_double_3x3_1(
                    inception_4e_double_3x3_1_bn_out
                )
        inception_4e_double_3x3_2_out = self.inception_4e_double_3x3_2(
            inception_4e_double_3x3_1_bn_out
        )
        inception_4e_double_3x3_2_bn_out = self.inception_4e_double_3x3_2_bn(
            inception_4e_double_3x3_2_out
        )
        inception_4e_relu_double_3x3_2_out = \
                self.inception_4e_relu_double_3x3_2(
                    inception_4e_double_3x3_2_bn_out
                )
        inception_4e_pool_out = self.inception_4e_pool(
            inception_4d_output_out
        )
        inception_4e_output_out = torch.cat(
            [
                inception_4e_3x3_bn_out,
                inception_4e_double_3x3_2_bn_out,
                inception_4e_pool_out
            ], 
            1
        )
        inception_5a_1x1_out = self.inception_5a_1x1(inception_4e_output_out)
        inception_5a_1x1_bn_out = self.inception_5a_1x1_bn(
            inception_5a_1x1_out
        )
        inception_5a_relu_1x1_out = self.inception_5a_relu_1x1(
            inception_5a_1x1_bn_out
        )
        inception_5a_3x3_reduce_out = self.inception_5a_3x3_reduce(
            inception_4e_output_out
        )
        inception_5a_3x3_reduce_bn_out = self.inception_5a_3x3_reduce_bn(
            inception_5a_3x3_reduce_out
        )
        inception_5a_relu_3x3_reduce_out = self.inception_5a_relu_3x3_reduce(
            inception_5a_3x3_reduce_bn_out
        )
        inception_5a_3x3_out = self.inception_5a_3x3(
            inception_5a_3x3_reduce_bn_out
        )
        inception_5a_3x3_bn_out = self.inception_5a_3x3_bn(
            inception_5a_3x3_out
        )
        inception_5a_relu_3x3_out = self.inception_5a_relu_3x3(
            inception_5a_3x3_bn_out
        )
        inception_5a_double_3x3_reduce_out = \
                self.inception_5a_double_3x3_reduce(inception_4e_output_out)
        inception_5a_double_3x3_reduce_bn_out = \
                self.inception_5a_double_3x3_reduce_bn(
                    inception_5a_double_3x3_reduce_out
                )
        inception_5a_relu_double_3x3_reduce_out = \
                self.inception_5a_relu_double_3x3_reduce(
                    inception_5a_double_3x3_reduce_bn_out
                )
        inception_5a_double_3x3_1_out = self.inception_5a_double_3x3_1(
            inception_5a_double_3x3_reduce_bn_out
        )
        inception_5a_double_3x3_1_bn_out = self.inception_5a_double_3x3_1_bn(
            inception_5a_double_3x3_1_out
        )
        inception_5a_relu_double_3x3_1_out = \
                self.inception_5a_relu_double_3x3_1(
                    inception_5a_double_3x3_1_bn_out
                )
        inception_5a_double_3x3_2_out = self.inception_5a_double_3x3_2(
            inception_5a_double_3x3_1_bn_out
        )
        inception_5a_double_3x3_2_bn_out = self.inception_5a_double_3x3_2_bn(
            inception_5a_double_3x3_2_out
        )
        inception_5a_relu_double_3x3_2_out = \
                self.inception_5a_relu_double_3x3_2(
                    inception_5a_double_3x3_2_bn_out
                )
        inception_5a_pool_out = self.inception_5a_pool(
            inception_4e_output_out
        )
        inception_5a_pool_proj_out = self.inception_5a_pool_proj(
            inception_5a_pool_out
        )
        inception_5a_pool_proj_bn_out = self.inception_5a_pool_proj_bn(
            inception_5a_pool_proj_out
        )
        inception_5a_relu_pool_proj_out = self.inception_5a_relu_pool_proj(
            inception_5a_pool_proj_bn_out
        )
        inception_5a_output_out = torch.cat(
            [
                inception_5a_1x1_bn_out,
                inception_5a_3x3_bn_out,
                inception_5a_double_3x3_2_bn_out,
                inception_5a_pool_proj_bn_out
            ], 
            1
        )
        inception_5b_1x1_out = self.inception_5b_1x1(inception_5a_output_out)
        inception_5b_1x1_bn_out = self.inception_5b_1x1_bn(
            inception_5b_1x1_out
        )
        inception_5b_relu_1x1_out = self.inception_5b_relu_1x1(
            inception_5b_1x1_bn_out
        )
        inception_5b_3x3_reduce_out = self.inception_5b_3x3_reduce(
            inception_5a_output_out
        )
        inception_5b_3x3_reduce_bn_out = self.inception_5b_3x3_reduce_bn(
            inception_5b_3x3_reduce_out
        )
        inception_5b_relu_3x3_reduce_out = self.inception_5b_relu_3x3_reduce(
            inception_5b_3x3_reduce_bn_out
        )
        inception_5b_3x3_out = self.inception_5b_3x3(
            inception_5b_3x3_reduce_bn_out
        )
        inception_5b_3x3_bn_out = self.inception_5b_3x3_bn(
            inception_5b_3x3_out
        )
        inception_5b_relu_3x3_out = self.inception_5b_relu_3x3(
            inception_5b_3x3_bn_out
        )
        inception_5b_double_3x3_reduce_out = \
                self.inception_5b_double_3x3_reduce(
                    inception_5a_output_out
                )
        inception_5b_double_3x3_reduce_bn_out = \
                self.inception_5b_double_3x3_reduce_bn(
                    inception_5b_double_3x3_reduce_out
                )
        inception_5b_relu_double_3x3_reduce_out = \
                self.inception_5b_relu_double_3x3_reduce(
                    inception_5b_double_3x3_reduce_bn_out
                )
        inception_5b_double_3x3_1_out = self.inception_5b_double_3x3_1(
            inception_5b_double_3x3_reduce_bn_out
        )
        inception_5b_double_3x3_1_bn_out = self.inception_5b_double_3x3_1_bn(
            inception_5b_double_3x3_1_out
        )
        inception_5b_relu_double_3x3_1_out = \
                self.inception_5b_relu_double_3x3_1(
                    inception_5b_double_3x3_1_bn_out
                )
        inception_5b_double_3x3_2_out = self.inception_5b_double_3x3_2(
            inception_5b_double_3x3_1_bn_out
        )
        inception_5b_double_3x3_2_bn_out = self.inception_5b_double_3x3_2_bn(
            inception_5b_double_3x3_2_out
        )
        inception_5b_relu_double_3x3_2_out = \
                self.inception_5b_relu_double_3x3_2(
                    inception_5b_double_3x3_2_bn_out
                )
        inception_5b_pool_out = self.inception_5b_pool(
            inception_5a_output_out
        )
        inception_5b_pool_proj_out = self.inception_5b_pool_proj(
            inception_5b_pool_out
        )
        inception_5b_pool_proj_bn_out = self.inception_5b_pool_proj_bn(
            inception_5b_pool_proj_out
        )
        inception_5b_relu_pool_proj_out = self.inception_5b_relu_pool_proj(
            inception_5b_pool_proj_bn_out
        )
        inception_5b_output_out = torch.cat(
            [
                inception_5b_1x1_bn_out,
                inception_5b_3x3_bn_out,
                inception_5b_double_3x3_2_bn_out,
                inception_5b_pool_proj_bn_out
            ], 
            1
        )
        return inception_5b_output_out
        # return inception_5b_output_out, inception_4e_output_out, inception_3c_output_out

    def logits(self, features):
        x = self.max_pool(features)
        fc7 = x.view(x.size(0), -1)
        x = self.last_linear(fc7)
        return x, fc7

    def forward(self, input, output_option='norm', val=False):
        x_h = self.features(input)
        #x_h, fc7_h = self.logits(x_h)

        return x_h#, fc7_h


class Inception_embed(nn.Module):
    def __init__(self, inception, inception_features_size, embed_features_size, num_classes, neck, emb_head='gp'):
        nn.Module.__init__(self)
        self.neck = neck
        self.inception = inception
        #self.embed = nn.Linear(inception_features_size, embed_features_size)
        self.embedding_head = \
            GSP(inception_features_size, embed_features_size, num_classes) if emb_head.lower() == 'gsp' \
                else LinearNorm(inception_features_size, embed_features_size, num_classes)

        print('\nINFO::MODEL::EMBEDDING: Using {} ...'.format(self.embedding_head.__class__.__name__))

        '''if self.neck:
            self.bottleneck = nn.BatchNorm1d(embed_features_size)
            self.bottleneck.bias.requires_grad_(False)  # no shift
            self.fc = nn.Linear(embed_features_size, num_classes,
                                bias=False)

            self.bottleneck.apply(weights_init_kaiming)
            self.fc.apply(weights_init_classifier)
        else:
            self.fc = nn.Linear(embed_features_size, num_classes)'''

    def forward(self, input, output_option='norm', val=False):
        #x, fc7 = self.inception(input)

        #embedding_features = self.embed(fc7)

        feat_map = self.inception(input)
        probs, embedding_features, attribute_probs = self.embedding_head(feat_map)

        return probs, embedding_features, attribute_probs

        '''if self.neck:
            feats_after = self.bottleneck(embedding_features)
        else:
            feats_after = embedding_features

        x = self.fc(feats_after)

        if output_option == 'norm':
            return x, embedding_features
        elif output_option == 'plain':
            return x, F.normalize(embedding_features, p=2, dim=1)
        elif output_option == 'neck' and self.neck:
            return x, feats_after
        elif output_option == 'neck' and not self.neck:
            print("Output option neck only avaiable if bottleneck (neck) is "
                  "enabeled - giving back x and fc7")
            return x, embedding_features'''


