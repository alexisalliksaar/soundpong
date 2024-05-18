import math
import random
from queue import Queue

import pygame
import pygame.gfxdraw

from sound_resolver import start_recording, stop_recording

BALL_RECT_KEYWORD = "ball_rect"
AI_DIFFICULTY_KEYWORD = "ai_difficulty"
AI_PLAYER_RECT_KEYWORD = "ai_player_rect"
AI_EASY = "EASY"
AI_MEDIUM = "MEDIUM"
AI_HARD = "HARD"

min_frequency = None
max_frequency = None
device_id = None
ai_difficulty = None  # EASY, MEDIUM or HARD


def ai_movement(args):
    ball_rect = args[BALL_RECT_KEYWORD]
    ai_diff = args[AI_DIFFICULTY_KEYWORD]
    ai_rect = args[AI_PLAYER_RECT_KEYWORD]

    # et vastane ei teeks liigutusi, kui ta on palliga samal kõrgusel
    if ball_rect.center[1] - 10 < ai_rect.center[1] < ball_rect.center[1]:
        return 0, True

    # leian kuhu suunas vastane peab liikuma
    if ai_rect.center[1] < ball_rect.center[1]:
        direction_up = False
    else:
        direction_up = True

    # Arvutan vastase kiirust, tuginedes vastase baaskiirusele ja tema kaugusele võrreldes palli kõrgusega
    if ai_diff == AI_EASY:
        speed = 0.2 + 0.5 * (abs(ai_rect.center[1] - ball_rect.center[1]) / (HEIGHT - (2 * PADDING_SIZE)))
        return speed, direction_up

    if ai_diff == AI_MEDIUM:
        speed = 0.5
        return speed, direction_up
    if ai_diff == AI_HARD:
        speed = 0.6 + 0.4 * (abs(ai_rect.center[1] - ball_rect.center[1]) / (HEIGHT - (2 * PADDING_SIZE)))
        return speed, direction_up


QUEUE_KEYWORD = "queue"


def player_movement(args):
    freq_queue = args[QUEUE_KEYWORD]
    if freq_queue.empty():
        return 0, True
    freq = freq_queue.get()
    print(freq)
    if freq == -1:
        return 0, True
    else:
        # kuna tajume heli logaritmiliselt, töötlen logaritme
        # kasutan konfis määratud max-i ja min-i
        log_max = math.log(max_frequency)
        log_min = math.log(min_frequency)
        log_freq = math.log(freq)
        center = ((log_max - log_min) / 2) + log_min
        # print(log_max)
        # print(log_min)
        # print(log_freq)
        # print("CENTER:", center)
        # kasutaja baas kiirus + tema hääle erinevus keskmisest hääle kõgusest
        return 0.3 + 0.7 * (abs(log_freq - center) / (center - log_min)), log_freq >= center


def load_conf():
    global min_frequency, max_frequency, device_id, ai_difficulty
    with open("SoundPong.conf", "r") as conf_file:
        lines = conf_file.readlines()
        key_dict = {}
        for line in lines:
            key, value = line.strip().split("=")
            key_dict[key] = value
        min_frequency = int(key_dict[MIN_FREQUENCY_KEYWORD])
        max_frequency = int(key_dict[MAX_FREQUENCY_KEYWORD])
        device_id = int(key_dict[DEVICE_ID_KEYWORD])
        ai_difficulty = key_dict[AI_DIFFICULTY_KEYWORD]


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
HEIGHT = 1000
WIDTH = 1000
BALL_RADIUS = 10
YELLOW = (255, 255, 102)
GREEN = (0, 255, 0)

PADDING_SIZE = 20

BALL_IMG = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
pygame.gfxdraw.aacircle(BALL_IMG, BALL_RADIUS, BALL_RADIUS, BALL_RADIUS, WHITE)
pygame.gfxdraw.filled_circle(BALL_IMG, BALL_RADIUS, BALL_RADIUS, BALL_RADIUS, WHITE)
BALL_SPEED = 8
BALL_RANDOMNESS = 30

PLAY_WITH_KEYBOARD = False
# ball movement is represented as an angle: 0 -> up, 90 -> right ...
allowed_ball_movements = [x for x in range(30, 151)] + \
                         [x for x in range(210, 331)]  # Want the ball to keep moving horizontally

horizontal_movement_angles = [x for x in range(75, 106)] + \
                             [x for x in range(255, 286)]# but don't want to set movement angle too horizontal after colliding with top or bottom wall

MIN_FREQUENCY_KEYWORD = "min_frequency"
MAX_FREQUENCY_KEYWORD = "max_frequency"
DEVICE_ID_KEYWORD = "device_id"


class Ball(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = BALL_IMG
        self.rect = self.image.get_rect(center=(WIDTH / 2, HEIGHT / 2))
        self.movement_angle = allowed_ball_movements[random.randint(0, len(allowed_ball_movements) - 1)]
        self.player_collision_grace_period = 0
        self.wait_for_start = 60

    def change_angle(self, dest, allow_horizontal=True):
        suitable_angles = list(
            filter(lambda x: True if (dest - BALL_RANDOMNESS <= x <= dest + BALL_RANDOMNESS) else False,
                   allowed_ball_movements))
        if not allow_horizontal:
            suitable_angles = [x for x in suitable_angles if x not in horizontal_movement_angles]

        if len(suitable_angles) == 0:
            self.movement_angle = dest
            return
        self.movement_angle = suitable_angles[random.randint(0, len(suitable_angles) - 1)]

    def update(self):
        if self.wait_for_start > 0:
            self.wait_for_start -= 1
            return
        if self.rect.top < PADDING_SIZE:
            if self.movement_angle < 90:
                entering_angle = 90 - self.movement_angle
            else:
                entering_angle = 270 - self.movement_angle
            self.change_angle(self.movement_angle + (2 * entering_angle), False)
        if self.rect.bottom > HEIGHT - PADDING_SIZE:
            if self.movement_angle < 180:
                entering_angle = 90 - self.movement_angle
            else:
                entering_angle = 270 - self.movement_angle
            self.change_angle(self.movement_angle + (2 * entering_angle), False)

        self.rect.x += math.sin(math.radians(self.movement_angle)) * BALL_SPEED
        self.rect.y -= math.cos(math.radians(self.movement_angle)) * BALL_SPEED
        if self.rect.x <= 0 or self.rect.x + 2 * BALL_RADIUS >= WIDTH:
            self.rect = self.image.get_rect(center=(WIDTH / 2, HEIGHT / 2))
            self.movement_angle = allowed_ball_movements[random.randint(0, len(allowed_ball_movements) - 1)]

    def resolve_player_collision(self, players):
        if self.player_collision_grace_period > 0:
            self.player_collision_grace_period -= 1
            return
        for player1 in players:
            if self.rect.colliderect(player1.rect):
                entering_angle = 360 - self.movement_angle
                self.change_angle(entering_angle)
                self.player_collision_grace_period = 5


class Player(pygame.sprite.Sprite):
    PLAYER_HEIGHT = 100
    PLAYER_WIDTH = 30

    def __init__(self, max_speed, update_resolver, ai_player):
        pygame.sprite.Sprite.__init__(self)
        self.max_speed = max_speed
        self.image = pygame.Surface((Player.PLAYER_WIDTH, Player.PLAYER_HEIGHT))
        self.image.fill(WHITE)
        self.update_resolver = update_resolver
        self.moving_up = True
        if ai_player:
            x_point = WIDTH - Player.PLAYER_WIDTH
        else:
            x_point = Player.PLAYER_WIDTH
        self.rect = self.image.get_rect(center=(x_point, (HEIGHT / 2)))
        self.movement_speed = 0  # percentage of top speed

    def resolve_movement(self, **kwargs):
        self.movement_speed, self.moving_up = self.update_resolver(kwargs)

    def update(self):
        if self.moving_up:
            self.rect.y -= self.movement_speed * self.max_speed
        else:
            self.rect.y += self.movement_speed * self.max_speed
        self.rect.y = max(PADDING_SIZE, min(HEIGHT - PADDING_SIZE - Player.PLAYER_HEIGHT, self.rect.y))


KEYBOARD_UP_KEYWORD = "keyboard_up"


def keyboard_input(args):
    if args[KEYBOARD_UP_KEYWORD] is None:
        return 0, True
    if args[KEYBOARD_UP_KEYWORD]:
        return 1, True
    else:
        return 1, False


FPS = 30

if __name__ == '__main__':

    load_conf()
    pygame.init()

    all_sprites = pygame.sprite.Group()
    ball = Ball()
    all_sprites.add(ball)

    if PLAY_WITH_KEYBOARD:
        player = Player(10, keyboard_input, False)
    else:
        player = Player(25, player_movement, False)
    ai_player = Player(10, ai_movement, True)

    all_sprites.add(player)
    all_sprites.add(ai_player)
    player_sprites = [ai_player, player]

    display_size = (WIDTH, HEIGHT)

    display = pygame.display.set_mode(display_size)
    pygame.display.set_caption("SoundPong")

    clock = pygame.time.Clock()

    running = True
    KEYBOARD_UP = None

    if not PLAY_WITH_KEYBOARD:
        frequency_queue = Queue()
        start_recording(frequency_queue, configured_min=min_frequency, configured_max=max_frequency, mic_id=device_id)

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if PLAY_WITH_KEYBOARD and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        KEYBOARD_UP = True
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        KEYBOARD_UP = False
                if PLAY_WITH_KEYBOARD and event.type == pygame.KEYUP:
                    if event.key == pygame.K_w or event.key == pygame.K_UP or event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        KEYBOARD_UP = None

            if PLAY_WITH_KEYBOARD:
                player.resolve_movement(keyboard_up=KEYBOARD_UP)
            else:
                player.resolve_movement(queue=frequency_queue)

            ai_player.resolve_movement(ball_rect=ball.rect, ai_difficulty=ai_difficulty, ai_player_rect=ai_player.rect)
            ball.resolve_player_collision(player_sprites)
            all_sprites.update()

            display.fill(BLACK)
            pygame.draw.rect(display, GREEN, [0, 0, WIDTH, PADDING_SIZE])
            pygame.draw.rect(display, GREEN, [0, HEIGHT - PADDING_SIZE, WIDTH, 30])
            all_sprites.draw(display)
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        if not PLAY_WITH_KEYBOARD:
            stop_recording()
        pygame.quit()
        # sys.exit()
