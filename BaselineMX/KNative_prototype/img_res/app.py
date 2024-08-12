from PIL import Image
def lambda_handler():
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
        width, height = image.size
        # Set the crop area
        left = 4
        top = height / 5
        right = left + width / 2
        bottom = 3 * height / 5
        im1 = image.crop((left, top, right, bottom))
        # Perform multiple resize operations to increase memory bandwidth usage
        for j in range(10):
            new_width = width * (j + 1)
            new_height = height * (j + 1)
            im1 = im1.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Save the processed mage to a specified path
        list.append(im1)
        end_time = time.time()
        # Calculate elapsed time
        elapsed_time = end_time - start_time
        total_time += elapsed_time

    average_time = total_time / generation_count
    for i in range(len(list)):
        output_image_path = f"./results/output_{os.getpid()}_{i}.jpg"
        list[i].save(output_image_path)

    return {"AverageExecutionTime": average_time}
