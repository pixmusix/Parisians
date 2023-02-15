# Parisians

A cute sim of Paris with autonomous pedestrians for your SBC projects.

https://user-images.githubusercontent.com/68670157/218994312-12538e5d-5171-4b94-a207-2348b8384e81.mp4

## Dependencies

#### Required Libraries
* https://pypi.org/project/pygame/
* https://pypi.org/project/pillow/
* https://pypi.org/project/numpy/
* https://pypi.org/project/matplotlib/
* https://pypi.org/project/prettymaps/
* https://pypi.org/project/opencv-python/

#### Building non-packaged Assets
Due to their size, Mara.png heatmap_buildings.png, and heatmap_roads.png do not come with this git repository. They must be created locally with code. This is done with the excellent git repo [prettymaps by marceloprates](https://github.com/marceloprates/prettymaps)

To create the maps the script use cartographer.py which pulls it's data from [openstreetmaps](https://www.openstreetmap.org/). cartographer.py contains a function: default() which builds the bare minimum you need to begin.
```python
def defaults():
    #Generate Main Map
    main_map = createMara(230)
    main_map.todisk()

    #Generate Both Negative for Path Following
    street_map = invertMap(grayscale(createNegativeStreets()))
    street_map.name = 'heatmap_roads'
    street_map.vinegar()
    build_map = invertMap(grayscale(createNegativeBuildings()))
    build_map.name = 'heatmap_buildings'
    build_map.vinegar()
```

Because the resulting maps are very large files, *Parisians* uses [tiled rendering](https://en.wikipedia.org/wiki/Tiled_rendering) to manage ram overflow. These tiles are saved in the .tiles directory and are created from mara.png with the sizzors.py script.

```bash
Python3 cartographer.py
Python3 sizzors.py
```

## Main Loop
The script that runs the main game loop is main.py located in the root of the repository. main.py classes and functions often inherit from pygame sprites and use global variables. Therefore it is not recommended to import main.py.

```bash
Python3 main.py
```

#### Set Zoom Multiplier
You can change the zoom with the zoom varible. The zoom variable sets the dimension of the in game camera to a ratio of your monitors resolution. 
```python
#Set the game window pixel ratio to a proportion of the monitor size. 
#This affects how zoomed in we are to the map.
zoom = 2.5
camera = (math.floor(monitor_pix[0]/zoom), math.floor(monitor_pix[1]/zoom))
```

#### Fullscreen
You can throw the sim into full screen with the fscr flag
```python
#Init the game display, and make it full screen. Then, give it a title.
fscr = False
if fscr:
    print("Little Paris in Fullscreen mode")
    gameDisplay = pygame.display.set_mode(camera, pygame.FULLSCREEN)
else:
    print("Little Paris in Window mode")
    gameDisplay = pygame.display.set_mode(camera)
```

#### Framerate
To monitor the frame rate set the getframe flag. You can change the framerate here too.
```python
#Create the clock.
getframe = False
framerate = 60
print("Building the clock")
clock = pygame.time.Clock()
fc = 0
```

#### Mouse Visibility
You can turn the mouse invisible inside this print line
```python
#Set mouse to invisible
pygame.display.set_caption('Little Paris')
print(f"Mouse visibility is {not pygame.mouse.set_visible(True)}")
```

#### Loadtime Initial Position
To can set the initial loading position of the simulation when defining *i* and *j* which are the co-ordinates of our global vector: *where we are in paris*.
```python
print("Initialising Global Co-oridiates")
i = (-(Map_Details[0] / 2) - 250)
j = (-(Map_Details[1] / 2) - 100)
```
For example: if you would like a random inital position on each load...
```python
print("Initialising Global Co-oridiates to random values 🤷")
i = random.randint(100, Map_Details[0] - 101)
j = random.randint(100, Map_Details[0] - 101)
```

## Maps, Tiles

#### Maps
The ./maps/ folder contains cartographer.py for genertating new maps and sizzors.py for populating the ./tiles/ folder.

Assuming you have run cartographer.py default() function, here you will find the map of paris as well as the heatmaps used for pathfinding.

However, the dimensions 23000 * 23000 pixels is hardcoded into main.py. This is to avoid having to check the dimensions of arbitrary files which would require reading the large file. If you would like to use other dimensions this is easily modified.

Heatmaps are read into main.py as binaries and unpickled at runtime. Surprisingly, this was the secret sauce that kept main.py always under 2gb of RAM.

- mara.png : the map printed to the camera.
- heatmap_roads.png : used for pathfinding
- heatmap_buildings.png : used when the parisian.transitioning flag is true.

#### Tiles
./tiles/ contains an indexed list of 920 by 920 pixel slices of the png built by sizzors.py using mara.png. This folder is read by the paris class dynamically at runtime to prevent RAM overload. At present, 920px is a hardcoded number (a factor of 23000).
```python
class paris:
    def __init__(self, i, j):
        self.dim = (23000,23000)
        self.pngs = [tile for tile in os.listdir('tiles') if tile.endswith('.png')]
        self.tile_dim = (920,920)
        self.tiles = []
```
```python
#If the pixel co-ords are within a reasonable range of our camera
if self.lokalise(pic_dims_pix, pos):
    #If this is a new tile let's add it in!
    if not pic in [t[0] for t in self.tiles]:
        self.tiles.append((pic, pygame.image.load(f"tiles/{pic}.png").convert(), pixdex))
else:
    #If we don't need it anymore we should remove it, it's taking up ram!
    if pic in [t[0] for t in self.tiles]:
        self.tiles = list(filter(lambda x: x[0] != pic, self.tiles))
```

## Autonomous Walkers

#### Overview
FrenchName_Database.json, located in ./assets/, is downloaded from [this dataset](https://en.wiktionary.org/wiki/Appendix:French_given_names) using curlPari.py.
main.py calls each object in the json file and uses it's properties to create a new instance of the parisian class.

#### Adding or Removing Autonomous Walkers
It is possible to add your own Autonomous Walkers by adding them into FrenchName_Database.json manually following standard json syntax.
A charecter must, at minimum, have an "ID" and a "name" key:value pair.
If you don't want to maintiain indexing, this repo also contains a script that reindexes the charecters in FrenchName_Database.json for you.
```bash
Python3 re_idx_json.py
```

Alternatively, you can also hardcode in a new Walker like so...
```python
my_auto_walker = parisian("Frère Jacques", paris.get_random_pos(), random.randint(0, 1000))
my_banner = portrait(my_auto_walker.name, my_auto_walker.position, my_auto_walker.timeturner)
citizens.add(my_auto_walker)
gallery.add(my_banner)
```

#### How does the Path Finding Work?
The parisian class find it's way across the map using the following formala.

parisian.position = The vector of the maximum value with the matrix *f* where... 
*f = [g + h] + p*

- *g* is a slice of a matrix with high scoring in bounds pixels (roads, bridges, buildings, etc) and low scoring out of bounds pixels (water, forests, railways, etc).
- *h* is a matrix where pixels in the direction of movement, that is the angle of the auto-walkers velocity vector, are scored highest.
- *p* is a matrix of non-repeating pseudo-random values.
- *f* is the normalised sum of the above.

Note : The size of all the matricies is the inscribed square of a circle with radius parisian.radius. (r * 2 + 1)

To summarise, *f*, or f-cost, is a noisy matrix that gives higher scores to pixels that are roads or buildings (parisian.heatmap) and higher scores to pixels that maintain momentum. Parisians "path-find" by setting it's position to the vector of the highest pixel of *f* which, importantly, will most likely be on the road in front of them.

![example_pathfinding](https://user-images.githubusercontent.com/68670157/218995453-526b7403-6901-4d3a-844d-16f22f19600a.png)

## Using a Raspberry PI

#### Minimum Requirements
For my build I used a [Raspberry Pi 4 model b](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/). You will need at least 2gb of RAM. I have also tested the [LattePanda](https://www.dfrobot.com/product-1404.html).

#### Modifying Autonomous Walkers Internal Clocks to Improve Performance. 
For Single Board Computer applications it is possible to improve performance by tinkering with ...
- parisian.watch : How many frames between each movement.
- parisian.radius : How far the parisian can see and move each calculation.
- portrait.watch : How many frames between each movement.
- ghost.watch : How many frames between each calculation.
- ghost.dispart() : How slowly the retraced steps disapear (and thus how long they need calculation time)
Remember, the internal clocks of these objects are out of phase with one another. This means that even if each objects calculations per frame are low, something will always be moving.

#### Using a Touch Screen.
For my build I had success with the [Waveshare 10.1inch Resistive Touch Screen LCD.](https://www.waveshare.com/wiki/10.1inch_HDMI_LCD). I used [this tutorial](https://www.waveshare.com/wiki/10.1inch_HDMI_LCD) to configure the touch screen. However, I found clicking clumsy with the touchscreens I tried. To resolve this I modified the gameloop of main.py such that, rather than clicking to move the camera, the camera steady only within a 200px safe zone in the center of the screen. This way, a simple tap near the edge of the touch screen to jump the mouse to that point will be sufficient to move the camera. Tapping the centre again will steady the camera.
```python
mopos = pygame.mouse.get_pos()
cx, cy = camera #Camera global location
if not (mopos[0] in range(cx - 200, cx + 200) and mopos[1] in range(cy - 200, cy + 200)):
    #Use the mouse to move the map around
```

#### Running at startup (linux).
I found I needed the [Desktop Version of Raspberry PI OS](https://www.raspberrypi.com/documentation/computers/os.html).I had the most success placing the following code in my .bashrc file at the bottom.
```bash
sleep 5
cd /absolute/path/to/script
python3 Raspoti.py
```

Then I ensured terminal booted on launch
```bash
cd home/pi/.config/lxsession/LXDE-pi/
echo "@lxterminal" >> autostart
reboot
```

Having terminal open appeared to be "necessary" to make the hotkeys trigger.
I also found that this method ensured that wifi and other auxiliaries would be operation before the loop would run.

## MIT License

Copyright (c) 2022 pixmusix

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
