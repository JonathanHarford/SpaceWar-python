import pygame
from spacewar_func import *
from numpy import array

class Body(pygame.sprite.Sprite):
    "Ships, shots, suns are all subclasses of this."

    def __init__(self,img,p,v=(0,0)):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = img
        ### self.area = pygame.Rect(0,0,DISP_WIDTH,DISP_HEIGHT)
        self.rect.center = p
        self.p = array(self.rect.center) # position
        self.v = array(v)                # velocity
        ### "a" = acceleration. Each tick it starts at 0,0 then gets changed by thrust & gravity, then gets added to "v"
        self.a = array((0,0))
        self.radius = self.rect.height/2
        self.mass = 1.0

    def speed_sqrd(self):
        "The speed of the Body, squared."
        return self.v[0]**2 + self.v[1]**2 # Why not return the speed? Because math.sqrt() is relatively expensive.

    def intersects(self,b):
        "Answers the question: Does this body intersect the body b?"
        return dist_sqrd(self.p,b.p) <= (self.radius + b.radius)**2

    # Well, the gravity's nice, but the orbits are like spirographs.
    def pulledby(self,b,force):
        "Alters this body's acceleration based on the distance and mass of body b. (I.e., gravity)"
        if self.intersects(b): return # To keep Bodys from jamming against each other (I think). Also escapes when self=b
        r =  b.p - self.p
        gravity = force*b.mass/dist_sqrd((0,0),r)
        self.a = self.a + gravity*r

    def update(self, area, is_walls):
        self.v = self.v + self.a
        self.p = self.p + self.v

        if is_walls:
            if self.p[0] - self.radius < area.left:
                self.v[0] = -self.v[0]
                self.p[0] = 2*self.radius-self.p[0]
            elif self.p[0] + self.radius > area.right:
                self.v[0] = -self.v[0]
                self.p[0] = 2*area.right - 2*self.radius - self.p[0]
            elif self.p[1] - self.radius < area.top:
                self.v[1] = -self.v[1]
                self.p[1] = 2*self.radius-self.p[1]
            elif self.p[1] + self.radius > area.bottom:
                self.v[1] = -self.v[1]
                self.p[1] = 2*area.bottom - 2*self.radius - self.p[1]
        else:   ### Toroidal universe (not very precise)
            if   self.p[0] < area.left:   self.p[0] = area.right
            elif self.p[0] > area.right:  self.p[0] = area.left
            if   self.p[1] < area.top:    self.p[1] = area.bottom
            elif self.p[1] > area.bottom: self.p[1] = area.top

        ### Speed limit
        if self.speed_sqrd() > MAXSPEED**2: self.v = normalize(self.v,MAXSPEED)

        self.a = 0 * self.a # Remove all acceleration, for this tick

        self.rect.center = self.p # Update where the picture is blitted

    def collide(self,b):
        """A collision between two Bodys, self and b."""
        # This code is not in the class definitions of Ship, Sun, and Shot because
        # A) I wanted to keep it in one place, and B) I didn't want to have to duplicate
        # code: ship.collide(shot) should be the same as shot.collide(ship).

        if isinstance(self,Sun):
            if isinstance(b,Sun):
                soundplay["bonk"]()
                bounce(self,b)
            if isinstance(b,Ship):
                soundplay["bonk"]()
                bounce(self,b)
                b.meter.decrease(CRASH_PAIN)
            if isinstance(b,Shot):
                soundplay["drip"]()
                b.timeleft = 0
        if isinstance(self,Ship):
            if isinstance(b,Sun):
                soundplay["bonk"]()
                bounce(self,b)
                self.meter.decrease(CRASH_PAIN)
            if isinstance(b,Ship):
                soundplay["bam"]()
                bounce(self,b)
            if isinstance(b,Shot):
                soundplay["doink"]()
                b.timeleft = 0
                self.meter.decrease(SHOT_PAIN)
        if isinstance(self,Shot):
            if isinstance(b,Sun): soundplay["drip"]()
            if isinstance(b,Ship):
                soundplay["doink"]()
                b.meter.decrease(SHOT_PAIN)
            # if isinstance(b,Shot): tiny_boom.play()
            self.timeleft = 0

