#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      jjh_000
#
# Created:     05/04/2013
# Copyright:   (c) jjh_000 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

DISP_WIDTH, DISP_HEIGHT = (800, 600)
SOUND = 1
FPS = 30  # frames per second

WALLS = 1           # Does the universe have bouncy walls? Or is it toroidal?
GRAV_CONST = 0.01   # I like to make this very low, and the sun(s) massive.

SHIP1_THRUST_KEY = K_w
SHIP1_LEFT_KEY =   K_a
SHIP1_RIGHT_KEY =  K_d
SHIP1_SHOOT_KEY =  K_q

SHIP2_THRUST_KEY = K_i
SHIP2_LEFT_KEY   = K_j
SHIP2_RIGHT_KEY  = K_l
SHIP2_SHOOT_KEY  = K_k

SUN = 2500          # Mass of Sun. 0 = no sun
MAXSPEED = 30
SHIP_ROTATE = 10  # How many degrees a ship can turn in a tick.
THRUST = 0.1
START_ENERGY = 10  # Eventually, 100
CRASH_PAIN = 5
SHOT_SPEED = 6
SHOT_LIFESPAN = 250
SHOT_DELAY = 15
SHOT_PAIN = 5


def main():
    pass

if __name__ == '__main__':
    main()
