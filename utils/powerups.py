import numpy as np
import pygame as pg
import itertools
from utils import misc


class Powerup(pg.sprite.Sprite):

    def __init__(self, fps, alive_time):
        super().__init__()
        self.fps = fps
        self.image = None
        self.timer = None
        self.alive_time = alive_time

    def update(self, player, players):
        if self.timer is None:
            self.transform(player, players)
            self.timer = self.alive_time

        elif self.timer > 0:
            self.timer -= 1/self.fps

        if self.timer <= 0:
            self.inv_transform(player, players)
            self.kill()

    def transform(self, player, players):
        pass

    def inv_transform(self, player, players):
        pass


class SelfSpeedUp(Powerup):

    SPEED_FACTOR = 2
    ALIVE_TIME = 5

    def __init__(self, fps):
        super().__init__(fps, self.ALIVE_TIME)

    def transform(self, player, players):
        player.velocity *= self.SPEED_FACTOR

    def inv_transform(self, player, players):
        player.velocity /= self.SPEED_FACTOR



