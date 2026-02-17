#init imports
import pygame
import os
import random
import csv
pygame.init()


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
# Jump and air control tuning
JUMP_POWER = -12          # initial jump velocity (negative = upward)
JUMP_BUFFER = 6           # frames to buffer a jump input before landing
COYOTE_TIME = 6           # frames after leaving ground to still allow jump
AIR_SPEED_MULTIPLIER = 0.9  # horizontal speed multiplier while in air (less control)

ground_friction = 0.1
ROWS = 16
COLS = 150
TILE_SIZE = screen.get_height() // ROWS
TILE_TYPES = 21
screen_scroll = 0
bg_scroll = 0
# debug
DEBUG_COLLISIONS = True
last_blocking_tile = None
last_blocking_info = None
level = 1

#define soldier action variables
moving_left = False
moving_right = False
shoot = False
throw_grenade = False
grenade_thrown = False
# debug: show all hitboxes toggle (press H)
show_all_hitboxes = True

#load images
#bg
pine1_img = pygame.image.load(f"shooter platformer/imports/img/background/pine1.bmp").convert_alpha()
pine2_img = pygame.image.load(f"shooter platformer/imports/img/background/pine2.bmp").convert_alpha()
mountain_img = pygame.image.load(f"shooter platformer/imports/img/background/mountain.bmp").convert_alpha()
sky_img = pygame.image.load(f"shooter platformer/imports/img/background/sky_cloud.bmp").convert_alpha()

#load tiles
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
    screen.blit(sky_img, (0, 0))
    screen.blit(mountain_img, (0, SCREEN_HEIGHT - mountain_img.get_height() - 300))
    screen.blit(pine1_img, (0, SCREEN_HEIGHT - pine1_img.get_height() - 150))
    screen.blit(pine2_img, (0, SCREEN_HEIGHT - pine2_img.get_height()))

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

        #update stuff
        self.update_animation()
        self.check_alive()
        #update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    #movement
    def move(self, moving_left, moving_right):
        #reset movement var
        screen_scroll = 0
        dx = 0
        dy = 0

        # timers: decrement jump buffer and coyote timers each frame
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= 1
        if self.in_air and self.coyote_timer > 0:
            self.coyote_timer -= 1

        # If we're initially overlapping a tile (spawning inside), resolve by placing player on top
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                # if player center is above tile center, place on top
                if self.rect.centery < tile[1].centery:
                    self.rect.bottom = tile[1].top
                    self.vel_y = 0
                    self.in_air = False
                else:
                    # otherwise push player below tile
                    self.rect.top = tile[1].bottom
                    self.vel_y = 0
                break

        # quick ground check: is there ground just below the player?
        on_ground = False
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x, self.rect.y + 1, self.width, self.height):
                on_ground = True
                break
        # update in_air state based on ground check
        self.in_air = not on_ground

        #assign movement variable
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # reduce horizontal control while in air for consistent speed
        if self.in_air:
            dx = int(dx * AIR_SPEED_MULTIPLIER)
        
        #jump (allow from ground or within coyote time; honor buffered inputs)
        if (self.jump or self.jump_buffer_timer > 0) and (not self.in_air or self.coyote_timer > 0):
            self.vel_y = JUMP_POWER
            self.jump = False
            self.jump_buffer_timer = 0
            self.in_air = True

        #apply gravity and gravity cap
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        
        #apply jump
        dy += self.vel_y

        # Axis-separated collision resolution for robustness
        # Horizontal: move then resolve collisions
        self.rect.x += dx
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                if dx > 0:
                    # place player flush to left of tile
                    self.rect.right = tile[1].left
                elif dx < 0:
                    # place player flush to right of tile
                    self.rect.left = tile[1].right

                # debug: record first blocking tile for drawing and logging
                global last_blocking_tile, last_blocking_info
                if DEBUG_COLLISIONS and self.char_type == 'player' and last_blocking_tile is None:
                    last_blocking_tile = tile[1].copy()
                    last_blocking_info = (tile[1].x, tile[1].y, self.rect.x, self.rect.y, dx)
                break

        # Vertical: move then resolve collisions
        self.rect.y += dy
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                # hitting head
                if dy < 0:
                    self.rect.top = tile[1].bottom
                    self.vel_y = 0
                # landing
                elif dy > 0:
                    self.rect.bottom = tile[1].top
                    self.vel_y = 0
                    self.in_air = False
                    # give a small window after landing to still jump (coyote)
                    self.coyote_timer = COYOTE_TIME
                break

        #update scroll based on player position
        if self.char_type == "player":
            # scroll right when player passes right threshold
            if self.rect.right > SCREEN_WIDTH - SCROLL_THRESH:
                scroll_amount = self.rect.right - (SCREEN_WIDTH - SCROLL_THRESH)
                self.rect.x -= scroll_amount
                screen_scroll = -scroll_amount
            # scroll left when player passes left threshold and background allows
            elif self.rect.left < SCROLL_THRESH and bg_scroll > 0:
                scroll_amount = SCROLL_THRESH - self.rect.left
                self.rect.x += scroll_amount
                screen_scroll = scroll_amount
        
        #return scroll amount
        return screen_scroll

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

    #shoot bullet
    def shoot(self):
        #check cooldown and ammo
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            # reduce ammo once per shot
            self.ammo -= 1
            new_bullet = Bullet(self.rect.centerx + (0.55 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
            bullet_group.add(new_bullet)

    #ai
    def ai(self):

        #check alive
        if self.alive and player.alive:
            #check if want to idle
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)
                self.idling = True
                self.idling_counter = 50

            #check if player in sight
            if self.vision.colliderect(player.rect):
                #stop running and face player
                self.update_action(0)
                #shoot
                self.shoot() 
            
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

    #spawn
    def draw(self):
        # compute on-screen rect (do not mutate world rects)
        display_rect = self.rect.copy()
        display_rect.x += screen_scroll
        screen.blit(pygame.transform.flip(self.image, self.flip, False), display_rect)
        # draw hitbox if enabled for this instance (draw using on-screen rects)
        if getattr(self, "show_hitbox", False):
            pygame.draw.rect(screen, RED, display_rect, 1)
            if self.char_type == "enemy":
                viz_rect = self.vision.copy()
                viz_rect.x += screen_scroll
                pygame.draw.rect(screen, WHITE, viz_rect, 1)
        
#world class
class World():

    #initialize
    def __init__(self):
        self.obstacle_list = []
        self.show_hitbox = show_all_hitboxes

    #process
    def process_data(self, data):
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
                        player = soldier("player", x * TILE_SIZE, y * TILE_SIZE, 1.5, 6, 20, 5)#player
                        health_bar = HealthBar(10, 10, player.health, player.max_health)
                    elif tile == 16:
                        enemy = soldier("enemy", x * TILE_SIZE, y * TILE_SIZE, 1.5, 2, 20, 0)#enemy
                        enemy_group.add(enemy)
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
            # compute on-screen position without mutating world rects
            draw_rect = tile[1].copy()
            draw_rect.x += screen_scroll
            # draw the tile image
            screen.blit(tile[0], draw_rect)
            # draw a less-bold outline over the tile when hitboxes are enabled
            if self.show_hitbox:
                try:
                    pygame.draw.rect(screen, TILE_HITBOX_COLOR, draw_rect, TILE_HITBOX_WIDTH)
                except Exception:
                    # defensive: if tile[1] isn't a Rect, skip
                    pass

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
        self.rect.x += (self.direction * self.speed)

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

#grenade class
class Grenade(pygame.sprite.Sprite):

    #initialize
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self) 
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
        self.vel_y += GRAVITY
        dy = self.vel_y

        #horizontal speed with friction effect
        speed_mag = self.speed - ground_friction * self.bounce_counter
        #keep speed positive
        if speed_mag < 0:
            speed_mag = 0
        #true directional speed
        true_dx = speed_mag * self.direction
        # store horizontal movement so the countdown only starts when grenade truly stops
        self.true_dx = true_dx

        # vertical movement and collision with world (resolve Y axis first)
        self.rect.y += dy
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                # moving down (hit floor)
                if dy > 0:
                    self.rect.bottom = tile[1].top

                    # invert and dampen the vertical velocity (bounce)
                    self.vel_y = -self.vel_y * 0.7
                    self.bounce_counter += 1

                    # stop bouncing if velocity becomes very small ( add "or self.bounce_counter > 6" for bounce limit)
                    if abs(self.vel_y) < 2:
                        self.vel_y = 0
                # moving up (hit ceiling)
                elif dy < 0:
                    self.rect.top = tile[1].bottom
                    self.vel_y = 0
                # stop checking tiles after collision
                break

        # horizontal movement (resolve X axis)
        self.rect.x += true_dx
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                # hit tile from left or right, push grenade out and reverse/dampen horizontal motion
                if true_dx > 0:
                    # moving right, place to left of tile
                    self.rect.right = tile[1].left
                elif true_dx < 0:
                    # moving left, place to right of tile
                    self.rect.left = tile[1].right

                # reverse/dampen horizontal motion
                self.direction *= -1
                self.speed *= 0.7
                break

        # clamp to screen edges and bounce/dampen
        if self.rect.left < 0:
            self.rect.left = 0
            self.direction *= -1
            self.speed *= 0.7
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.direction *= -1
            self.speed *= 0.7

        #countdown timer once grenade stops moving (use small thresholds to handle float movement)
        if abs(self.true_dx) < 0.1 and abs(self.vel_y) < 0.1:
            self.timer -= 1
            #once timer is up explode
            if self.timer <= 0:
                #kill
                self.kill()
                #create explosion (scale to match max damage distance)
                explosion = Explosion(self.rect.centerx, self.rect.centery, damage_radius=TILE_SIZE*2)
                explosion_group.add(explosion)

                #helper: distance from point (px,py) to rectangle (closest point)
                def _rect_point_dist(rect, px, py):
                    dx = max(rect.left - px, 0, px - rect.right)
                    dy = max(rect.top - py, 0, py - rect.bottom)
                    return (dx*dx + dy*dy) ** 0.5

                #damage nearby characters (use distance to rect so touching counts)
                #player
                dist = _rect_point_dist(player.rect, self.rect.centerx, self.rect.centery)
                if dist < TILE_SIZE:
                    player.health -= 100
                elif dist < TILE_SIZE * 2:
                    player.health -= 50

                #all enemies in group do damage
                for enemy in enemy_group:
                    dist = _rect_point_dist(enemy.rect, self.rect.centerx, self.rect.centery)
                    if dist < TILE_SIZE:
                        enemy.health -= 100
                    elif dist < TILE_SIZE * 2:
                        enemy.health -= 50

#explosion class
class Explosion(pygame.sprite.Sprite):

    #initialize
    def __init__(self, x, y, scale=None, damage_radius=None):
        pygame.sprite.Sprite.__init__(self) 
        #load base images first
        base_imgs = []
        for num in range(1, 6):
            img = pygame.image.load(f"shooter platformer/imports/img/explosion/exp{num}.bmp").convert_alpha()
            base_imgs.append(img)

        # If a damage_radius is provided, compute scale so the image diameter (width) equals 2 * damage_radius
        if damage_radius is not None:
            # compute desired diameter from damage radius with a safe padding (avoid referencing undefined variables)
            desired_diameter = int(damage_radius * 2 + player.width)
            orig_w = base_imgs[0].get_width() if base_imgs else 1
            if orig_w <= 0:
                scale = 1.0
            else:
                scale = desired_diameter / orig_w
        else:
            # fallback to provided scale or default 1.0
            if scale is None:
                scale = 1.0

        # apply scaling
        self.images = []
        for img in base_imgs:
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
player, HealthBar = world.process_data(world_data)

#quit or no
run = True
#game loop
while run:

    #set fps
    clock.tick(fps)

    #any keybinds happening (process input early so movement & scroll are in sync with drawing)
    for event in pygame.event.get():    

        #quit game
        if event.type == pygame.QUIT:
            run = False

        #keyboard press
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w and player.alive:
                # set buffered jump so quick presses just before landing or slightly after leaving ground still work
                player.jump_buffer_timer = JUMP_BUFFER
                player.jump = True
            if event.key == pygame.K_SPACE:
                shoot = True
            if event.key == pygame.K_e:
                throw_grenade = True
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key == pygame.K_h:
                # toggle global hitbox display and apply to existing sprites
                show_all_hitboxes = not show_all_hitboxes
                player.show_hitbox = show_all_hitboxes
                for enemy_sprite in enemy_group:
                    enemy_sprite.show_hitbox = show_all_hitboxes
                for grenade_sprite in grenade_group:
                    grenade_sprite.show_hitbox = show_all_hitboxes
                for bullet_sprite in bullet_group:
                    bullet_sprite.show_hitbox = show_all_hitboxes
                for item_box_sprite in item_box_group:
                    item_box_sprite.show_hitbox = show_all_hitboxes
                for explosion_sprite in explosion_group:
                    explosion_sprite.show_hitbox = show_all_hitboxes
                # ensure the world tiles are also toggled
                try:
                    world.show_hitbox = show_all_hitboxes
                except Exception:
                    pass

        #keyboard release
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                shoot = False
            if event.key == pygame.K_e:
                throw_grenade = False
                grenade_thrown = False
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False

    #update map and background on screen
    #compute movement & scroll before drawing so world and sprites render in correct positions
    screen_scroll = player.move(moving_left, moving_right)
    draw_bg()
    world.draw()

    #draw health bar
    HealthBar.draw(player.health)

    #put ui elements on screen
    draw_text("AMMO: ", ui_font, WHITE, 10, 30)
    for x in range(player.ammo):
        screen.blit(bullet_img, (130 + (x * 10), 50))
    draw_text("GRENADES: ", ui_font, WHITE, 10, 60)
    for x in range(player.grenades):
        screen.blit(grenade_img, (190 + (x * 15), 75))

    #update visuals on screen
    player.update()
    player.draw()
    for enemy in enemy_group:
        enemy.ai()
        enemy.update()
        enemy.draw()
    bullet_group.update() 
    grenade_group.update()
    explosion_group.update()
    bullet_group.draw(screen)
    grenade_group.draw(screen)
    explosion_group.draw(screen)
    item_box_group.update()
    item_box_group.draw(screen)
    water_group.update()
    water_group.draw(screen)
    exit_group.update()
    exit_group.draw(screen)
    decoration_group.update()
    decoration_group.draw(screen)

    # draw hitboxes for non-soldier sprites that have the toggle enabled
    for group in (bullet_group, grenade_group, item_box_group):
        for sprite in group:
            if getattr(sprite, "show_hitbox", False):
                # draw a small centered box for bullets so the visual matches collision area
                if isinstance(sprite, Bullet):
                    bullet_box_width, bullet_box_height = 6, 6
                    bullet_hitbox_rect = pygame.Rect(0, 0, bullet_box_width, bullet_box_height)
                    bullet_hitbox_rect.center = sprite.rect.center
                    pygame.draw.rect(screen, WHITE, bullet_hitbox_rect, 1)
                else:
                    pygame.draw.rect(screen, RED, sprite.rect, 1)
    # debug collision overlay (toggle with DEBUG_COLLISIONS)
    if DEBUG_COLLISIONS and last_blocking_tile is not None:
        # draw blocking tile (in world coords adjusted for scroll)
        draw_rect = last_blocking_tile.copy()
        draw_rect.x += screen_scroll
        pygame.draw.rect(screen, (255,200,0), draw_rect, 3)
        # draw text info
        info = f"tile@({last_blocking_tile.x},{last_blocking_tile.y}) player@({player.rect.x},{player.rect.y}) scroll={screen_scroll}"
        try:
            draw_text(info, info_font, WHITE, 10, 520)
        except Exception:
            pass
        # also print to console once for capture and then clear
        print("DBG: blocking tile:", last_blocking_info, "screen_scroll=", screen_scroll)
        last_blocking_tile = None
        last_blocking_info = None    # draw grenade explosion damage radii (white) for small and big damage

    for grenade_sprite in grenade_group:
        if getattr(grenade_sprite, "show_hitbox", False):
            center_x, center_y = grenade_sprite.rect.center
            small_damage_rect = pygame.Rect(0, 0, TILE_SIZE * 2, TILE_SIZE * 2)
            small_damage_rect.center = (center_x, center_y)
            big_damage_rect = pygame.Rect(0, 0, TILE_SIZE * 4, TILE_SIZE * 4)
            big_damage_rect.center = (center_x, center_y)
            pygame.draw.rect(screen, WHITE, small_damage_rect, 1)
            pygame.draw.rect(screen, WHITE, big_damage_rect, 1) 

    #activate player actions
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

        #hitbox status
        draw_text(f"Hitboxes: {'ON' if show_all_hitboxes else 'OFF'} (H to toggle)", info_font, RED, 10, 500)

        #display update
        pygame.display.update()