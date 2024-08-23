# import torch
# import torch.nn as nn
# import torchvision.models as models
#
# def modify_first_two_conv_layers(model, new_size1=100, new_size2=3):
#     # ?????????
#     first_conv_layer = model.conv1
#     in_channels = first_conv_layer.in_channels
#     out_channels = first_conv_layer.out_channels
#     stride = first_conv_layer.stride
#     padding = (new_size1 - 1) // 2  # Calculate padding to maintain the output size
#     new_conv1 = nn.Conv2d(in_channels, out_channels, new_size1, stride, padding)
#     model.conv1 = new_conv1
#
#     # ???????????????
#     first_block = model.layer1[0]  # ??????
#     block_first_conv_layer = first_block.conv1
#     block_in_channels = block_first_conv_layer.in_channels
#     block_out_channels = block_first_conv_layer.out_channels
#     block_stride = block_first_conv_layer.stride
#     block_padding = (new_size2 - 1) // 2  # Calculate padding to maintain the output size
#     new_block_conv1 = nn.Conv2d(block_in_channels, block_out_channels, new_size2, block_stride, block_padding)
#     first_block.conv1 = new_block_conv1
#
# # ??? ResNet152 ????????
# resnet152 = models.resnet152(pretrained=True)
#
# # ???????????
# modify_first_two_conv_layers(resnet152, new_size1=40, new_size2=40)
#
# # ????????
# def init_weights(m):
#     if isinstance(m, nn.Conv2d):
#         nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
#         if m.bias is not None:
#             nn.init.constant_(m.bias, 0)
#     elif isinstance(m, nn.Linear):
#         nn.init.normal_(m.weight, 0, 0.01)
#         nn.init.constant_(m.bias, 0)
#
# resnet152.apply(init_weights)
#
# # ???????????????
# torch.save(resnet152.state_dict(), 'resnet152_modified_weights.pth')
# torch.save(resnet152, 'resnet152_full_model.pth')
import torch
import torch.nn as nn
import torch.nn.functional as F

class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, in_channels, out_channels, stride=1, downsample=None, mid_kernel_size=7):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)  # ??1x1
        self.bn1 = nn.BatchNorm2d(out_channels)
        # ????? kernel size ????
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=mid_kernel_size, stride=stride, padding=mid_kernel_size//2, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.conv3 = nn.Conv2d(out_channels, out_channels * self.expansion, kernel_size=1, bias=False)  # ??1x1
        self.bn3 = nn.BatchNorm2d(out_channels * self.expansion)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        #if self.downsample is not None:
        #    identity = self.downsample(x)

        #out += identity
        out = self.relu(out)
        return out

class ResNet152(nn.Module):
    def __init__(self, num_classes=1000, conv1_kernel_size=10):
        super(ResNet152, self).__init__()
        self.in_channels = 64  # Initialize in_channels before it's used
        self.conv1 = nn.Conv2d(3, 64, kernel_size=conv1_kernel_size, stride=2, padding=conv1_kernel_size//2, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=conv1_kernel_size//2, stride=2, padding=conv1_kernel_size//4)
        
        self.layer1 = self.make_layer(Bottleneck, 64, 3)
        self.layer2 = self.make_layer(Bottleneck, 128, 8, stride=2)
        self.layer3 = self.make_layer(Bottleneck, 256, 36, stride=2)
        self.layer4 = self.make_layer(Bottleneck, 512, 3, stride=2)
        
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512 * Bottleneck.expansion, num_classes)

    def make_layer(self, block, out_channels, blocks, stride=1, mid_kernel_size=7):
        downsample = None
        if stride != 1 or self.in_channels != out_channels * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.in_channels, out_channels * block.expansion, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels * block.expansion),
            )

        layers = []
        layers.append(block(self.in_channels, out_channels, stride, downsample))
        self.in_channels = out_channels * block.expansion
        for _ in range(1, blocks):
            layers.append(block(self.in_channels, out_channels))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)

        return x



# ??????
model = ResNet152(num_classes=1000)


# ???????
def init_weights(m):
    if isinstance(m, nn.Conv2d):
        nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
        if m.bias is not None:
            nn.init.constant_(m.bias, 0)
    elif isinstance(m, nn.Linear):
        nn.init.normal_(m.weight, 0, 0.01)
        nn.init.constant_(m.bias, 0)


model.apply(init_weights)

# ??????
torch.save(model.state_dict(), 'resnet152_modified_weights.pth')
# ??????
torch.save(model, 'resnet152_full_model.pth')
