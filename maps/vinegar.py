import pickle
from PIL import Image
from numpy import asarray
Image.MAX_IMAGE_PIXELS = 529000000 + 1

def vinegar():
    '''Pickles a map as binary'''
    pickle.dump(asarray(Image.open('heatmap_buildings.png')), open(f"heatmap_buildings.b", "wb"))
    pickle.dump(asarray(Image.open('heatmap_roads.png')), open(f"heatmap_roads.b", "wb"))

if __name__ == "__main__":
	vinegar()
	exit()