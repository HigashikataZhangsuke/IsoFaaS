import os
import time
import torch
from torchvision import models, transforms
from PIL import Image
import json
import os

# Set CPU affinity to CPU 6
os.sched_setaffinity(0, {6})  # The first argument 0 applies the affinity to the current process

def alu(model,labels_path):
    
    model.eval()  # Set the model to evaluation mode

    # Download ImageNet labels if not already present
    
    
    with open(labels_path, 'r') as f:
        labels = json.load(f)

    input_dir = '/home/ubuntu/IsoFaaS/Profiling/Res/'  # Update this to your image directory path
    image_list = os.listdir(input_dir)
    generation_count = 1
    total_time = 0.0

    for i in range(generation_count):
        input_image_name = image_list[i % len(image_list)]
        image_path = os.path.join(input_dir, input_image_name)
        start_time = time.time()

        # Define image preprocessing
        preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Read and process the image
        image = Image.open(image_path)
        img_tensor = preprocess(image)
        img_tensor = img_tensor.unsqueeze(0)  # Batchify the image

        # Perform inference
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

model = models.resnet50(pretrained=True)
labels_url = 'https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json'
labels_path = 'imagenet_labels.json'
if not os.path.exists(labels_path):
    import urllib.request
    urllib.request.urlretrieve(labels_url, labels_path)

print("Now ready for BW Tests")
while True:
    alu(model,labels_path)
