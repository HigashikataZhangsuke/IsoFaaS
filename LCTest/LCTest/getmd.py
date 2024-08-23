# download_model.py
import torchvision.models as models
import torch

def download_vgg19():
    model = models.vgg19(pretrained=True)
    torch.save(model.state_dict(), './vgg19_pretrained.pth')
    print("VGG-19 model downloaded and saved.")

if __name__ == "__main__":
    download_vgg19()

