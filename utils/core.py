import numpy as np
import pygame as pg

from utils import misc

# Define game constants
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 30


class Game:

    def __init__(self, player_dicts):
        self.board = Board()
        self.clock = pg.time.Clock()
        self.going = True
        self.is_paused = False
        self.players = [Player(self.board.play_area, **player_dict) for player_dict in player_dicts]

    def _init_round(self):
        self.board.set_play_area(reset_trails=True)

        for player in self.players:
            player.reset()
        self.players_group = pg.sprite.Group(self.players)
        self.trail_group = pg.sprite.Group()

        self.round_over = False
        self.is_paused = True

        # Do 5 game steps to draw the initial player positions
        for i in range(5):
            self._game_step(True)
        pg.display.update()

    def _handle_game_state(self):
        self.clock.tick(FPS)

        for event in pg.event.get():
            self._pause_state_machine(event)

            # Check for KEYDOWN event
            if event.type == pg.KEYDOWN:
                # If the Esc key is pressed, then exit the main loop
                if event.key == pg.K_ESCAPE:
                    self.going = False

            # Check for QUIT event. If QUIT, then set running to false.
            elif event.type == pg.QUIT:
                self.going = False

    def _game_step(self, freeze_direction=False):
        # Move players
        self.players_group.update(self.board.trails, self.board.trails_mask)

        # Change players movement direction
        if not freeze_direction:
            for player in self.players_group:
                player.change_direction()

        # Update screen
        self.board.set_play_area()
        self.board.set_score_board(self.players)
        self.players_group.draw(self.board.play_area)
        self.board.blit_background()

        # Check if only a single player remains
        if len(self.players_group) == 1:
            self.round_over = True

    def _round(self):
        self._init_round()

        while not self.round_over:
            self._handle_game_state()

            # Check if paused/going
            if not self.going:
                break
            if self.is_paused:
                continue

            self._game_step()
            pg.display.update()

    def main(self):
        while self.going:
            self._round()
            self.is_paused = True

            while self.going and self.is_paused:
                self._handle_game_state()

        pg.quit()

    def _pause_state_machine(self, event):
        if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            self.is_paused = not self.is_paused


class Board:
    PLAY_AREA_RECT = pg.rect.Rect(20, 20, 1540, 1040)
    SCORES_AREA_RECT = pg.rect.Rect(PLAY_AREA_RECT.left + PLAY_AREA_RECT.width + 40,
                                    PLAY_AREA_RECT.top, 300, PLAY_AREA_RECT.height)

    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SCALED)
        self.background = pg.Surface(self.screen.get_size()).convert()
        self.play_area = self.background.subsurface(self.PLAY_AREA_RECT)
        self.trails = self.play_area.copy()
        self.trails_mask = None

        self._init_score_board()

    def _init_score_board(self):
        self.score_board = self.background.subsurface(self.SCORES_AREA_RECT)

        self.score_title_font = pg.freetype.SysFont('Arial', 36, bold=True)
        self.score_font = pg.freetype.SysFont('Arial', 24, bold=True)

    def set_score_board(self, players):
        self.score_board.fill('Black')

        score_board_rect = self.score_board.get_rect()
        pg.draw.lines(self.score_board, 'white', True, [score_board_rect.topleft, score_board_rect.topright,
                                                        score_board_rect.bottomright, score_board_rect.bottomleft], 5)

        title_text = f'First to {10*(len(players)-1)} wins!'
        dst = (10, 100)
        dst = misc.text_wrap(self.score_board, title_text, self.score_title_font, dst, 'White', 'Black')

        for player in sorted(players, key=lambda p: p.score):
            score_text = f'{player.name}: {player.score}'
            dst = misc.text_wrap(self.score_board, score_text, self.score_font, dst, player.color, 'Black')

    def set_play_area(self, reset_trails=False, draw_borders=True):
        self.play_area.fill((0, 0, 0))
        if reset_trails:
            self.trails = self.play_area.copy()
        else:
            self.play_area.blit(self.trails, (0, 0))

        if draw_borders:
            rect = self.play_area.get_rect()
            pg.draw.lines(self.play_area, 'yellow', True, [rect.topleft, rect.topright,
                                                           rect.bottomright, rect.bottomleft], 5)

        self.trails_mask = pg.mask.from_threshold(self.trails, (0, 0, 0, 255), (1, 1, 1, 255))
        self.trails_mask.invert()

    def blit_background(self):
        self.screen.blit(self.background, (0, 0))


class Player(pg.sprite.Sprite):
    DEFAULT_WIDTH = 7  # Pixels
    ROTATION_ANGLE = 3  # Degrees
    INITIAL_SPEED = 3  # Pixels
    TRAIL_PIXEL_DELAY = 5
    EXPECTED_TIME_BETWEEN_HOLES = 4  # Seconds
    HOLE_COOLOFF = 2  # Seconds
    HOLE_TIME_RANGE = (0.2, 0.3)  # Seconds

    def __init__(self, play_area, key_bindings_dict, color, name):
        super().__init__()

        # Init vars
        self.score = 0
        self.play_area = play_area
        self.key_bindings_dict = key_bindings_dict
        self.color = color
        self.name = name

        self.reset()

    def reset(self):

        self.active_powerups = []

        self.hole_cooloff_timer = self.HOLE_COOLOFF + np.random.exponential(FPS * (self.EXPECTED_TIME_BETWEEN_HOLES
                                                                                   - self.HOLE_COOLOFF)) / FPS
        self.hole_draw_timer = None
        self.is_hole_being_drawn = False

        self.velocity = self.INITIAL_SPEED * pg.math.Vector2([1, 0]).rotate(np.random.rand(1)*360)
        self.width = self.DEFAULT_WIDTH

        self.out_of_bounds = False
        self.source_trail_point = None

        self.image = pg.transform.scale(pg.image.load("../sprites/player.png").convert_alpha(),
                                        (self.width, self.width))
        self.image.set_colorkey((255, 255, 255), pg.RLEACCEL)
        player_rect_bounds = [[30, self.play_area.get_rect().width - 30],
                              [30, self.play_area.get_rect().height - 30]]
        self.rect = self.image.get_rect(center=(np.random.randint(*player_rect_bounds[0]),
                                                np.random.randint(*player_rect_bounds[1])))
        self.rect_center_float = self.rect.center  # To be used when the velocity is not an integer
        self.mask = pg.mask.from_surface(self.image)

    def change_direction(self):
        held_keys = pg.key.get_pressed()
        for key, direction in self.key_bindings_dict.items():
            if held_keys[key]:
                if direction is "left":
                    self.velocity.rotate_ip(-self.ROTATION_ANGLE)
                else:
                    self.velocity.rotate_ip(self.ROTATION_ANGLE)

    def update(self, trails, trails_mask):
        self._update_hole_stats()

        self.rect_center_float += self.velocity
        movement_vector = self.rect_center_float - self.rect.center
        movement_vector = pg.math.Vector2(list(np.round(movement_vector[:])))
        self.rect.move_ip(movement_vector)

        self._check_collisions(trails_mask)
        if self._check_death():
            self.kill()

        if not self.is_hole_being_drawn and self.source_trail_point is not None:
            dest_trail_point = self._calc_drawing_point(movement_vector)
            self._calc_drawing_point(movement_vector)
            self._draw_trail(trails, dest_trail_point)
        else:
            self.source_trail_point = self._calc_drawing_point(movement_vector)

    def _draw_trail(self, trails, dest_trail_point):
        if (dest_trail_point - self.source_trail_point).length_squared() >= self.TRAIL_PIXEL_DELAY ** 2:
            pg.draw.line(trails, self.color, self.source_trail_point, dest_trail_point, self.width)
            self.source_trail_point = dest_trail_point

    def _calc_drawing_point(self, movement_vector):
        radius_vec = self.rect.width//2 * movement_vector.normalize()
        radius_vec.x = np.trunc(radius_vec.x) + 2*np.sign(radius_vec.x)
        radius_vec.y = np.trunc(radius_vec.y) + 2*np.sign(radius_vec.y)
        return pg.math.Vector2(self.rect.center) - radius_vec

    def _check_death(self):
        return self.trail_collision or self.out_of_bounds

    def _check_collisions(self, trails_mask):
        try:
            self.trail_collision = trails_mask.overlap_area(self.mask, self.rect.topleft) > 0
        except IndexError:
            self.trail_collision = True
        self.out_of_bounds = not self.play_area.get_rect().contains(self.rect)

    def _update_hole_stats(self):
        if not self.is_hole_being_drawn:
            self.hole_cooloff_timer -= 1 / FPS
            if self.hole_cooloff_timer <= 0:
                self.is_hole_being_drawn = True
                self.hole_draw_timer = np.random.uniform(*self.HOLE_TIME_RANGE)
        else:
            self.hole_draw_timer -= 1 / FPS
            if self.hole_draw_timer <= 0:
                self.is_hole_being_drawn = False
                self.hole_cooloff_timer = self.HOLE_COOLOFF + np.random.exponential(FPS *
                                                                                    (self.EXPECTED_TIME_BETWEEN_HOLES
                                                                                     - self.HOLE_COOLOFF)) / FPS


class Powerup:
    def __init__(self, powerup_type):
        self.powerup_type = powerup_type


if __name__ == "__main__":

    def set_key_bindings(keys):
        directions = ['left', 'right']
        keys = [pg.key.key_code(key) for key in keys]
        return dict(zip(keys, directions))

    player1_dict = {'key_bindings_dict': set_key_bindings(['q', 'w']), 'color': 'red', 'name': 'fred'}
    player2_dict = {'key_bindings_dict': set_key_bindings(['o', 'p']), 'color': 'blue', 'name': 'bluebell'}
    player_dicts = [player1_dict, player2_dict]

    game = Game(player_dicts)
    game.main()
