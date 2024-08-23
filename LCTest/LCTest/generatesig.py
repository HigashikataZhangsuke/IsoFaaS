from PIL import Image
import numpy as np
import multiprocessing
import os

# Generate a large image (approximately 48MB)
def generate_and_save_large_image(index, width=4096, height=4096):
    """
    Generates a large RGB image and saves it to the disk.
    :param index: The index to distinguish file names for each image.
    :param width: The width of the image.
    :param height: The height of the image.
    """
    # Generate a random RGB image (each pixel has 3 channels with values from 0 to 255)
    large_image_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    # Convert the NumPy array to a PIL image
    large_image = Image.fromarray(large_image_array)
    
    # Save the image with a unique name based on the index
    image_path = f'./ROT/large_image_{index}.png'
    large_image.save(image_path)
    print(f"Image {index} saved at {image_path}")

def run_multiprocessing():
    # Get the number of available CPU cores
    num_cores = multiprocessing.cpu_count()
    print(f"Using {num_cores} CPU cores.")

    # Create a pool of processes, one for each CPU core
    with multiprocessing.Pool(num_cores) as pool:
        # Distribute the work across multiple processes
        pool.map(generate_and_save_large_image, range(100))

if __name__ == "__main__":
    # Make sure the output directory exists
    os.makedirs('./ROT', exist_ok=True)
    
    # Run the multiprocessing function
    run_multiprocessing()
