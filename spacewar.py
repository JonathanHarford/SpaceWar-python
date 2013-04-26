#!/usr/bin/env python

"""
Requires-Python: 2.7

Spacewar! is one of the earliest known digital computer games. It is a
two-player game, with each player taking control of a spaceship and attempting
to destroy the other.

A star in the centre of the screen pulls on both ships and requires maneuvering
to avoid falling into it.

TODO:
Create Gamestate module?
Abstract code in main loop into functions.
Load all images at beginning
Ditch numpy?
ships explode
2nd ship
fullscreen mode
title/menu
AI
Make ships reflect sun
ship mouse-controllable
"""

### Import Modules

import pygame


# Numeric arrays are elegant: 2*[2,4] == [4,8] rather than 2*[2,4] == [2,4,2,4]
# I don't remember why I'm not just using plain arrays. Speed? Oh well.

from spacewar_func import *  # My Spacewar functions


### Initialization

if not pygame.font:
    print 'Warning, fonts disabled'
if not pygame.mixer:
    print 'Warning, sound disabled'

# Everyone can play sounds! (I know, sloppy.)



def main():
    """this function is called when the program starts.
       It initializes everything it needs, then runs in
       a loop until the function returns."""

    #Initialize Everything
    pygame.init()
    gamestate = GameState()
    if not SOUND:
        pygame.mixer.quit()
    screen = pygame.display.set_mode((DISP_WIDTH, DISP_HEIGHT))
    pygame.display.set_caption('Spacewar')

    # Create and display the backgound
    background = pygame.Surface(screen.get_size())
    background = load_image("starfield.jpg")[0]
    screen.blit(background, (0, 0))
    pygame.display.flip()

    ### Prepare Game Objects
    clock = pygame.time.Clock()
    gamestate.soundplay["drip"]  = load_sound('drip.wav')
    gamestate.soundplay["bam"]   = load_sound('bam.wav')
    gamestate.soundplay["bonk"]  = load_sound('bonk.wav')
    gamestate.soundplay["doink"] = load_sound('doink.wav')
    ship1 = Ship(gamestate,load_image("ship.png"),(200,200),(-3,3))
    if SUN_MASS > 0: Sun(gamestate,load_image("ball.png"),(400,300))

    # Main Loop
    mainloop = True
    while mainloop:
        clock.tick(FPS)

        # Handle Input Events
        for event in pygame.event.get():
            if event.type == pygame.locals.QUIT or (event.type == pygame.locals.KEYDOWN and event.key == pygame.locals.K_ESCAPE):
                mainloop = False
            keystate = pygame.key.get_pressed()
        direction = keystate[SHIP1_LEFT_KEY] - keystate[SHIP1_RIGHT_KEY]
        if direction: ship1.rotate(SHIP_ROTATE * direction)
        if keystate[SHIP1_THRUST_KEY]:
            ship1.thrust = 1
            gamestate.flames.add(ship1.flame)
        else:
            ship1.thrust = 0
            gamestate.flames.remove(ship1.flame)
        if keystate[SHIP1_SHOOT_KEY]:
            if not ship1.cantshoot: ship1.shoot(gamestate)

        # This loop compares every unique pair of sprites once and only
        # once for collision detection. I suspect there's a more
        # elegant way to do it.
        for i in xrange(len(gamestate.bodys.sprites()) - 1 ):
            for j in xrange(i + 1,len(gamestate.bodys.sprites())):
                if gamestate.bodys.sprites()[i].intersects(gamestate.bodys.sprites()[j]):
                    gamestate.bodys.sprites()[i].collide(gamestate, gamestate.bodys.sprites()[j])
        # Sprites should only be kill()ed in their updates-- if they're killed
        # in above collision, we get a nasty error.


        # The beauty here is that extremely close objects have no pull, so it's okay that x pulls x sometimes.
        # And, unlike above, we want both x pulling y and y pulling x. So the code is prettier.

        for x in gamestate.bodys.sprites():
            map(x.pulledby,gamestate.bodys.sprites())

        # update: change velocities according to accelerations, postitions according to velocities, etc.
        # flames and meters don't need to be updated-- Ship.update() handles it when necessary.
        gamestate.bodys.update(gamestate)
        gamestate.explosions.update(gamestate)

        # Draw sprites, meters
        for ship in gamestate.ships.sprites():
            ship.meter.draw(screen) # Draw meters
        gamestate.flames.draw(screen)
        gamestate.bodys.draw(screen)
        gamestate.explosions.draw(screen)

        # Paste it onto the screen
        pygame.display.flip()

        # Clear sprites, meters
        for ship in gamestate.ships.sprites():
            ship.meter.clear(screen,background) # Clear meters
        gamestate.flames.clear(screen,background)
        gamestate.bodys.clear(screen,background)
        # explosions.clear(screen,background)
        screen.blit(background, (0, 0)) # Slower, but more complete



if __name__ == '__main__':
    main()
    pygame.quit() # Needed when running from IDLE or PyScripter

