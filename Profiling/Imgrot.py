import time
from PIL import Image
import os
def alu():
    input_dir = './Res/'  # Modify this to your image directory
    image_list = os.listdir(input_dir)
    generation_count = 100

    total_time = 0.0
    list = []
    for i in range(generation_count):
        input_image_name = image_list[i % len(image_list)]
        input_image_path = os.path.join(input_dir, input_image_name)

        start_time = time.time()

        # Open and process the image
        image = Image.open(input_image_path)

        im1 = image.transpose(Image.ROTATE_90)
        im2 = im1.transpose(Image.ROTATE_90)
        im3 = im2.transpose(Image.ROTATE_90)
        list.append(im3)
        # im3.save(proc_image_path)
        # Save the processed image to a specified path
        # output_image_path = f"/home/ubuntu/Resultsbin/output_{os.getpid()}_{i}.jpg"
        # im3.save(proc_image_path)
        end_time = time.time()

        # Calculate elapsed time
        elapsed_time = end_time - start_time
        total_time += elapsed_time

    average_time = total_time / generation_count
    # output_image_path = f"/home/ubuntu/Resultsbin/output_{os.getpid()}_{i}.jpg"
    # im3.save(output_image_path)
    # Check if running on CPU 0-3 before writing to the file

    for i in range(len(list)):
        output_image_path = f"./results/output_{os.getpid()}_{i}.jpg"
        list[i].save(output_image_path)
    return {"AverageExecutionTime": average_time}

listoftheresult = []
for i in range(5):
    st = time.time()
    result = alu()
    et = time.time()
    if i>1:
        listoftheresult.append(et-st)

print(sum(listoftheresult)/len(listoftheresult))
print("Now ready for BW Tests")
while True:
    alu()