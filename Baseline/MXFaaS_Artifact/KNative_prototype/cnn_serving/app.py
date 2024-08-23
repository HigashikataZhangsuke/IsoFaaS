import torch
from torchvision import models, transforms
from PIL import Image
import os
import json
import time
torch.set_num_threads(1)

# 限制 MKL 和 OpenMP 使用的线程数
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
def lambda_handler():
    torch.set_num_threads(1)

    # 限制 MKL 和 OpenMP 使用的线程数
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    model = models.resnet50(pretrained=True)
    model.eval()  # 设置为评估模式
    # 下载ImageNet标签文件
    labels_url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
    labels_path = 'imagenet_labels.json'
    if not os.path.exists(labels_path):
        import urllib.request
        urllib.request.urlretrieve(labels_url, labels_path)
    with open(labels_path, 'r') as f:
        labels = json.load(f)
    input_dir = './Res/'  # 修改为包含图片的目录路径
    image_list = os.listdir(input_dir)
    generation_count = 1
    total_time = 0.0
    for i in range(generation_count):
        input_image_name = image_list[i % len(image_list)]
        image_path = os.path.join(input_dir, input_image_name)
        start_time = time.time()
        # 定义图像预处理过程
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        # 读取并处理图像
        image = Image.open(image_path)
        img_tensor = preprocess(image)
        img_tensor = img_tensor.unsqueeze(0)  # 批量化
        # 进行推断
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            top5_prob, top5_catid = torch.topk(probabilities, 5)
        inference = ''
        for j in range(top5_prob.size(0)):
            inference += 'With prob = %.5f, it contains %s. ' % (top5_prob[j].item(), labels[top5_catid[j].item()])
        exec_time = time.time() - start_time
        total_time += exec_time
    average_time = total_time / generation_count
    return {"result": inference, "average_execution_time": average_time}

