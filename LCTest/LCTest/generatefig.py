from PIL import Image, ImageDraw
import random
from multiprocessing import Pool

def create_image(index):
    width, height = 4000, 4000
    image = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(image)
    # Generate random colors and shapes
    for _ in range(100):  # ?????????10?????1000???????
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = x1 + random.randint(0, width // 10), y1 + random.randint(0, height // 10)
        draw.rectangle([x1, y1, x2, y2], fill=color)

    image.save(f'./Res/{index}.png')
    #return f'Image {index} saved successfully.'

def main():
    num_images = 10000  # ????100???
    pool = Pool()  # ????????
    results = pool.map(create_image, range(num_images))
    pool.close()
    pool.join()
    #print("\n".join(results))

if __name__ == "__main__":
    main()
