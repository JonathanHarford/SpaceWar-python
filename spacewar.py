#/usr/bin/env python
"""
Spacewar! is one of the earliest known digital computer games. It is a two-player game, with each player taking control of a spaceship and attempting to destroy the other. A star in the centre of the screen pulls on both ships and requires maneuvering to avoid falling into it.

TODO:
ships explode
2nd ship
fullscreen mode
title/menu
AI
Make ships reflect sun
ship mouse-controllable

OPTIMIZATIONS:
* Instead of kill()ing and creating shots and explosions on the fly, put them in and take them out of unrendered groups
* Rewrite in C++ (haha only serious)
"""
### Import Modules

import os, pygame, math, random
from pygame.locals import *
from math import sqrt

# numpy arrays are (almost too) elegant: 2*[2,4] == [4,8] rather than 2*[2,4] == [2,4,2,4]
# I don't remember why I'm not just using plain arrays. Speed? Oh well.

from numpy import array

from spacewar_func import * # My Spacewar functions

### Stuff ya can change

WINDOW_SIZE = (800,600)
SOUND = 1

WALLS = 1           # Does the universe have bouncy walls? Or is it toroidal?
GRAV_CONST = 0.01   # I like to make this very low, and the sun(s) massive.

SHIP1_THRUST_KEY = K_w
SHIP1_LEFT_KEY   = K_a
SHIP1_RIGHT_KEY  = K_d
SHIP1_SHOOT_KEY  = K_q

SHIP2_THRUST_KEY = K_i
SHIP2_LEFT_KEY   = K_j
SHIP2_RIGHT_KEY  = K_l
SHIP2_SHOOT_KEY  = K_k

SUN = 2500         # Mass of Sun. 0 = no sun
MAXSPEED = 30
SHIP_ROTATE = 10   # How fast a ship can rotate. Specifically: how many degrees a ship can turn in a tick.
THRUST = 0.1
START_ENERGY = 10  # Eventually, 100
CRASH_PAIN = 5
SHOT_SPEED = 6
SHOT_LIFESPAN = 250
SHOT_DELAY = 15
SHOT_PAIN = 5

### Initialization

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'

# Everyone can play sounds! (I know, sloppy.)

soundplay = {}

# These are some groups I want everyone to be able to access. (See above re: sloppy)

flames     = pygame.sprite.RenderUpdates()
bodys      = pygame.sprite.RenderUpdates()
explosions = pygame.sprite.RenderUpdates()
ships      = pygame.sprite.Group() # For keeping track of Ship.meters

### Classes for our game objects

class Body(pygame.sprite.Sprite):
	"Ships, shots, suns are all subclasses of this."

	def __init__(self,img_filename,p,v=(0,0)):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image(img_filename)
		self.area = pygame.Rect(0,0,WINDOW_SIZE[0],WINDOW_SIZE[1])
		self.rect.center = p
		self.p = array(self.rect.center) # position
		self.v = array(v)                # velocity
		### "a" = acceleration. Each tick it starts at 0,0 then gets changed by thrust & gravity, then gets added to "v"
		self.a = array((0,0))
		self.radius = self.rect.height/2
		self.mass = 1.0
		self.add(bodys)

	def speed_sqrd(self):
		"The speed of the Body, squared."
		return self.v[0]**2 + self.v[1]**2 # Why not return the speed? Because math.sqrt() is relatively expensive.

	def intersects(a,b):
		"Answers the question: Does this body intersect the body b?"
		return dist_sqrd(a.p,b.p) <= (a.radius + b.radius)**2

	# Well, the gravity's nice, but the orbits are like spirographs.
	def pulledby(self,b):
		"Alters this body's acceleration based on the distance and mass of body b. (I.e., gravity)"
		if self.intersects(b): return # To keep Bodys from jamming against each other (I think). Also escapes when self=b
		r =  b.p - self.p
		gravity = GRAV_CONST*b.mass/dist_sqrd((0,0),r)
		self.a = self.a + gravity*r

	def update(self):
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
			if   self.p[0] < self.area.left:   self.p[0] = self.area.right
			elif self.p[0] > self.area.right:  self.p[0] = self.area.left
			if   self.p[1] < self.area.top:    self.p[1] = self.area.bottom
			elif self.p[1] > self.area.bottom: self.p[1] = self.area.top

		### Speed limit
		if self.speed_sqrd() > MAXSPEED**2: self.v = normalize(self.v,MAXSPEED)

		self.a = 0 * self.a # Remove all acceleration, for this tick

		self.rect.center = self.p # Update where the picture is blitted

	def collide(a,b):
		"""A collision between two Bodys, a and b."""
		# This code is not in the class definitions of Ship, Sun, and Shot because
		# A) I wanted to keep it in one place, and B) I didn't want to have to duplicate
		# code: ship.collide(shot) should be the same as shot.collide(ship).

		if isinstance(a,Sun):
			if isinstance(b,Sun):
				soundplay["bonk"]()
				bounce(a,b)
			if isinstance(b,Ship):
				soundplay["bonk"]()
				bounce(a,b)
				b.meter.decrease(CRASH_PAIN)
			if isinstance(b,Shot):
				soundplay["drip"]()
				b.timeleft = 0
		if isinstance(a,Ship):
			if isinstance(b,Sun):
				soundplay["bonk"]()
				bounce(a,b)
				a.meter.decrease(CRASH_PAIN)
			if isinstance(b,Ship):
				soundplay["bam"]()
				bounce(a,b)
			if isinstance(b,Shot):
				soundplay["doink"]()
				b.timeleft = 0
				a.meter.decrease(SHOT_PAIN)
		if isinstance(a,Shot):
			if isinstance(b,Sun): soundplay["drip"]()
			if isinstance(b,Ship):
				soundplay["doink"]()
				b.meter.decrease(SHOT_PAIN)
			# if isinstance(b,Shot): tiny_boom.play()
			a.timeleft = 0

### End class Body


class Sun(Body):
	"""Sun object."""

	def __init__(self,img_filename,p,v=(0,0)):
		Body.__init__(self,img_filename,p,v) #call Body intializer
		self.mass = SUN

### End class Sun


class Ship(Body):
	"""Spaceship object."""

	def __init__(self,img_filename,p,v=(0,0)):
		Body.__init__(self,img_filename,p,v)
		self.angle = 0.0
		self.original = self.image # Useful for image rotations.
		self.thrust = 0
		self.cantshoot = 0 # this becomes nonzero for a short while after a shot is fired
		self.flame = Flame()
		self.meter = Meter(pygame.Rect(10,10,300,20),START_ENERGY)
		self.add(ships)

	def thrustvec(self): return (cos(self.angle), -sin(self.angle))

	def update(self):
		if self.cantshoot: self.cantshoot = self.cantshoot - 1
		if self.thrust:
			tmp_thrustvec = self.thrustvec() # I use it twice, so I calculate it once
			self.a = self.a + (THRUST * tmp_thrustvec[0], THRUST * tmp_thrustvec[1])
			Body.update(self)
			self.flame.rect.center = self.p - (self.radius * tmp_thrustvec[0],self.radius * tmp_thrustvec[1])
		else: Body.update(self) # I know, having this under the "if" AND the "else" seems silly. Trust me. it's good.

		# update image-- theoretically only necessary if angle has changed but I do it every frame.
		center = self.rect.center
		self.image = pygame.transform.rotate(self.original, self.angle)
		self.rect = self.image.get_rect() # The new image is a different size, so the center will move
		self.rect.center = center # That's better
		if self.meter <= 0:
			self.kill()
			self.meter.value = 0
			Shot("shot.png",
			    (self.p[0] + 1.5*self.radius ,self.p[1] + 1.5*self.radius),
			    (self.v[0] + SHOT_SPEED      ,self.v[1] + 3))
			Shot("shot.png",
			    (self.p[0] + 1.5*self.radius ,self.p[1] - 1.5*self.radius),
			    (self.v[0] + SHOT_SPEED      ,self.v[1] - 3))
			Shot("shot.png",
			    (self.p[0] - 1.5*self.radius ,self.p[1] + 1.5*self.radius),
			    (self.v[0] - SHOT_SPEED      ,self.v[1] + 3))
			Shot("shot.png",
			    (self.p[0] - 1.5*self.radius ,self.p[1] - 1.5*self.radius),
			    (self.v[0] - SHOT_SPEED      ,self.v[1] - 3))

	def rotate(self,deg):
		"Rotates the ship image"
		self.angle = (self.angle + deg) % 360.0

	def shoot(self):
		"shoot a missile"
		tmp_thrustvec = self.thrustvec() # I use it twice, so I calculate it once
		self.cantshoot = SHOT_DELAY
		Shot("shot.png",
		    (self.p[0] + 1.5*self.radius * tmp_thrustvec[0],self.p[1] + 1.5*self.radius * tmp_thrustvec[1]),
		    (self.v[0] + SHOT_SPEED      * tmp_thrustvec[0],self.v[1] + SHOT_SPEED      * tmp_thrustvec[1]))

### End class Ship


class Shot(Body):
	"""Shot object."""
	def __init__(self,img_filename,p,v=(0,0)):
		Body.__init__(self,img_filename,p,v)
		self.timeleft = SHOT_LIFESPAN; # Why is there a semicolon here? I'm scared to delete it.

# Should I really be killing shots, or just putting them out of the way until one needs to be born?

	def update(self):
		# Shots live for a limited time, so update decrements their mortal coil.
		self.timeleft = self.timeleft - 1
		if self.timeleft > 0: Body.update(self)
		else:
			explosions.add(Explosion(self.p))
			self.kill()

### End class Shot


class Flame(pygame.sprite.Sprite):
	"What comes out of the rockets"

	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("flame.png")

### End class Flame


class Explosion(pygame.sprite.Sprite):
	""
	def __init__(self,p):
		pygame.sprite.Sprite.__init__(self)
		self.image, self.rect = load_image("flame.png")
		self.timeleft = 10
		self.rect.center = p

	def update(self):
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
	"Displays level of Energy, Shield, etc. for each ship"

	def __init__(self,rectangle,maximum,value=None):
		self.original_r = rectangle
		self.r = rectangle.move(0,0) # This is the easiest way I could think of to copy a rectangle. Lame.
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

	def draw(self,screen): pygame.draw.rect(screen,(255,255,255),self.r,1)

### End class Meter

def main():
	"""this function is called when the program starts.
	   It initializes everything it needs, then runs in
	   a loop until the function returns."""

	#Initialize Everything
	pygame.init()
	if not SOUND: pygame.mixer.quit()
	screen = pygame.display.set_mode(WINDOW_SIZE)
	pygame.display.set_caption('Spacewar')

	# Create and display the backgound
	background = pygame.Surface(screen.get_size())
	background = load_image("starfield.jpg")[0]
	screen.blit(background, (0, 0))
	pygame.display.flip()

	### Prepare Game Objects
	clock = pygame.time.Clock()
	soundplay["drip"]  = load_sound('drip.wav')
	soundplay["bam"]   = load_sound('bam.wav')
	soundplay["bonk"]  = load_sound('bonk.wav')
	soundplay["doink"] = load_sound('doink.wav')
	ship1 = Ship("ship.png",(200,200),(-3,3))
	if SUN: Sun("ball.png",(400,300))

#Main Loop
	while 1:
		clock.tick(60)

		#Handle Input Events
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE): return
			keystate = pygame.key.get_pressed()
		direction = keystate[SHIP1_LEFT_KEY] - keystate[SHIP1_RIGHT_KEY]
		if direction: ship1.rotate(SHIP_ROTATE * direction)
		if keystate[SHIP1_THRUST_KEY]:
			ship1.thrust = 1
			flames.add(ship1.flame)
		else:
			ship1.thrust = 0
			flames.remove(ship1.flame)
		if keystate[SHIP1_SHOOT_KEY]:
			if not ship1.cantshoot: ship1.shoot()

		# Collision detection... I know, I know, I should extend the Sprite one.

		# Okay, this code is gruesome. But it has to be done to keep from testing
		# both x.intersects(y) and y.intersects(x)-- not to mention x.intersects(x)!
		for i in xrange(len(bodys.sprites()) - 1 ):
			for j in xrange(i + 1,len(bodys.sprites())):
				if bodys.sprites()[i].intersects(bodys.sprites()[j]):
					bodys.sprites()[i].collide(bodys.sprites()[j])
		# Sprites should only be kill()ed in their updates-- if they're killed in above collision, we get a nasty error.


		# The beauty here is that extremely close objects have no pull, so it's okay that x pulls x sometimes.
		# And, unlike above, we want both x pulling y and y pulling x. So the code is (a lot) prettier.

		#for x in bodys.sprites():
		#	for y in bodys.sprites():
		#		x.pulledby(y)

		# Uglier (faster?) map() version:

		for x in bodys.sprites():
			map(x.pulledby,bodys.sprites())

		# update: change velocities according to accelerations, postitions according to velocities, etc.
		# flames and meters don't need to be updated-- Ship.update() handles it when necessary.
		bodys.update()
		explosions.update()

		# Draw sprites, meters
		for ship in ships.sprites(): ship.meter.draw(screen) # Draw meters
		flames.draw(screen)
		bodys.draw(screen)
		explosions.draw(screen)

		# Paste it onto the screen
		pygame.display.flip()

		# Clear sprites, meters
		for ship in ships.sprites(): ship.meter.clear(screen,background) # Clear meters
		flames.clear(screen,background)
		bodys.clear(screen,background)
		# explosions.clear(screen,background)
		screen.blit(background, (0, 0)) # Slower, but more complete

if __name__ == '__main__': main()
#Game Over
