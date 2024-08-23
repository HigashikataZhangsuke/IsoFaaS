import os
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
import logging
import random
import redis
import time
import multiprocessing
import json
import threading
import torch
from torchvision import models, transforms
from PIL import Image
import subprocess
#Class
import torch
import torch.nn as nn
import torch.nn.functional as F
torch.set_num_threads(1)


class Bottleneck(nn.Module):
    expansion = 4

    def __init__(self, in_channels, out_channels, stride=1, downsample=None, mid_kernel_size=7):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)  # 保持1x1
        self.bn1 = nn.BatchNorm2d(out_channels)
        # 修改这里的 kernel size 为可配置
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=mid_kernel_size, stride=stride, padding=mid_kernel_size//2, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.conv3 = nn.Conv2d(out_channels, out_channels * self.expansion, kernel_size=1, bias=False)  # 保持1x1
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
    def __init__(self, num_classes=1000, conv1_kernel_size=20):
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
        
def MLserve():
    torch.set_num_threads(1)
    # 限制 MKL 和 OpenMP 使用的线程数
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    resnet152 = torch.load('resnet152_full_model.pth',weights_only=False)
    #resnet152.eval()
    resnet152.load_state_dict(torch.load('./resnet152_modified_weights.pth',weights_only=False))
    resnet152.eval()
    # 下载ImageNet标签文件
    labels_url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
    labels_path = 'imagenet_labels.json'
    if not os.path.exists(labels_path):
        import urllib.request
        urllib.request.urlretrieve(labels_url, labels_path)
    with open(labels_path, 'r') as f:
        labels = json.load(f)
    input_dir = './ROT/'  #./ResRes/
    image_list = os.listdir(input_dir)
    generation_count =5
    total_time = 0.0
    for i in range(generation_count):
        #input_image_name = random.choice(image_list)
        #image_path = os.path.join(input_dir, input_image_name)
        input_image_path ='./ROT/large_image_'+str(i+30)+'.png'
        start_time = time.time()
        # 定义图像预处理过程(Resize and filter, make it to be a mem bound)
        preprocess = transforms.Compose([
            transforms.Resize(512),
            transforms.CenterCrop(224),
            #transforms.ColorJitter(),  # 添加色彩变换
            #transforms.GaussianBlur(5),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        # 读取并处理图像
        image = Image.open(input_image_path)
        img_tensor = preprocess(image)
        img_tensor = img_tensor.unsqueeze(0)  # 批量化
        # 进行推断
        with torch.no_grad():
            outputs = resnet152(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            top5_prob, top5_catid = torch.topk(probabilities, 5)
        inference = ''
        for j in range(top5_prob.size(0)):
            inference += 'With prob = %.5f, it contains %s. ' % (top5_prob[j].item(), labels[top5_catid[j].item()])
        exec_time = time.time() - start_time
        total_time += exec_time
    average_time = total_time / generation_count
    return {"result": inference, "average_execution_time": average_time}


def measure_throughput(duration_seconds):
    start_time = time.time()
    end_time = start_time + duration_seconds
    iterations = 0

    while time.time() < end_time:
        result = MLserve()  # Adjust as needed
        iterations += 5
    return iterations

def run_test():
    duration_seconds = 20  # Duration for each process
    for cpu_count in [1,12,19,20,21,22]:
    #1,4,8,12,16,
    #cpu_count = 4  # Number of CPUs to use
        #for i in range(3):
        st = time.time()
        with multiprocessing.Pool(cpu_count) as pool:
            results = pool.map(measure_throughput, [duration_seconds] * cpu_count)
        et = time.time()
        total_iterations = sum(results)
        print(f"Total iterations across all CPUs in {duration_seconds} seconds: {total_iterations/(et-st)} with {cpu_count}")
        time.sleep(5)

if __name__ == "__main__":
    #os.sched_setaffinity(0, {6})
    #while True:
    #    st = time.time()
    #    results = MLserve()
    #    et = time.time()
    #    print(et-st,flush=True)
    run_test()
    #os.sched_setaffinity(0, {6})
    #st = time.time()
    #results = MLserve()
    #et = time.time()
    #print(et-st,flush=True)

