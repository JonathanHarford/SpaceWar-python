#!/usr/bin/env python

"""Handy functions and classes for my Spacewar program"""

import math, os, sys, pygame
from numpy import array
import pygame.locals # pygame constants, like "K_ESCAPE".

# Default initialization settings

DISP_WIDTH, DISP_HEIGHT = (800, 600)
SOUND = 1
FPS = 30  # frames per second

WALLS = 1           # Does the universe have bouncy walls? Or is it toroidal?
GRAV_CONST = 0.01   # I like to make this very low, and the sun(s) massive.

SHIP1_THRUST_KEY = pygame.locals.K_w
SHIP1_LEFT_KEY =   pygame.locals.K_a
SHIP1_RIGHT_KEY =  pygame.locals.K_d
SHIP1_SHOOT_KEY =  pygame.locals.K_q

SHIP2_THRUST_KEY = pygame.locals.K_i
SHIP2_LEFT_KEY   = pygame.locals.K_j
SHIP2_RIGHT_KEY  = pygame.locals.K_l
SHIP2_SHOOT_KEY  = pygame.locals.K_k

SUN_MASS = 2500          # Mass of Sun. 0 = no sun
MAXSPEED = 30
SHIP_ROTATE = 10  # How many degrees a ship can turn in a tick.
THRUST = 0.1
START_ENERGY = 10  # Eventually, 100
CRASH_PAIN = 5
SHOT_SPEED = 6
SHOT_LIFESPAN = 250
SHOT_DELAY = 15
SHOT_PAIN = 5

# Functions

def sin(x):
    """Return sin(x) where x is in degrees (which pygame prefers)"""
    return math.sin(math.pi*x/180)

def cos(x):
    """Return cos(x) where x is in degrees (which pygame prefers)"""
    return math.cos(math.pi*x/180)

def dist_sqrd(a,b):
    """Return distance (squared) between two points"""
    return (a[0] - b[0])**2 + (a[1] - b[1])**2

def normalize(r,n=1):
    """Return 2-vector r but with a length of n"""
    return n * r / math.hypot(r[0],r[1])

def load_image(name):
    """Load image from data directory, returning the image and its bounding rectangle"""
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert_alpha()
    except pygame.error, message:
        print 'Cannot load image:', fullname
        raise SystemExit, message
    return image, image.get_rect()

def load_sound(name):
    """Load sound (wav) from data directory"""

    class NoneSound:
        def play(self):
            pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound().play
    fullname = os.path.join('data', name)
    try:
        soundplayer = pygame.mixer.Sound(fullname).play
    except pygame.error, message:
        print 'Cannot load sound:', fullname
        raise SystemExit, message
    return soundplayer

# Classes for our game objects

class GameState():
    flames     = pygame.sprite.RenderUpdates()
    bodys      = pygame.sprite.RenderUpdates()
    explosions = pygame.sprite.RenderUpdates()
    ships      = pygame.sprite.Group()  # For keeping track of Ship.meters
    soundplay = {}

class Body(pygame.sprite.Sprite):
    """Ships, shots, suns are all subclasses of this."""

    def __init__(self, gamestate, img,p,v=(0,0)):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = img
        self.area = pygame.Rect(0,0,DISP_WIDTH,DISP_HEIGHT)
        self.rect.center = p
        self.p = array(self.rect.center) # position
        self.v = array(v)                # velocity
        # "a" = acceleration. Each tick it starts at 0,0 then gets changed by thrust & gravity, then gets added to "v"
        self.a = array((0,0))
        self.radius = self.rect.height/2
        self.mass = 1.0
        self.add(gamestate.bodys)

    def speed_sqrd(self):
        """Return the speed of the Body, squared."""
        return self.v[0]**2 + self.v[1]**2 # Why not return the speed? Because math.sqrt() is relatively expensive.

    def intersects(self,b):
        """Return: Does this body intersect the body b?"""
        return dist_sqrd(self.p,b.p) <= (self.radius + b.radius)**2

    # Well, the gravity's nice, but the orbits are like spirographs.
    def pulledby(self,b):
        """Alters this body's acceleration based on the distance and mass of body b. (I.e., gravity)"""
        if self.intersects(b): return # To keep Bodys from jamming against each other (I think). Also escapes when self=b
        r =  b.p - self.p
        gravity = GRAV_CONST*b.mass/dist_sqrd((0,0),r)
        self.a = self.a + gravity*r

    def update(self, gamestate):
        self.v = self.v + self.a
        self.p = self.p + self.v

        if WALLS:
            if self.p[0] - self.radius < self.area.left:
                self.v[0] = -self.v[0]
                self.p[0] = 2*self.radius-self.p[0]
            elif self.p[0] + self.radius > self.area.right:
                self.v[0] = -self.v[0]
                self.p[0] = 2*self.area.right - 2*self.radius - self.p[0]
            elif self.p[1] - self.radius < self.area.top:
                self.v[1] = -self.v[1]
                self.p[1] = 2*self.radius-self.p[1]
            elif self.p[1] + self.radius > self.area.bottom:
                self.v[1] = -self.v[1]
                self.p[1] = 2*self.area.bottom - 2*self.radius - self.p[1]
        else:   ### Toroidal universe (not very precise)
            if   self.p[0] < self.area.left:
                self.p[0] = self.area.right
            elif self.p[0] > self.area.right:
                self.p[0] = self.area.left
            if   self.p[1] < self.area.top:
                self.p[1] = self.area.bottom
            elif self.p[1] > self.area.bottom:
                self.p[1] = self.area.top

        ### Speed limit
        if self.speed_sqrd() > MAXSPEED**2:
            self.v = normalize(self.v, MAXSPEED)

        self.a = 0 * self.a  # Remove all acceleration, for this tick

        self.rect.center = self.p # Update where the picture is blitted

    def collide(self, gamestate, b):
        """A collision between two Bodys, self and b."""
        # This code is not in the class definitions of Ship, Sun, and Shot because
        # A) I wanted to keep it in one place, and B) I didn't want to have to duplicate
        # code: ship.collide(shot) should be the same as shot.collide(ship).

        if isinstance(self,Sun):
            if isinstance(b,Sun):
                gamestate.soundplay["bonk"]()
                self.bounce(b)
            if isinstance(b,Ship):
                gamestate.soundplay["bonk"]()
                self.bounce(b)
                b.meter.decrease(CRASH_PAIN)
            if isinstance(b,Shot):
                gamestate.soundplay["drip"]()
                b.timeleft = 0
        if isinstance(self,Ship):
            if isinstance(b,Sun):
                gamestate.soundplay["bonk"]()
                self.bounce(b)
                self.meter.decrease(CRASH_PAIN)
            if isinstance(b,Ship):
                gamestate.soundplay["bam"]()
                self.bounce(b)
            if isinstance(b,Shot):
                gamestate.soundplay["doink"]()
                b.timeleft = 0
                self.meter.decrease(SHOT_PAIN)
        if isinstance(self,Shot):
            if isinstance(b,Sun):
                gamestate.soundplay["drip"]()
            if isinstance(b,Ship):
                gamestate.soundplay["doink"]()
                b.meter.decrease(SHOT_PAIN)
            # if isinstance(b,Shot): tiny_boom.play()
            self.timeleft = 0

    def bounce(self,othr):
        """'Billiard-ball' collision"""

        fv = (self.mass * self.v + othr.mass * othr.v) / (self.mass + othr.mass) # Velocity of the center of momentum
        fp = (self.mass * self.p + othr.mass * othr.p) / (self.mass + othr.mass)

        # These are the velocities of the ships in the center of momentum frame.
        fav = self.v - fv
        fbv = othr.v - fv

        fap = self.p - fp
        fbp = othr.p - fp

        dist  = math.sqrt(dist_sqrd(fap,fbp))
        speed = math.hypot(fav[0],fav[1])
        sinA = -( (fbp[0]-fap[0])*fav[1] - (fbp[1]-fap[1])*fav[0] ) / (dist*speed)
        cosA =  ( (fbp[0]-fap[0])*fav[0] + (fbp[1]-fap[1])*fav[1] ) / (dist*speed)

        # Calculate the new velocities (in the c of m frame).
        fav = -((cosA*cosA-sinA*sinA)*fav[0] - (2*sinA*cosA)*fav[1]),-((2*sinA*cosA)*fav[0] + (cosA*cosA-sinA*sinA)*fav[1])
        fbv = -((cosA*cosA-sinA*sinA)*fbv[0] - (2*sinA*cosA)*fbv[1]),-((2*sinA*cosA)*fbv[0] + (cosA*cosA-sinA*sinA)*fbv[1])

        # Transform back to original frame
        self.v = fav + fv
        othr.v = fbv + fv

### End class Body


class Sun(Body):
    """Sun object."""

    def __init__(self, gamestate,img,p,v=(0,0)):
        Body.__init__(self, gamestate,img,p,v)
        self.mass = SUN_MASS

### End class Sun


class Ship(Body):
    """Spaceship object."""

    def __init__(self, gamestate, img, p, v=(0,0)):
        Body.__init__(self, gamestate, img, p, v)
        self.angle = 0.0
        self.original = self.image  # Useful for image rotations.
        self.thrust = 0
        self.cantshoot = 0  # this becomes nonzero for a short while after a shot is fired
        self.flame = Flame()
        self.meter = Meter(pygame.Rect(10,10,300,20),START_ENERGY)
        self.add(gamestate.ships)

    def thrustvec(self):
        return (cos(self.angle), -sin(self.angle))

    def update(self, gamestate):
        if self.cantshoot:
            self.cantshoot = self.cantshoot - 1
        if self.thrust:
            tmp_thrustvec = self.thrustvec() # I use it twice, so I calculate it once
            self.a = self.a + (THRUST * tmp_thrustvec[0], THRUST * tmp_thrustvec[1])
            Body.update(self, gamestate)
            self.flame.rect.center = self.p - (self.radius * tmp_thrustvec[0],self.radius * tmp_thrustvec[1])
        else:
            Body.update(self, gamestate) # I know, having this under the "if" AND the "else" seems silly. Trust me. it's good.

        # update image-- theoretically only necessary if angle has changed but I do it every frame.
        center = self.rect.center
        self.image = pygame.transform.rotate(self.original, self.angle)
        self.rect = self.image.get_rect() # The new image is a different size, so the center will move
        self.rect.center = center # That's better
        if self.meter <= 0:
            self.kill()
            self.meter.value = 0
            Shot(gamestate,
                 load_image("shot.png"),
                (self.p[0] + 1.5*self.radius ,self.p[1] + 1.5*self.radius),
                (self.v[0] + SHOT_SPEED,self.v[1] + 3))
            Shot(gamestate,
                 load_image("shot.png"),
                (self.p[0] + 1.5*self.radius ,self.p[1] - 1.5*self.radius),
                (self.v[0] + SHOT_SPEED,self.v[1] - 3))
            Shot(gamestate,
                 load_image("shot.png"),
                (self.p[0] - 1.5*self.radius ,self.p[1] + 1.5*self.radius),
                (self.v[0] - SHOT_SPEED,self.v[1] + 3))
            Shot(gamestate,
                 load_image("shot.png"),
                (self.p[0] - 1.5*self.radius ,self.p[1] - 1.5*self.radius),
                (self.v[0] - SHOT_SPEED,self.v[1] - 3))

    def rotate(self,deg):
        """Rotate the ship image"""
        self.angle = (self.angle + deg) % 360.0

    def shoot(self,gamestate):
        """Shoot a missile"""
        tmp_thrustvec = self.thrustvec() # I use it twice, so I calculate it once
        self.cantshoot = SHOT_DELAY
        Shot(gamestate,
             load_image("shot.png"),
            (self.p[0] + 1.5*self.radius * tmp_thrustvec[0],self.p[1] + 1.5*self.radius * tmp_thrustvec[1]),
            (self.v[0] + SHOT_SPEED      * tmp_thrustvec[0],self.v[1] + SHOT_SPEED      * tmp_thrustvec[1]))

### End class Ship


class Shot(Body):
    """Shot object"""
    def __init__(self, gamestate,img,p,v=(0,0)):
        Body.__init__(self, gamestate,img,p,v)
        self.timeleft = SHOT_LIFESPAN

    # Should I really be killing shots, or just putting them out of the way until one needs to be born?

    def update(self, gamestate):
        # Shots live for a limited time, so update decrements their mortal coil.
        self.timeleft = self.timeleft - 1
        if self.timeleft > 0: Body.update(self,gamestate)
        else:
            gamestate.explosions.add(Explosion(self.p))
            self.kill()

### End class Shot

class Flame(pygame.sprite.Sprite):
    """What comes out of the rockets"""

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image("flame.png")

### End class Flame


class Explosion(pygame.sprite.Sprite):

    def __init__(self,p):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image("flame.png")
        self.timeleft = 10
        self.rect.center = p

    def update(self, gamestate):
        if self.timeleft:
            center = self.rect.center
            self.image = pygame.transform.scale(self.image,(3*self.timeleft,3*self.timeleft))
            self.rect = self.image.get_rect() # The new image is a different size, so the center will move
            self.rect.center = center # That's better
            self.timeleft = self.timeleft - 1
        else:
            self.kill()

### End class Explosion


class Meter:
    """Displays level of Energy, Shield, etc. for each ship"""

    def __init__(self,rectangle,maximum,value=None):
        self.original_r = rectangle
        self.r = rectangle.move(0,0) # This is the easiest way I could think of to copy a rectangle.
        self.maximum = maximum
        if value: self.value = value
        else: self.value = maximum

    def __cmp__(self,x): return self.value.__cmp__(x)

    def decrease(self,x):
        self.value = self.value - x
        if self.value <= 0: self.value = 0
        self.r.width = self.original_r.width * self.value / self.maximum

    def clear(self,screen,bgd):
        screen.blit(bgd,self.original_r,self.original_r) # I should really only blit as large as necessary

    def draw(self,screen):
        pygame.draw.rect(screen,(255,255,255),self.r,1)

### End class Meter
