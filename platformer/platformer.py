import pygame
from pygame.locals import *

#startup init
pygame.init()

screen_width = 1000
screen_height = 1000

#load images
sun_img = pygame.image.load("platformer/platformer_assets/img/sun.png")
bg_img = pygame.image.load("platformer/platformer_assets/img/sky.png")

#define game variables
tile_size = 50

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Platformer")

#classes
#world class
class World():
    def __init__(self, data):

        #tile list
        self.tile_list = []

        #load the images
        dirt_img = pygame.image.load("platformer/platformer_assets/img/dirt.png")
        grass_img = pygame.image.load("platformer/platformer_assets/img/grass.png")

        #load data    
        row_count = 0    
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])

#player
class Player():
    def __init__(self, x, y):
        img = pygame.image.load("platformer/platformer_assets/img/player.png")
        self.image = pygame.transform.scale(img, (40, 80))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = ya

world_data = [
    [1,1,1,1,1],
    [1,0,0,0,1],
    [1,0,0,0,1],
    [1,0,0,0,1],
    [1,2,2,2,1]
]

world = World(world_data)

print(world.tile_list)


run = True
while run:

    screen.blit(bg_img, (0, 0))
    screen.blit(sun_img, (100, 100))

    world.draw()

    for event in pygame.event.get():
        if event.type == QUIT:
            run = False

    pygame.display.update()

pygame.quit()