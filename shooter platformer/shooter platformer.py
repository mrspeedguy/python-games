#init and import
import pygame
from pygame import mixer
import os
import random
import csv
import button 
pygame.init()
mixer.init
"""notes:
- game doneeeee"""
#screen sizing
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

#screen make
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("shooter game")

#set frame rate
clock = pygame.time.Clock()
fps = 60

#define game variables
GRAVITY = 0.75
SCROLL_THRESH = 200
GROUND_FRICTION = 0.2
BOUNCYNESS = 0.6
ROWS = 16
COLS = 150
TILE_SIZE = screen.get_height() // ROWS
TILE_TYPES = 21
screen_scroll = 0
bg_scroll = 0
start_game = False
start_intro = False
MAX_LEVElS = 3
level = 1
enemies_alive = 0

#define soldier action variables
moving_left = False
moving_right = False
shoot = False
throw_grenade = False
grenade_thrown = False
# debug variables
paused = False
show_all_hitboxes = False

#load music and sounds
pygame.mixer.music.load("shooter platformer/imports/audio/music2.mp3")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound("shooter platformer/imports/audio/jump.wav")
jump_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound("shooter platformer/imports/audio/shot.wav")
shot_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound("shooter platformer/imports/audio/grenade.wav")
grenade_fx.set_volume(0.5)

#load images
#buttons
start_img = pygame.image.load("shooter platformer/imports/img/start_btn.bmp").convert_alpha()
restart_img = pygame.image.load("shooter platformer/imports/img/restart_btn.bmp").convert_alpha()
exit_img = pygame.image.load("shooter platformer/imports/img/exit_btn.bmp").convert_alpha()

#bg
pine1_img = pygame.image.load("shooter platformer/imports/img/background/pine1.bmp").convert_alpha()
pine2_img = pygame.image.load("shooter platformer/imports/img/background/pine2.bmp").convert_alpha()
mountain_img = pygame.image.load("shooter platformer/imports/img/background/mountain.bmp").convert_alpha()
sky_img = pygame.image.load("shooter platformer/imports/img/background/sky_cloud.bmp").convert_alpha()

#tiles
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f"shooter platformer/imports/img/tile/{x}.bmp").convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

#bullet
bullet_img = pygame.image.load(f"shooter platformer/imports/img/icons/bullet.bmp").convert_alpha()

#grenade
grenade_img = pygame.image.load(f"shooter platformer/imports/img/icons/grenade.bmp").convert_alpha()

#pickup boxes
health_box_img = pygame.image.load(f"shooter platformer/imports/img/icons/health_box.bmp").convert_alpha()
ammo_box_img = pygame.image.load(f"shooter platformer/imports/img/icons/ammo_box.bmp").convert_alpha()
grenade_box_img = pygame.image.load(f"shooter platformer/imports/img/icons/grenade_box.bmp").convert_alpha()
#box dictionary
item_boxes = {
    "Health"    : health_box_img,
    "Ammo"      : ammo_box_img,
    "Grenade"   : grenade_box_img
}

#define colors
BG = (130, 225, 130)
RED = (255, 0, 0)
PINK = (235, 65, 54)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# tile hitbox style (less bold)
TILE_HITBOX_COLOR = (200, 70, 70)
TILE_HITBOX_WIDTH = 1

# Define fonts (cache to support multiple sizes)
font_cache = {}

def get_font(size=30, name="Futura"):
    key = (name, size)
    # return cached font if available
    if key in font_cache:
        return font_cache[key]
    # Try pygame.font (classic)
    try:
        pygame.font.init()
        f = pygame.font.SysFont(name, size)
        font_cache[key] = f
        return f
    except Exception:
        pass
    # Try pygame.freetype
    try:
        import pygame.freetype as ft
        try:
            f = ft.SysFont(name, size)
        except Exception:
            f = ft.Font(None, size)
        font_cache[key] = f
        return f
    except Exception:
        pass
    # Last resort: cache None to avoid repeated attempts
    font_cache[key] = None
    return None

# draw text
def draw_text(text, font_obj=None, text_col=RED, x=0, y=0):
    f = font_obj if font_obj is not None else get_font()
    if f is None:
        # font unavailable; silently skip drawing to avoid crashes
        return
    try:
        # Handle different render signatures:
        # - pygame.freetype.Font.render(text, fgcolor) -> (surface, rect)
        # - pygame.font.Font.render(text, antialias, color) -> surface
        try:
            res = f.render(text, text_col)
        except TypeError:
            # fallback to pygame.font.Font signature
            res = f.render(text, True, text_col)
        # unpack if needed
        if isinstance(res, tuple):
            surf = res[0]
        else:
            surf = res
        screen.blit(surf, (x, y))
    except Exception:
        # If something unexpected goes wrong drawing text, skip it
        return

#background update
def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5,0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

#reset level
def reset_level():

    #empty all
    enemy_group.empty()
    bullet_group.empty()
    explosion_group.empty()
    grenade_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    exit_group.empty()
    water_group.empty()
    global enemies_alive
    enemies_alive = 0
    #create empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    
    return data

#soldier class
class soldier(pygame.sprite.Sprite): 

    #initialize
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades): 
        pygame.sprite.Sprite.__init__(self)
        #shooting and grenades
        self.shoot_cooldown = 0
        self.ammo = ammo
        self.start_ammo = ammo
        self.grenades = grenades
        #damage/living
        self.alive = True
        self.health = 100
        self.max_health = self.health
        #player or enemy
        self.char_type = char_type
        #speed
        self.speed = speed
        #direction/jump
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        # jump helpers
        self.coyote_timer = 0
        self.jump_buffer_timer = 0
        #setup loading animation
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks ()
        animation_types = ["idle", "run", "jump", "death"]
        for animation in animation_types:

            #reset temporary list
            temp_list = []

            #count files in folder
            animation_path = f"shooter platformer/imports/img/{self.char_type}/{animation}"

            # get only .bmp files and sort them and get length
            frame_files = sorted([f for f in os.listdir(animation_path) if f.lower().endswith(".bmp")])

            #load images
            for filename in frame_files:
                full_path = os.path.join(animation_path, filename)
                img = pygame.image.load(full_path).convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)

            self.animation_list.append(temp_list)

        #set first image
        self.image = self.animation_list[self.action][self.frame_index]

        #hit box load
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        # per-instance hitbox display toggle
        self.show_hitbox = show_all_hitboxes

        #ai only variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

    #update
    def update(self):
        self.update_animation()
        self.check_alive()
        #update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    #movement
    def move(self, moving_left, moving_right):
        #reset movement variables
        screen_scroll = 0
        dx = 0 
        dy = 0

        #assign movement variables if moving left or right
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        
        #jump
        if self.jump and self.in_air == False:
            self.vel_y = -12
            jump_fx.play()
            self.jump = False
            self.in_air = True

        #calculate and apply jump forces
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        #check collision with world
        for tile in world.obstacle_list:
            #x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0

                #if ai hit wall turn
                if self.char_type == "enemy":
                    self.direction *= -1
                    self.move_counter = 0

            #y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy + 1, self.width, self.height):

                #check if below the ground i.e. jumping
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                    
                #check if above the ground i.e. falling
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
                    self.in_air = False

        #check if in water
        temporaryrect = self.rect.copy() 
        temporaryrect.y -= self.height
        if self.show_hitbox:
            pygame.draw.rect(screen, WHITE, temporaryrect, 1)
        for water in water_group:
            if water.rect.colliderect(temporaryrect):
                self.health = 0

        #check if hit exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False) and enemies_alive < 1:
            level_complete = True
        elif pygame.sprite.spritecollide(self, exit_group, False):
            draw_text("you need to kill more enemies to pass", ui_font, RED, 170, 0)
        print(enemies_alive)

        #check if off bottom of screen
        if self.rect.top > SCREEN_HEIGHT:
            self.health = 0

        #check if off side of screen
        if self.char_type == "player":
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        #update pos
        self.rect.x += dx
        self.rect.y += dy

        #update scroll based on player position
        if self.char_type == "player":
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < world.level_length * TILE_SIZE - SCREEN_WIDTH) or (self.rect.left < SCROLL_THRESH and bg_scroll > 0):
                self.rect.x -= dx
                screen_scroll = -dx
        
        return screen_scroll, level_complete

    #update action
    def update_action(self, new_action):
        #check if new action is different to previous one
        if new_action != self.action:
            self.action = new_action
            #reset action timer
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    #alive check
    def check_alive(self):
        #check dead
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)
            if self.char_type == "enemy":
                global enemies_alive
                enemies_alive -= 1

    #shoot bullet
    def shoot(self):
        #check cooldown and ammo
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            # reduce ammo once per shot
            self.ammo -= 1
            #sound
            shot_fx.play()
            #spawn bullet
            new_bullet = Bullet(self.rect.centerx + (0.55 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(new_bullet)

    #ai
    def ai(self):
        self.patrol_direction = self.direction

        #check alive
        if self.alive and player.alive:
            #check if want to idle
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)
                self.idling = True
                self.idling_counter = 50

            #check if player in sight
            if self.vision.colliderect(player.rect):
                # stop running
                self.update_action(0)

                #remeber old direction
                self.patrol_direction = self.direction
                
                # face player
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False
                
                # shoot
                self.shoot()
            
                #reset direction
                self.direction = self.patrol_direction

            #otherwise patrol
            else:
                #check not idling 
                if self.idling == False:
                    #move left and right 
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)
                    self.move_counter += 1
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                        
                #count down idling if idling
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

                #update ai vision
                self.vision.center = (self.rect.centerx +75 * self.direction, self.rect.centery)
                if self.show_hitbox:
                    pygame.draw.rect(screen, WHITE, self.vision, 1)
        
        #scroll
        self.rect.x += screen_scroll

    #animation update
    def update_animation(self):
        #time between transition
        ANIMATION_COOLDOWN = 100
        #update current image
        self.image = self.animation_list[self.action][self.frame_index]
        #check time after last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        #reset index after it animation end
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    #draw
    def draw(self):
        # compute on-screen rect
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)
        # draw hitbox if enabled for this instance (draw using on-screen rects)
        if getattr(self, "show_hitbox", False):
            pygame.draw.rect(screen, RED, self.rect, 1)
    
#world class
class World(): 

    #initialize
    def __init__(self):
        self.obstacle_list = []
        self.show_hitbox = show_all_hitboxes

    #process
    def process_data(self, data):
        self.level_length = len(data[0])
        #set variables so no local variables errors
        player = None
        health_bar = None
        #iterate through every value
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)#dirt
                    elif tile >= 9 and tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)#water
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)#decoration
                        decoration_group.add(decoration)
                    elif tile == 15:
                        player = soldier("player", x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5)#player
                        health_bar = HealthBar(10, 10, player.health, player.max_health)
                    elif tile == 16:
                        enemy = soldier("enemy", x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0)#enemy
                        enemy_group.add(enemy)
                        global enemies_alive
                        enemies_alive += 1
                    elif tile == 17:
                        item_box = ItemBox("Ammo", x * TILE_SIZE, y * TILE_SIZE)#ammo
                        item_box_group.add(item_box)
                    elif tile == 18:
                        item_box = ItemBox("Grenade", x * TILE_SIZE, y * TILE_SIZE)#grenade
                        item_box_group.add(item_box)
                    elif tile == 19:
                        item_box = ItemBox("Health", x * TILE_SIZE, y * TILE_SIZE)#health
                        item_box_group.add(item_box)
                    elif tile == 20:
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)#exit
                        exit_group.add(exit)
        return player, health_bar

    #draw
    def draw(self):
        for tile in self.obstacle_list:
            #shift tile
            tile[1][0] += screen_scroll
            #draw tile
            screen.blit(tile[0], tile[1])
            # draw hitbox if enabled for this instance
            if self.show_hitbox:
                pygame.draw.rect(screen, TILE_HITBOX_COLOR, tile[1], TILE_HITBOX_WIDTH)

#decoration class
class Decoration(pygame.sprite.Sprite):

    #initialize
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes 
        if self.show_hitbox:
            pygame.draw.rect(screen, RED, self.rect, 1)
    
    #update
    def update(self):
        self.rect.x += screen_scroll

#water class
class Water(pygame.sprite.Sprite):

    #initialize
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes 
        if self.show_hitbox:
            pygame.draw.rect(screen, RED, self.rect, 1)

    #update
    def update(self):
        self.rect.x += screen_scroll

        #hitboxes
        if self.show_hitbox:
            pygame.draw.rect(screen, RED, self.rect, 1)

#exit class
class Exit (pygame.sprite.Sprite):

    #initialize
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes
        if self.show_hitbox:
            pygame.draw.rect(screen, RED, self.rect, 1) 
        self.rect.x += screen_scroll

    #update
    def update(self):
        self.rect.x += screen_scroll
     
#item box class
class ItemBox(pygame.sprite.Sprite):

    #initialize
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes
    
    #update
    def update(self):
        #scroll
        self.rect.x += screen_scroll

        #check if player has picked up box
        if pygame.sprite.collide_rect(self, player):
            #check the box type
            if self.item_type == "Health":
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == "Ammo":
                player.ammo += 15
            elif self.item_type == "Grenade":
                player.grenades += 3

            #delete item box
            self.kill() 

#healthbar class
class HealthBar():

    #initialize
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    #draw
    def draw(self, health):
        #update and calculate health stuff
        self.health = health
        ratio = self.health / self.max_health
        #draw bar
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

#bullet class
class Bullet(pygame.sprite.Sprite):

    #initialize
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes
        self.direction = direction
    
    #update
    def update(self):
        #move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll

        #check if bullet is off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        #check collision with world
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        #check collision with characters
        #player
        if pygame.sprite.collide_rect(self, player):
            if player.alive:
                player.health -= 5
                self.kill()
        #enemy
        hit_enemies = pygame.sprite.spritecollide(self, enemy_group, False)
        for hit_enemy in hit_enemies:
            if hit_enemy.alive:
                hit_enemy.health -= 25
                self.kill()
                break

        if self.show_hitbox:
            pygame.draw.rect(screen, RED, self.rect, 1)

#grenade class
class Grenade(pygame.sprite.Sprite):

    #initialize
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self) 
        self.x = x
        self.y = y
        self.timer = 30
        self.bounce_counter = 0
        self.vel_y = -11
        self.true_dx = 0
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes
        self.direction = direction

    #update
    def update(self):
        """print(f"y = {self.rect.y}")
        print(f"x = {self.rect.x}")
        print(f"dy = {self.vel_y}")
        print(f"dx = {self.direction * self.speed}")
        print(f"bounce counter = {self.bounce_counter}")"""
        self.vel_y += GRAVITY
        dy = self.vel_y

        #horizontal speed with friction effect
        speed_mag = self.speed - GROUND_FRICTION * self.bounce_counter
        #keep speed positive
        if speed_mag < 0:
            speed_mag = 0
        #true directional speed
        true_dx = speed_mag * self.direction
        # store horizontal movement so the countdown only starts when grenade truly stops
        self.true_dx = true_dx

        #check collision with screen
        if self.rect.left + true_dx < 0 or self.rect.right + true_dx > SCREEN_WIDTH:
            self.direction *= -1
            true_dx = self.direction * speed_mag * BOUNCYNESS

        # Vertical movement and collision
        self.rect.y += dy
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                if dy > 0:
                    self.rect.bottom = tile[1].top
                    self.vel_y = -self.vel_y * BOUNCYNESS
                    self.bounce_counter += 1
                    if abs(self.vel_y) < 2:
                        self.vel_y = 0
                elif dy < 0:
                    self.rect.top = tile[1].bottom
                    self.vel_y = -self.vel_y * BOUNCYNESS

        # Horizontal movement and collision
        self.rect.x += true_dx
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                if true_dx > 0:
                    self.rect.right = tile[1].left
                    self.direction *= -1
                    self.speed *= BOUNCYNESS
                elif true_dx < 0:
                    self.rect.left = tile[1].right
                    self.direction *= -1
                    self.speed *= BOUNCYNESS
        # Apply screen scroll to x position
        self.rect.x += screen_scroll

        #countdown timer once grenade stops moving
        if abs(self.true_dx) < 0.1 and abs(self.vel_y) < 0.1:
            self.timer -= 1
        if self.timer <= 0:
            self.kill()
            #create explosion
            grenade_fx.play()
            explosion = Explosion(self.rect.centerx, self.rect.centery, 1.5)
            explosion_group.add(explosion)
            #damage
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 1 and abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 1:                        
                if player.alive:
                    player.health -= 100
            elif abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:                        
                if player.alive:
                    player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 1 and abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 1:
                    enemy.health -= 100
                elif abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 50
    
#explosion class
class Explosion(pygame.sprite.Sprite):

    #initialize
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self) 
        #load base images first
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"shooter platformer/imports/img/explosion/exp{num}.bmp").convert_alpha()
            #scale
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # per-instance hitbox toggle
        self.show_hitbox = show_all_hitboxes
        self.counter = 0
    
    #update
    def update(self):
        #scroll
        self.rect.x += screen_scroll
        #explode
        EXPLOSION_SPEED = 4
        #update explosion animation
        self.counter += 1
        #check if enough time 
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            #if animation is complete then delete explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

#screen fade
class ScreenFade():

    #initialize
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    #fade
    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        #direction whole
        if self.direction == 1:
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (SCREEN_WIDTH//2 + self.fade_counter, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT//2))
            pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT//2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
         #direction down
        if self.direction==2:
            pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete
        
#create screen fade
intro_fade = ScreenFade(1, BLACK, 8)
death_fade = ScreenFade(2, PINK, 8)

#create buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50,restart_img, 2)


#create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# prepare font
ui_font = get_font()
info_font = get_font(10)

#empty tile list filled with air
world_data = [] 
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#load in level data
with open(f"shooter platformer/imports/level{level}_data.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

#quit or no
run = True
#game loop
while run:

    #set fps
    clock.tick(fps)

    #start menu
    if start_game==False:
        #draw menu
        screen.fill(BG)
        #add buttons
        if start_button.draw(screen):
            start_intro = True
            start_game = True
        if exit_button.draw(screen):
            run = False

    #start / run the game        
    else:

        #update map and background on screen
        draw_bg()
        world.draw()

        #draw health bar
        health_bar.draw(player.health)

        #put ui elements on screen
        draw_text("AMMO: ", ui_font, WHITE, 10, 30)
        for x in range(player.ammo):
            screen.blit(bullet_img, (130 + (x * 10), 50))
        draw_text("GRENADES: ", ui_font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (190 + (x * 15), 75))

        #update visuals on screen
        if paused == False:
            player.update()
            for enemy in enemy_group:
                enemy.ai()
                enemy.update()
            bullet_group.update() 
            grenade_group.update()
            explosion_group.update()
            item_box_group.update()
            water_group.update()
            exit_group.update()
            decoration_group.update()
        player.draw()
        for enemy in enemy_group:
            enemy.draw()
        decoration_group.draw(screen)
        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        exit_group.draw(screen)
        item_box_group.draw(screen)
        water_group.draw(screen)

        #show intro
        if start_intro:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

        #hitbox status
        #draw_text(f"Hitboxes: {'ON' if show_all_hitboxes else 'OFF'} (H to toggle)", info_font, RED, 10, 500)

        #player action if alive 
        if player.alive:

            #shoot bullets
            if shoot:
                player.shoot()

            #throw grenade
            elif throw_grenade and grenade_thrown == False and player.grenades > 0:
                new_grenade = Grenade(player.rect.centerx + (0.55 * player.rect.size[0] * player.direction), player.rect.top, player.direction)
                grenade_group.add(new_grenade)
                grenade_thrown = True

                #reduce grenades
                player.grenades -= 1

            #update action   idle = 0     run = 1     jump = 2     
            if player.in_air:
                player.update_action(2)
            elif moving_left or moving_right:
                player.update_action(1)
            else:
                player.update_action(0)
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll

            #check if level complete
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVElS:
                    #load in level data
                    with open(f"shooter platformer/imports/level{level}_data.csv", newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)

        #restart screen if dead
        else:
            for enemy in enemy_group:
                enemy.ai()
                enemy.move(moving_left, moving_right)
                enemy.update()
                enemy.draw()
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True 
                    bg_scroll = 0
                    world_data = reset_level()
                    #load in level data
                    with open(f"shooter platformer/imports/level{level}_data.csv", newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)

    #any keybinds happening
    for event in pygame.event.get():    

        #quit game
        if event.type == pygame.QUIT:
            run = False

        #keyboard press
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w and player.alive and not paused:
                player.jump = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_e:
                throw_grenade = True
            if event.key == pygame.K_a and not paused:
                moving_left = True
            if event.key == pygame.K_d and not paused:
                moving_right = True
            if event.key == pygame.K_q:
                for grenade in grenade_group:
                    grenade.timer = 0
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key == pygame.K_h:
                show_all_hitboxes = not show_all_hitboxes
                #update all existing instances to new hitbox setting
                player.show_hitbox = show_all_hitboxes
                for enemy in enemy_group:
                    enemy.show_hitbox = show_all_hitboxes
                world.show_hitbox = show_all_hitboxes
                for tile in world.obstacle_list:
                    pass  # tile hitboxes drawn during world.draw()
                for box in item_box_group:
                    box.show_hitbox = show_all_hitboxes
                for deco in decoration_group:
                    deco.show_hitbox = show_all_hitboxes
                for water in water_group:
                    water.show_hitbox = show_all_hitboxes
                for ex in exit_group:
                    ex.show_hitbox = show_all_hitboxes
                for bullet in bullet_group:
                    bullet.show_hitbox = show_all_hitboxes
                for grenade in grenade_group:
                    grenade.show_hitbox = show_all_hitboxes
                for explosion in explosion_group:
                    explosion.show_hitbox = show_all_hitboxes
            if event.key == pygame.K_p:
                paused = not paused

        #keyboard release
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and not paused:
                shoot = False
            if event.key == pygame.K_e:
                throw_grenade = False
                grenade_thrown = False
            if event.key == pygame.K_a and not paused:
                moving_left = False
            if event.key == pygame.K_d and not paused:
                moving_right = False

    #draw entity rect for game pause
    for bullet in bullet_group:
        if bullet.show_hitbox:
            pygame.draw.rect(screen, RED, bullet.rect, 1)
    for grenade in grenade_group:
        if grenade.show_hitbox:
            pygame.draw.rect(screen, RED, grenade.rect, 1)

    #display update
    pygame.display.update()