
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
        """Sun should have a mass greater than zero"""
        self.assertGreater(self.testsun.mass, 0)

    def tearDown(self):
        pygame.quit()

class TestShip(unittest.TestCase):

    def setUp(self):
        pygame.init()
        testgamestate = GameState()
        screen = pygame.display.set_mode((DISP_WIDTH, DISP_HEIGHT))
        self.testsun = Sun(testgamestate, load_image("ball.png"), (400,300))

    def test_ship_cant_shoot_after_death(self):
        """Ship should be unable to fire after it dies"""
        pass

    def tearDown(self):
        pygame.quit()

if __name__ == "__main__":
    unittest.main()
