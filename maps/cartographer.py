import io
from prettymaps import *
import pickle
import matplotlib.font_manager as fm
from matplotlib import pyplot as plt
from PIL import Image, ImageFilter, ImageOps, PngImagePlugin
from numpy import asarray

#----------- GLOBALS ------------------
Image.MAX_IMAGE_PIXELS = 529000000 + 1
map_radius = 6000
map_location = (48.86554, 2.32115)
#--------------------------------------
class map_out:

    def __init__(self, x):
        if not isinstance(x, PngImagePlugin.PngImageFile):
            raise ValueError("A map_out only accepts objects of type PIL.PngImagePulgin.PngImageFile")
            exit()
        self.img = x
        self.name = ''

    def append_mark(self, mark):
        if not self.name == '':
            self.name = self.name + "_" + mark
        else:
            self.name = mark
        return self

    def vinegar(self):
        '''Pickles a map_out'''
        pickle.dump(asarray(self.img), open(f"{self.name}.b", "wb"))
        return self

    def todisk(self):
        self.img.save(f"{self.name}.png")
        return self

def fig_to_img(fig):
    '''Converts MatPlotLib figure into a PIL image. Thanks Internet
    Args: fig as MatPlotLib figure object
    Returns: Img as PIL Image object'''
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    return Image.open(buf)

def createMara(dimy):
    ''' Create a map of Paris.
    Args:
        dimy (int) : the width and height of the map
    Returns: The name of the file created as string'''

    # Init matplotlib figure
    fig, ax = plt.subplots(figsize = (dimy, dimy), constrained_layout = True)

    layers = plot(
        # Address:
        map_location,
        # Plot geometries in a circle of radius:
        radius = map_radius,
        # Matplotlib axis
        ax = ax,
        # Which OpenStreetMap layers to plot and their parameters:
        layers = {
                # Perimeter (in this case, a circle)
                'perimeter': {},
                # Streets and their widths
                'streets': {
                    'width': {
                        'motorway': 5,
                        'trunk': 5,
                        'primary': 4.5,
                        'secondary': 4,
                        'tertiary': 3.5,
                        'residential': 3,
                        'service': 2,
                        'unclassified': 2,
                        'pedestrian': 2,
                        'footway': 1,
                    }
                },
                # Other layers:
                #   Specify a name (for example, 'building') and which OpenStreetMap tags to fetch
                'building': {'tags': {'building': True, 'landuse': 'construction'}, 'union': False},
                'water': {'tags': {'natural': ['water', 'bay']}},
                'green': {'tags': {'landuse': 'grass', 'natural': ['island', 'wood'], 'leisure': 'park'}},
                'forest': {'tags': {'landuse': 'forest'}},
                'parking': {'tags': {'amenity': 'parking', 'highway': 'pedestrian', 'man_made': 'pier'}}
            },
            # drawing_kwargs:
            #   Reference a name previously defined in the 'layers' argument and specify matplotlib parameters to draw it
            drawing_kwargs = {
                'background': {'fc': '#010101', 'ec': '#010101', 'hatch': 'ooo...', 'zorder': -1},
                'perimeter': {'fc': '#B59C7D', 'ec': '#B59C7D', 'lw': 0, 'hatch': 'ooo...',  'zorder': 0},
                'green': {'fc': '#0C330A', 'ec': '#003D31', 'lw': 1, 'zorder': 1},
                'forest': {'fc': '#154012', 'ec': '#112e18', 'lw': 1, 'zorder': 1},
                'water': {'fc': '#000520', 'ec': '#001929', 'hatch': 'ooo...', 'hatch_c': '#005082', 'lw': 1, 'zorder': 2},
                'parking': {'fc': '#A99580', 'ec': '#A99580', 'lw': 1, 'zorder': 3},
                'streets': {'fc': '#2F3737', 'ec': '#475657', 'alpha': 1, 'lw': 0, 'zorder': 3},
                'building': {'palette': ['#956B4B', '#7A583E', '#443122'], 'ec': '#2F3737', 'lw': .5, 'zorder': 4},
            }
    )
    mara = map_out(fig_to_img(plt))
    mara.append_mark("Mara")
    return mara

def getAmenity(dimy):
    ''' Create a map of Paris with just amenity.
    Args:
        dimy (int) : the width and height of the map
    Returns: The name of the file created as string'''

    # Init matplotlib figure
    fig, ax = plt.subplots(figsize = (dimy, dimy), constrained_layout = True)

    layers = plot(
        # Address:
        map_location,
        # Plot geometries in a circle of radius:
        radius = map_radius,
        # Matplotlib axis
        ax = ax,
        # Which OpenStreetMap layers to plot and their parameters:
        layers = {
                # Perimeter (in this case, a circle)
                'perimeter': {},
                'pubscafes': {'tags': {'amenity': 'bars', 'amenity': 'cafe', 'amenity': 'pub'}, 'union': False},
                'eaters': {'tags': {'amenity': 'biergarten', 'amenity': 'restaurant'}, 'union': False},
                'life': {'tags': {'amenity': 'theatre', 'amenity': 'nightclub', 'amenity': 'library'}, 'union': False},
                'buyandstay': {'tags': {'building': 'supermarket', 'building': 'hotel'}, 'union': False}
            },
            # drawing_kwargs:
            #   Reference a name previously defined in the 'layers' argument and specify matplotlib parameters to draw it
            drawing_kwargs = {
                # Perimeter (in this case, a circle)
                'perimeter': {'fc': '#EEEEEE', 'ec': '#EEEEEE', 'lw': 0, 'hatch': 'ooo...',  'zorder': 0},
                'pubscafes': {'fc': '#AA3333', 'ec': '#BBBBBB', 'lw': 0, 'hatch': 'xxx...',  'zorder': 0},
                'eaters': {'fc': '#33AA33', 'ec': '#BBBBBB', 'lw': 0, 'hatch': 'zzz...',  'zorder': 0},
                'life': {'fc': '#3333AA', 'ec': '#BBBBBB', 'lw': 0, 'hatch': 'yyy...',  'zorder': 0},
                'buyandstay': {'fc': '#AA7777', 'ec': '#BBBBBB', 'lw': 0, 'hatch': '###...',  'zorder': 0}
            }
    )
    amen = map_out(fig_to_img(plt))
    amen.append_mark("Amen")
    return amen

def createNegativeStreets(dimy):
    ''' Create a map of Paris with just the routes.
    Args:
        dimy (int) : the width and height of the map
    Returns: The name of the file created as string'''

    # Init matplotlib figure
    fig, ax = plt.subplots(figsize = (dimy, dimy), constrained_layout = True)

    layers = plot(
        # Address:
        map_location,
        # Plot geometries in a circle of radius:
        radius = map_radius,
        # Matplotlib axis
        ax = ax,
        # Which OpenStreetMap layers to plot and their parameters:
        layers = {
                # Perimeter (in this case, a circle)
                'perimeter': {},
                # Streets and their widths
                'streets': {
                    'width': {
                        'motorway': 5,
                        'trunk': 5,
                        'primary': 4.5,
                        'secondary': 4,
                        'tertiary': 3.5,
                        'residential': 3,
                        'service': 2,
                        'unclassified': 2,
                        'pedestrian': 2,
                        'footway': 1,
                    }
                },
                # Other layers:
                #   Specify a name (for example, 'building') and which OpenStreetMap tags to fetch
                'building': {'tags': {'building': True, 'landuse': 'construction'}, 'union': False},
            },
            # drawing_kwargs:
            #   Reference a name previously defined in the 'layers' argument and specify matplotlib parameters to draw it
            drawing_kwargs = {
                'background': {'fc': '#FFFFFF', 'ec': '#FFFFFF', 'hatch': 'ooo...', 'zorder': -1},
                'perimeter': {'fc': '#FFFFFF', 'ec': '#FFFFFF', 'lw': 0, 'hatch': 'ooo...',  'zorder': 0},
                'streets': {'fc': '#000000', 'ec': '#000000', 'alpha': 1, 'lw': 0, 'zorder': 3},
                'building': {'palette': ['#AAAAAA', '#AAAAAA', '#AAAAAA'], 'ec': '#AAAAAA', 'lw': .5, 'zorder': 4},
            }
    )

    ngtv = map_out(fig_to_img(plt))
    ngtv.append_mark("Ngtv_streets")
    return ngtv

def createNegativeBuildings(dimy):
    ''' Create a map of Paris with just the buildings.
    Args:
        dimy (int) : the width and height of the map
    Returns: The name of the file created as string'''

    # Init matplotlib figure
    fig, ax = plt.subplots(figsize = (dimy, dimy), constrained_layout = True)

    layers = plot(
        # Address:
        map_location,
        # Plot geometries in a circle of radius:
        radius = map_radius,
        # Matplotlib axis
        ax = ax,
        # Which OpenStreetMap layers to plot and their parameters:
        layers = {
                # Perimeter (in this case, a circle)
                'perimeter': {},
                # Streets and their widths
                'streets': {
                    'width': {
                        'motorway': 5,
                        'trunk': 5,
                        'primary': 4.5,
                        'secondary': 4,
                        'tertiary': 3.5,
                        'residential': 3,
                        'service': 2,
                        'unclassified': 2,
                        'pedestrian': 2,
                        'footway': 1,
                    }
                },
                # Other layers:
                #   Specify a name (for example, 'building') and which OpenStreetMap tags to fetch
                'building': {'tags': {'building': True, 'landuse': 'construction'}, 'union': False},
            },
            # drawing_kwargs:
            #   Reference a name previously defined in the 'layers' argument and specify matplotlib parameters to draw it
            drawing_kwargs = {
                'background': {'fc': '#FFFFFF', 'ec': '#FFFFFF', 'hatch': 'ooo...', 'zorder': -1},
                'perimeter': {'fc': '#FFFFFF', 'ec': '#FFFFFF', 'lw': 0, 'hatch': 'ooo...',  'zorder': 0},
                'streets': {'fc': '#AAAAAA', 'ec': '#AAAAAA', 'alpha': 1, 'lw': 0, 'zorder': 3},
                'building': {'palette': ['#000000', '#000000', '#000000'], 'ec': '#000000', 'lw': .5, 'zorder': 4},
            }
    )

    ngtv = map_out(fig_to_img(plt))
    ngtv.append_mark("Ngtv_buildings")
    return ngtv

def sepiaMap(mp):
    ''' A sepia filter.
    Args:
        mp (map_out) : map_out to apply filter to
    Returns: The same map_out with a sepia filter'''

    # create the pixel array
    width, height = mp.img.size
    pixels = mp.img.load() 

    for py in range(height):
        print('sepia -> ',py)
        for px in range(width):
            r, g, b, a = mp.img.getpixel((px, py))

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            if tr > 255:
                tr = 255

            if tg > 255:
                tg = 255

            if tb > 255:
                tb = 255

            pixels[px, py] = (tr,tg,tb, a)

    return mp.append_mark('sepia')

def invertMap(mp):
    ''' Create a negative of a png.
    Args:
        mp (map_out) : the map_out to invert
    Returns: the same map_out inverted'''
    mp.img = ImageOps.invert(mp.img)
    return mp.append_mark('invert')

def grayscale(mp):
    ''' Create a grayscale version of a png.
    Args:
        mp (map_out) : the map_out to flatten
    Returns: the same map_out as a grayscale'''
    mp.img = ImageOps.grayscale(mp.img)
    return mp.append_mark('gray')
        

def blurMap(mp, radius):
    ''' A gaussian blur filter.
    Args:
        mp (map_out) : the path to the map_out to apply filter
    Returns: the same map_out blurred'''
    mp.img = mp.img.filter(ImageFilter.BoxBlur(radius))
    return mp.append_mark('blur')

def flipMap(mp):
    mp.img = mp.img.transpose(Image.FLIP_LEFT_RIGHT)
    return mp.append_mark('flip')

def defaults():
    #Generate Main Map
    main_map = createMara(230)
    main_map.name = 'Mara'
    main_map.todisk()

    #Generate Both Negative for Path Following
    street_map = invertMap(grayscale(createNegativeStreets(230)))
    street_map.name = 'heatmap_roads'
    street_map.todisk()
    street_map.vinegar()
    build_map = invertMap(grayscale(createNegativeBuildings(230)))
    build_map.name = 'heatmap_buildings'
    build_map.todisk()
    build_map.vinegar()

if __name__ == "__main__":
    try:
        defaults()
    except ValueError:
        print("Exiting Runtime due to ValueError!")


        