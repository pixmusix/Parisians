#--------------------- IMPORTS ---------------------
import math
import random
import sys
import os
import json
import pickle
import threading

import pygame
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from numpy import asarray, unravel_index
import warnings

#--------------------- OBJECTS ---------------------
class parisian(pygame.sprite.Sprite):
    def __init__(self, name, pos, time):
        pygame.sprite.Sprite.__init__(self)
        self.watch = 50
        self.laptime = time % self.watch
        self.name = name
        self.position = pos
        self.radius = 15
        self.transitioning = random.choice([False, False, False, True, False])
        self.heatmap = heatmap_buildings if self.transitioning else heatmap_roads 
        self.inside = False
        self.dextra = bool(random.getrandbits(1))
        self.theta = (random.randint(-self.radius, self.radius),random.randint(-self.radius, self.radius))
        self.sight = np.empty((self.radius * 2 + 1, self.radius * 2 + 1), np.int32)
        self.png = Image.open('assets/foot_white.png').resize((15, 15), Image.ANTIALIAS)
        self.image = self.dancing_feet()
        self.rect = self.image.get_rect()

    def update(self):
        self.rect = self.image.get_rect()
        self.rect.center = self.position
        self.laptime = (self.laptime + 1) % self.watch

    def dancing_feet(self):
        '''Rotate and crop the footprints of the parisian'''

        #First we want to make one of the feet transparent depending on self.dextra.
        #However, if we are inside, then we are going to be stopped, and we can use double feet.
        alpha = self.sagent_feet(self.png.copy()) if not self.inside else self.png.copy()

        #Now we rotate that foot in the direction of the vector we are currently using.
        angle = int(round((math.atan2(self.theta[0], self.theta[1])*180/math.pi + 180) % 360, 0))
        rota = alpha.rotate(angle, expand=True)

        #We have a single, rotated foot as a png. 
        #Now we need to convert that into a pygame surface for our sprite.
        mode = rota.mode
        size = rota.size
        data = rota.tobytes()
        self.image = pygame.image.fromstring(data, size, mode).convert_alpha()
        return self.image

    def translate(self, i, j):
        '''When the map moves, this function ensures the parisian move with it'''
        self.position = tuple(map(lambda a, b: a - b, self.position, (i, j)))

    def locomotor(self):
        '''In this function, the parisian chooses a new pixel to move to.
        The choice is based on the brightest pixel returned by the path_find function'''
        r = self.radius
        #I want to store the previous position so we can calculate self.theta later.
        past_pos = self.position
        #Get the index of the largest number in our sight
        pathdex = unravel_index(self.sight.argmax(), self.sight.shape)
        #Let's make pathdex relative, such that the parisian is in the centre of that grid
        pathdex = tuple(map(lambda a, b: a - b, pathdex, (r,r)))
        #Now we can update the position by adding pathdex
        self.position = tuple(map(lambda a, b: a + b, self.position, pathdex))
        #We also want to know the direction we are facing, which is a NSEW tuple.
        self.theta = tuple(map(lambda a, b: a - b, self.position, past_pos))
        #Lastly we want to swap which foot we are on.
        self.dextra = not self.dextra
        return self.position
 
    def path_find(self, x, y):
        '''In this function, the parisian checks their surrounding area.
        Args: 
            x & y as pixel co-ordinates relative to the origin of the global map, 
        Returns: a numpy array, representing a heatmap of their prefered future position.'''

        #r is our radius, how far can they see in front of them.
        r = self.radius

        #Generate some randomness to give the path some surprises.
        rand_weight = math.floor(r*10)
        rand_cost = np.random.randint(rand_weight, size=(r * 2 + 1, r * 2 + 1))

        #self.heatmap is a 2D numpy array of the pixels in our map.
        #Streets and buildings are higher numbers than non-passable areas. 
        g_cost = self.aspare(x, y, r)

        #h_cost is our current direction. 
        #This is to give the path some bias to keep going straight and at a constant speed.
        h_cost = self.poursuivre(r, self.theta)

        #f_cost is a compotion of all of the above to create organic movment.
        f_cost = self.normalize(rand_cost + h_cost, 127) + g_cost

        #apply a little bit of noise so no two values are the same.
        f_cost = f_cost + np.random.normal(loc=0., scale=f_cost.std()*0.01, size=f_cost.shape)

        self.sight = f_cost
        return f_cost

    def poursuivre(self, r, th):
        '''Generates a h_cost with a lightcone biasing towards our current direction.
        Args:
            r : The radius of the array.
            th : the angle of our velocity vector.
        Returns: a 2d numpy array of size 2r weighted towards the velocity vector.'''
        h_cost = np.fromfunction(lambda a, b: (th[0]*2 + (a-r))**2 + (th[1]*2 + (b-r))**2, (r * 2 + 1, r * 2 + 1))
        h_cost = np.sqrt(h_cost)
        h_cost = np.floor(h_cost).astype(np.int32)
        return h_cost

    def aspare(self, x, y, r):
        '''Generates a g_cost where high values responding to building and streets.
        Args:
            x, y : The x & y co-or from the origin of the heatmap.
            r : The radius of the heatmatmap.
        Returns: A subset of the heatmap as a 2d numpy array.'''
        g_cost = self.heatmap[y-r:y+r+1, x-r:x+r+1]
        g_cost = np.rot90(np.fliplr(g_cost))

        #If we are near a border, we need to pad out the numpy array.
        w = abs(g_cost.shape[0] - (2*r+1))
        if w > 0:
            u = (w,0) if x < 0 else (0,w)
            g_cost = np.pad(g_cost, (u,(0,0)))
            self.theta = (self.theta[0] * -1, self.theta[1] * -1)
        w = abs(g_cost.shape[1] - (2*r+1))
        if w > 0:
            v = (w,0) if y < 0 else (0,w)
            g_cost = np.pad(g_cost, ((0,0),v))
            self.theta = (self.theta[0] * -1, self.theta[1] * -1)
        return g_cost

    def normalize(self, np_arr, ub):
        '''This function normalises a numpy array to be within the specified upperbound.
        Args: 
            np_arr : numpy array to be normalised.
            ub : the upper bound of the normalised output.
        Returns: a normalised numpy array.'''
        np_arr = np_arr.astype('float64')
        np_arr *= ub/np_arr.max()
        return np_arr.astype(np.int32)

    def sagent_feet(self, pix):
        '''Calcuate which foot we are up to and make the other one transparent.
        Args: pix which is a PIL Image.
        Returns: a PIL where either the left our right side of the image has been made transparent.'''
        sz = pix.size
        canvas = np.zeros([sz[0], sz[1], 4], dtype=np.uint8)
        pixdata = asarray(pix)
        d = math.ceil(sz[0]/2)
        if self.dextra:
            canvas[:,d:] = pixdata[:,d:]
        else:
            canvas[:,:d] = pixdata[:,:d]
        pix = Image.fromarray(canvas)
        return pix

    def try_transition(self):
        '''Rolls a biased dice to sagent self.transitioning and re-assign self.heatmap.
        Returns: self.transitioning which is a boolean'''
        guess = random.randrange(500 if self.transitioning else 2500)
        if guess == 0:
            self.transitioning = not self.transitioning
            self.heatmap = heatmap_buildings if self.transitioning else heatmap_roads
            self.inside = False
        return self.transitioning

    def petrify(self, x, y):
        ''' Checks if we should be standing still or not.
        Args:
            x, y : instances global co-ordinates from the origin
        Returns: True IFF a)self.transitioning && b)self.position local radius corresponds to a building'''
        if self.try_transition():
            if not self.inside:
                r = math.ceil(self.radius/10)
                g = self.aspare(x, y, r)
                self.inside = not np.any(g<250)
        else:
            self.inside = False
        return self.inside

    def reveal(self, path_find):
        surf = pygame.surfarray.make_surface(path_find);
        gameDisplay.blit(surf, (self.position[0] - self.radius, self.position[1] - self.radius))


    def geminio(self):
        '''Create a snapshot of this instance's key property to pass to other classes.
        Returns: A list of properties.'''
        return [self.rect,
                self.sagent_feet(self.png.copy()),
                self.position, 
                self.laptime, 
                self.theta, 
                self.dextra]

class ghost(pygame.sprite.Sprite):
    def __init__(self, rect, png, position, time, theta, dextra):
        pygame.sprite.Sprite.__init__(self)
        self.position = position
        self.theta = theta
        self.dextra = dextra
        self.png = png
        self.alpha = 1.
        self.image = self.dispart(self.png.copy())
        self.rect = rect
        self.watch = 90
        self.laptime = time

    def update(self):
        self.rect = self.image.get_rect()
        self.rect.center = self.position
        self.laptime = (self.laptime + 1) % self.watch
        self.end_self()

    def translate(self, i, j):
        '''When the map moves, this function ensures the parisian move with it'''
        self.position = tuple(map(lambda a, b: a - b, self.position, (i, j)))

    def dispart(self, pix):
        '''Reduce the alpha value of the image by a specified value
        Args: pix which is a PIL Image.
        Returns: a pygame surface with a reduced alpha channel.'''
        self.alpha = self.alpha * 0.99

        #Reduce Alpha
        pixdata = asarray(pix)
        pixdata = pixdata * self.alpha
        pix = Image.fromarray(pixdata.astype(np.uint8))
        return pix

    def sedate(self):
        '''Rotate and crop the footprints of the parisian'''

        #Now we rotate that foot in the direction of the vector we are currently using.
        angle = int(round((math.atan2(self.theta[0], self.theta[1])*180/math.pi + 180) % 360, 0))
        rota = self.png.copy().rotate(angle, expand=True)

        #In the ghost class, we want to reduce the alpha chanel over frames.
        seethru = self.dispart(rota)

        #We have a single, rotated foot as a png. 
        #Now we need to convert that into a pygame surface for our sprite.
        mode = seethru.mode
        size = seethru.size
        data = seethru.tobytes()
        self.image = pygame.image.fromstring(data, size, mode).convert_alpha()
        return self.image

    def end_self(self):
        '''Sends this instance of the sprite to the garbage, freeing the computers memory'''
        if self.alpha <= 0.15:
            self.kill()

class portrait(pygame.sprite.Sprite):
    def __init__(self, name, position, time):
        pygame.sprite.Sprite.__init__(self)
        self.watch = 50
        self.laptime = time % self.watch
        self.position = position
        self.vector = (0,0)
        self.throttle = 45
        self.name = name
        self.png = self.quill()
        self.image = self.to_surface()
        self.rect = self.image.get_rect()
    
    def update(self):
        self.rect = self.image.get_rect()
        self.rect.center = self.position
        self.laptime = (self.laptime + 1) % self.watch

    def quill(self):
        '''Creates a rectagular box and fills it with the instance name.
        Returns: A PIL png image.'''

        #Declare Sizes
        fnt_sz = 10
        pad = 10
        #Declare Colours
        bg_fil = (245, 245, 245, 255)
        txt_fil = (30, 30, 30, 255)
        ln_fil = (128, 128, 128, 255)

        #Declare Font
        fnt = ImageFont.truetype('./assets/Luminari.ttf', fnt_sz)
        #Get size based on length of name
        fnt_bbox = fnt.getbbox(self.name)
        fnt_box = fnt_bbox[2] + pad, fnt_bbox[3] + math.ceil(pad/2)
        #Get top left corner
        fnt_ach = (math.ceil(pad/2), math.ceil(pad/4))

        #Create Background
        banner = Image.new(mode="RGBA", size=(fnt_box), color=bg_fil)
        #Create Text
        pencil = ImageDraw.Draw(banner)
        pencil.text(fnt_ach, self.name, font=fnt, fill=txt_fil)
        #Create Border
        bdr_wth = math.floor(pad/4)
        bdr_top = (0, 0, fnt_box[0] - bdr_wth, 0)
        bdr_btm = (0, fnt_box[1] - bdr_wth, fnt_box[0] - bdr_wth, fnt_box[1] - bdr_wth)
        bdr_lft = (0, 0, 0, fnt_box[1] - bdr_wth)
        bdr_rgt = (fnt_box[0] - bdr_wth, 0, fnt_box[0] - bdr_wth, fnt_box[1] - bdr_wth)
        pencil.line(bdr_top, fill=ln_fil, width=bdr_wth)
        pencil.line(bdr_btm, fill=ln_fil, width=bdr_wth)
        pencil.line(bdr_lft, fill=ln_fil, width=bdr_wth)
        pencil.line(bdr_rgt, fill=ln_fil, width=bdr_wth)

        return banner

    def seek(self, target):
        '''Seek the target position through vector manipulation.
        Args: A tupple with target positon to seek.
        Returns: The new positon of self.'''
        self.vector = tuple(map(lambda a, b: a - b, target, self.position))
        if not math.sqrt(self.vector[0]**2 + self.vector[1]**2) < self.throttle:
            self.vector = (math.floor(self.vector[0] / self.throttle), math.floor(self.vector[1] / self.throttle))
            self.position = tuple(map(lambda a, b: a + b, self.position, self.vector))
        return self.position

    def to_surface(self):
        '''Convert image to pygame surface.'''
        pix = self.png.copy()
        mode = pix.mode
        size = pix.size
        data = pix.tobytes()
        self.image = pygame.image.fromstring(data, size, mode).convert_alpha()
        return self.image

    def translate(self, i, j):
        '''When the map moves, this function ensures the parisians move with it'''
        self.position = tuple(map(lambda a, b: a - b, self.position, (i, j)))

class paris:
    def __init__(self, i, j):
        self.dim = (23000,23000)
        self.pngs = [tile for tile in os.listdir('tiles') if tile.endswith('.png')]
        self.tile_dim = (920,920)
        self.tiles = []
        self.laptime = 0
        self.minutes = math.floor(math.sqrt(len(self.pngs)))
        self.hours = len(self.pngs)

    def update(self, i, j):
        '''Populate self.tiles and with an ID, surface, and position IFF it is nearby to our camera.
        Then it draws all those tiles to the screen.
        Args: Co-oridnates of our camera.
        Returns: a list of surfaces and their relative positions'''

        #Get a pick based on the rolling laptime
        for k in range(self.minutes):
            pic = self.pngs[self.laptime]
            #Bring i,j into absolute co-ords
            pos = tuple(map(lambda a, b: a + b, (i,j), self.dim))
            #extract the intended pixel co-ords from the file name
            pic = pic.replace(".png", "")
            pic_split = pic.split("_")
            pic_dims = (int(pic_split[1]), int(pic_split[2]))
            #pic_dims show y then x, let's flip that to an (x,y) while we multiply by the pixel depth.
            pic_dims_pix = (pic_dims[1] * self.tile_dim[1], pic_dims[0] * self.tile_dim[0])

            #If the pixel co-ords are within a reasonable range
            if self.lokalise(pic_dims_pix, pos):
                #Centre the pix_cor since everything in the main loop is in reference to the camera.
                pixdex = (pic_dims_pix[0] - self.dim[0]/2, pic_dims_pix[1] - self.dim[1]/2)
                #If this is a new tile let's add it in! Otherwise, it's already there, so let's not load it again.
                if not pic in [t[0] for t in self.tiles]:
                    self.tiles.append((pic, pygame.image.load(f"tiles/{pic}.png").convert(), pixdex))
            else:
                #If we don't need it anymore we should remove it, it's taking up ram!
                if pic in [t[0] for t in self.tiles]:
                    self.tiles = list(filter(lambda x: x[0] != pic, self.tiles))

            #Spin it
            self.laptime = self.laptime + 1
            self.laptime = self.laptime % len(self.pngs)

        self.paint(i,j)

        return self.tiles

    def lokalise(self, k, ij):
        '''Is the camera pos between the tile pixel index, plus or minus an extra tile (and a bit) on both axes?
        Args: 
            k  -> the Absolute Pixel-Co-ordinates of a tile.
            ij -> the Inverted Absolute position of the Camera.
        Returns: A boolean -> true if ij is in k or one of k's 8 neighbors.'''
        a = bool(k[0] - self.tile_dim[0] - 100 < self.dim[0] - ij[0] < k[0] + self.tile_dim[0] * 2 + 100)
        b = bool(k[1] - self.tile_dim[1] - 100 < self.dim[1] - ij[1] < k[1] + self.tile_dim[1] * 2 + 100)
        return bool(a and b) 

    def get_random_pos(self):
        '''Generate a randomised tuple that is within range r
        Args: r as range that tuples must be within
        Returns : a tuple of two random ints within r'''
        r = self.dim[0] / 2 - 5000
        x = random.randint(-r, r)
        y = random.randint(-r, r)
        return (x,y)

    def lock_in_bounds(self, x,y,w,v):
        '''Checks if camera is within the borders of the map
        Args : 
            x and y as integers. Pixel co-ordinates to move to.
            w and v as integers. Current pixel co-ordinates.
        Returns :
            new pixel co-ordinates as tuple. 
            x&y if new pos is within the borders; w&v if not.'''
        m = tuple(map(lambda a, b: a + b, (x,y), (self.dim[0] / 2, self.dim[1] / 2)))
        if math.sqrt((m[0] ** 2) + (m[1] ** 2)) < ((self.dim[0] / 2)):
            return (x, y)
        else:
            return (w,v)

    def sort_tiles(self):
        '''sorting the bucket of tiles just makes visualisation easy - optional'''
        self.tiles.sort(key=lambda tup: (tup[2][0], tup[2][1]))

    def paint(self, i, j):
        '''Prints the tiles onto the game display'''
        for tile in self.tiles:
            gameDisplay.blit(tile[1], tuple(map(lambda a,b,c: a + b + c, tile[2], (i,j), (self.dim[0]/2, self.dim[1]/2))))

#--------------------- SETUP ---------------------
#Refuse import!
if __name__ != "__main__": quit()

#Init pygame.
print("Initialising...")
pygame.init()

#Silence Warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

#Init PIL range and Numpy Size
print("Opening up gargantuan Image and Data buffers")
Image.MAX_IMAGE_PIXELS = 529000000 + 1
np.set_printoptions(threshold=sys.maxsize, linewidth=1000)

#Get dimension of the monitor.
print("Calling display dimensions")
monitor_pix = pygame.display.Info().current_w, pygame.display.Info().current_h

#Set the game window pixel ratio to a proportion of the monitor size. 
#This affects how zoomed in we are to the map.
zoom = 2.5
camera = (math.floor(monitor_pix[0]/zoom), math.floor(monitor_pix[1]/zoom))

#Init the game display, and make it full screen. Then, give it a title.
fscr = False
if fscr:
    print("Little Paris in Fullscreen mode")
    gameDisplay = pygame.display.set_mode(camera, pygame.FULLSCREEN)
else:
    print("Little Paris in Window mode")
    gameDisplay = pygame.display.set_mode(camera)

#Set mouse to invisible
pygame.display.set_caption('Little Paris')
print(f"Mouse visibility is {not pygame.mouse.set_visible(True)}")

#Create the clock.
getframe = False
framerate = 60
print("Building the clock")
clock = pygame.time.Clock()
fc = 0

#Load in the maps specs so we can pull it's dimensions which we will need for calculations later.
print("Calling map dimensions")
# Map_Details = (Image.open('maps/Mara.png'))
# print(Map_Details.size)
Map_Details = (23000, 23000)

#We also want a heatmap version of the streets and buildings in a numpy array for matrix operations.
print("Unpickling heatmap binaries.")
heatmap_roads = pickle.load(open("maps/heatmap_roads.b", "rb"))
heatmap_buildings = pickle.load(open("maps/heatmap_buildings.b", "rb"))

#I and J are going to be the co-ordinates of the top left corner of the map. 
#We will initialize it such that the centre of the map begins in the centre of the gameDisplay (Camera)
#So if the map is 100 * 100 pixels, we need the map to init at (-50,-50)
print("Initialising Global Co-oridiates")
i = (-(Map_Details[0] / 2) - 250)
j = (-(Map_Details[1] / 2) - 100)

#Let's initalise the Map!
print("*Drawing Paris*")
Map = paris(i, j)

#citizens: Generate all the parisians on the map
print("Creating Sprite Classes")
print(" -> Citizens")
citizens = pygame.sprite.OrderedUpdates()

#Gallery: one name tag for each parisian which receives the parisians position each frame.
print(" -> Gallery")
gallery = pygame.sprite.OrderedUpdates()

#Graveyard: Copies of the parisians at a past position and orientation.
print(" -> Graveyard")
graveyard = pygame.sprite.Group()

#We need some citizens. There is a json file in our local directory we can parse.
print("Loading Citizens...")
with open('assets/FrenchName_Database.json') as f:
    data = json.load(f)
    for _ in range(1000):
        #Get a random Parisian.
        z = random.randint(0, len(data) - 1)
        agent = data[z]
        print(f"-> Loading @{agent['id']} :: {agent['name']}")
        #create a parisian and a nametag for them.
        new_crt = parisian(agent['name'], Map.get_random_pos(), agent["id"])
        new_pnt = portrait(new_crt.name, new_crt.position, new_crt.laptime)
        #Stick them in the lists.
        citizens.add(new_crt)
        gallery.add(new_pnt)

print("Loading Complete!")

#--------------------- LOOP ---------------------
#Game Loop!
terminate_flag = False
while not terminate_flag:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate_flag = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                terminate_flag = True

    #Hold frame rate
    clock.tick(framerate)

    #We want a copy of where we were before the following translation.
    memory_ij = (i,j)
    
    #Use the mouse to move the map around
    if pygame.mouse.get_pressed()[0]:
        mopos = pygame.mouse.get_pos()
        #hypo is a hypotenuse of a right angle triangle radiating from the centre of the camera. 
        hypo = tuple(map(lambda a, b: a - b, mopos, (camera[0]/2, camera[1]/2)))
        #Scale down max speed.
        hypo = (math.floor(hypo[0]/75), math.floor(hypo[1]/75))
        #Check if we have gone beyond the border of the map and return a new i,j anchor.
        i, j = Map.lock_in_bounds(i - hypo[0], j - hypo[1], i, j)
    
    
    #Draw Map to background 
    x = threading.Thread(target=Map.update, args=(i, j))
    x.start()

    for agent in citizens:
        #Translate them with the map
        agent.translate(memory_ij[0] - i, memory_ij[1] - j)
        if agent.laptime == 0:
            #Do we need to move?
            if not agent.petrify(int(-Map.dim[0] - i + agent.position[0]), int(-Map.dim[1] - j + agent.position[1])):
                #It's expensive to render gosts, so let's only make them if our parisian is on screen.
                if -200 < agent.position[0] < (camera[0] + 200) and -200 < agent.position[1] < (camera[1] + 200):
                    nicholas = ghost(*agent.geminio())
                    graveyard.add(nicholas)
                #Where do we want to go?
                agent.path_find(int(-Map.dim[0] - i + agent.position[0]), int(-Map.dim[1] - j + agent.position[1]))
                #Go there!
                agent.locomotor()
            #Swap feet and orientate ourselves in the direction of our velocity.
            agent.dancing_feet()

    for nick in graveyard:
        #Translate them with the map
        nick.translate(memory_ij[0] - i, memory_ij[1] - j)
        #Reduce alpha channel and align with past orientation
        nick.sedate()

    for idx, painting in enumerate(gallery):
        #Translate them with the map
        painting.translate(memory_ij[0] - i, memory_ij[1] - j)
        if painting.laptime % math.ceil(painting.watch / 8) == 0:
            #Excute a simple seek algorithm for each painting/parisian pair.
            gallery.sprites()[idx].position = gallery.sprites()[idx].seek(citizens.sprites()[idx].position)

    #Update and render
    citizens.update()
    citizens.draw(gameDisplay)
    graveyard.update()
    graveyard.draw(gameDisplay)
    gallery.update()
    gallery.draw(gameDisplay)
    pygame.display.update()

    if getframe:
        clock.get_fps()
        if fc % 120 == 0:
            print(f"----> {math.floor(clock.get_fps())}")
        fc += 1

pygame.quit()
print("Au revoir")
quit()