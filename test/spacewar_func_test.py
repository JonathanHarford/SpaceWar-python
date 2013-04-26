
# test/test_core/parser_test.py

import unittest
import sys

sys.path.append("../")


from spacewar_func import *  # My Spacewar functions

class TestSun(unittest.TestCase):

    def setUp(self):
        pygame.init()
        testgamestate = GameState()
        screen = pygame.display.set_mode((DISP_WIDTH, DISP_HEIGHT))
        self.testsun = Sun(testgamestate, load_image("ball.png"), (400,300))

    def test_sun_has_mass_by_default(self):
        print(self.testsun.mass)
        self.assertGreater(self.testsun.mass, 0)

    def tearDown(self):
        pygame.quit()

##class TestShip(unittest.TestCase):
##
##    def setUp(self):
##        testgamestate = GameState()
##        testship = Ship(testgamestate, load_image(r"..\data\ship.png"), (200,200), (-3,3))
##
##    def test_ship_cant_shoot_after_death(self):


if __name__ == "__main__":
    unittest.main()
