import cv2
import math

def tile_it(file):
    
    img = cv2.imread(f'{file}.png')

    img_shape = img.shape
    tile_size = (920, 920)
    offset = (920, 920)

    for i in range(int(math.ceil(img_shape[0]/(offset[1] * 1.0)))):
        for j in range(int(math.ceil(img_shape[1]/(offset[0] * 1.0)))):
            cropped_img = img[offset[1]*i:min(offset[1]*i+tile_size[1], img_shape[0]), offset[0]*j:min(offset[0]*j+tile_size[0], img_shape[1])]
            # Debugging the tiles
            cv2.imwrite(f"../tiles/{file}_{i}_{j}.png", cropped_img)

if __name__ == '__main__':
    tile_it('Mara')
