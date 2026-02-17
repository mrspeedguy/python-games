import pygame
import button
import csv
import pickle
import os

pygame.init()

clock = pygame.time.Clock()
FPS = 60

#game window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 640
LOWER_MARGIN = 100
SIDE_MARGIN = 300

screen = pygame.display.set_mode((SCREEN_WIDTH + SIDE_MARGIN, SCREEN_HEIGHT + LOWER_MARGIN))
pygame.display.set_caption('Level Editor')


#define game variables
ROWS = 16
MAX_COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
level = 0
# base directory with shooter platformer files
SHOOTER_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'shooter platformer'))
# common places for level files (check imports first)
SHOOTER_LEVEL_DIRS = [os.path.join(SHOOTER_BASE_DIR, 'imports'), SHOOTER_BASE_DIR]

def get_level_path(level_num):
	filename = f'level{level_num}_data.csv'
	for d in SHOOTER_LEVEL_DIRS:
		path = os.path.join(d, filename)
		if os.path.exists(path):
			return path
	# default to the imports folder for new files
	return os.path.join(SHOOTER_LEVEL_DIRS[0], filename)

current_tile = 0
scroll_left = False
scroll_right = False
scroll = 0
scroll_speed = 1


#load images
pine1_img = pygame.image.load('LevelEditor-main/img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('LevelEditor-main/img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('LevelEditor-main/img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('LevelEditor-main/img/Background/sky_cloud.png').convert_alpha()
#store tiles in a list
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'LevelEditor-main/img/tile/{x}.png').convert_alpha()
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)

save_img = pygame.image.load('LevelEditor-main/img/save_btn.png').convert_alpha()
load_img = pygame.image.load('LevelEditor-main/img/load_btn.png').convert_alpha()


#define colours
GREEN = (144, 201, 120)
WHITE = (255, 255, 255)
RED = (200, 25, 25)

# hitbox display settings
HITBOX_SHOW = False  # toggle with H key
HITBOX_COLOR = (255, 255, 0)  # use yellow for better contrast
HITBOX_WIDTH = 3  # outline width in pixels
HITBOX_FILL_ALPHA = 100  # translucent fill alpha (0-255)

#define font
font = pygame.font.SysFont('Futura', 30)

# message for user feedback
message = ''
message_time = 0
MSG_DURATION = 2000  # milliseconds

#create empty tile list
world_data = []
for row in range(ROWS):
	r = [-1] * MAX_COLS
	world_data.append(r)

#create ground
for tile in range(0, MAX_COLS):
	world_data[ROWS - 1][tile] = 0


#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))


#create function for drawing background
def draw_bg():
	screen.fill(GREEN)
	width = sky_img.get_width()
	for x in range(4):
		screen.blit(sky_img, ((x * width) - scroll * 0.5, 0))
		screen.blit(mountain_img, ((x * width) - scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
		screen.blit(pine1_img, ((x * width) - scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
		screen.blit(pine2_img, ((x * width) - scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

#draw grid
def draw_grid():
	#vertical lines
	for c in range(MAX_COLS + 1):
		pygame.draw.line(screen, WHITE, (c * TILE_SIZE - scroll, 0), (c * TILE_SIZE - scroll, SCREEN_HEIGHT))
	#horizontal lines
	for c in range(ROWS + 1):
		pygame.draw.line(screen, WHITE, (0, c * TILE_SIZE), (SCREEN_WIDTH, c * TILE_SIZE))


#function for drawing the world tiles
def draw_world():
	for y, row in enumerate(world_data):
		for x, tile in enumerate(row):
			if tile >= 0:
				# compute on-screen position taking scroll into account
				pos_x = x * TILE_SIZE - scroll
				pos_y = y * TILE_SIZE
				# draw tile
				screen.blit(img_list[tile], (pos_x, pos_y))
				# optionally draw hitbox translucent fill and outline for placed tiles
				if HITBOX_SHOW:
					# translucent fill
					fill_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
					fill_surf.fill((*HITBOX_COLOR, HITBOX_FILL_ALPHA))
					screen.blit(fill_surf, (pos_x, pos_y))
					# outline
					pygame.draw.rect(screen, HITBOX_COLOR, (pos_x, pos_y, TILE_SIZE, TILE_SIZE), HITBOX_WIDTH) 



#create buttons
save_button = button.Button(SCREEN_WIDTH // 2, SCREEN_HEIGHT + LOWER_MARGIN - 50, save_img, 1)
load_button = button.Button(SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT + LOWER_MARGIN - 50, load_img, 1)
#make a button list
button_list = []
button_col = 0
button_row = 0
for i in range(len(img_list)):
	tile_button = button.Button(SCREEN_WIDTH + (75 * button_col) + 50, 75 * button_row + 50, img_list[i], 1)
	button_list.append(tile_button)
	button_col += 1
	if button_col == 3:
		button_row += 1
		button_col = 0


run = True
while run:

	clock.tick(FPS)

	draw_bg()
	draw_grid()
	draw_world()

	draw_text(f'Level: {level}', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 90)
	draw_text('Press H to toggle hitboxes', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 120)
	draw_text('Press UP or DOWN to change level', font, WHITE, 10, SCREEN_HEIGHT + LOWER_MARGIN - 60)
	# persistent hitbox status in the tile panel
	draw_text(f'Hitboxes: {"ON" if HITBOX_SHOW else "OFF"}', font, WHITE, SCREEN_WIDTH + 10, SCREEN_HEIGHT - 30)
	# display temporary message if any
	if message and pygame.time.get_ticks() - message_time < MSG_DURATION:
		draw_text(message, font, RED, 10, SCREEN_HEIGHT + LOWER_MARGIN - 30)

	#save and load data
	if save_button.draw(screen):
		#save level data (writes to shooter platformer folder or imports)
		path = get_level_path(level)
		os.makedirs(os.path.dirname(path), exist_ok=True)
		try:
			with open(path, 'w', newline='') as csvfile:
				writer = csv.writer(csvfile, delimiter = ',')
				for row in world_data:
					writer.writerow(row)
			message = f'Saved level to {os.path.basename(path)}'
			message_time = pygame.time.get_ticks()
			print(message)
		except Exception as e:
			message = f'Error saving: {e}'
			message_time = pygame.time.get_ticks()
			print(message)
		#alternative pickle method
		#pickle_out = open(f'level{level}_data', 'wb')
		#pickle.dump(world_data, pickle_out)
		#pickle_out.close()
	if load_button.draw(screen):
		#load in level data (from shooter platformer folder)
		#reset scroll back to the start of the level
		scroll = 0
		path = get_level_path(level)
		try:
			with open(path, newline='') as csvfile:
				reader = csv.reader(csvfile, delimiter = ',')
				for x, row in enumerate(reader):
					for y, tile in enumerate(row):
						world_data[x][y] = int(tile)
			message = f'Loaded level {os.path.basename(path)}'
			message_time = pygame.time.get_ticks()
			print(message)
		except FileNotFoundError:
			message = f'Level file not found: {os.path.basename(path)}'
			message_time = pygame.time.get_ticks()
			print(message)
		except Exception as e:
			message = f'Error loading: {e}'
			message_time = pygame.time.get_ticks()
			print(message)
		#alternative pickle method
		#world_data = []
		#pickle_in = open(f'level{level}_data', 'rb')
		#world_data = pickle.load(pickle_in)
				

	#draw tile panel and tiles
	pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH, 0, SIDE_MARGIN, SCREEN_HEIGHT))

	#choose a tile
	button_count = 0
	for button_count, i in enumerate(button_list):
		if i.draw(screen):
			current_tile = button_count

	#highlight the selected tile
	pygame.draw.rect(screen, RED, button_list[current_tile].rect, 3)

	#scroll the map
	if scroll_left == True and scroll > 0:
		scroll -= 5 * scroll_speed
	if scroll_right == True and scroll < (MAX_COLS * TILE_SIZE) - SCREEN_WIDTH:
		scroll += 5 * scroll_speed

	#add new tiles to the screen
	#get mouse position
	pos = pygame.mouse.get_pos()
	x = (pos[0] + scroll) // TILE_SIZE
	y = pos[1] // TILE_SIZE

	#check that the coordinates are within the tile area
	if pos[0] < SCREEN_WIDTH and pos[1] < SCREEN_HEIGHT:
		#update tile value
		if pygame.mouse.get_pressed()[0] == 1:
			if world_data[y][x] != current_tile:
				world_data[y][x] = current_tile
		if pygame.mouse.get_pressed()[2] == 1:
			world_data[y][x] = -1


	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
		#keyboard presses
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_UP:
				level += 1
			if event.key == pygame.K_DOWN and level > 0:
				level -= 1
			if event.key == pygame.K_LEFT:
				scroll_left = True
			if event.key == pygame.K_RIGHT:
				scroll_right = True
			if event.key == pygame.K_RSHIFT:
				scroll_speed = 5
			if event.key == pygame.K_h:
				# toggle hitbox display
				HITBOX_SHOW = not HITBOX_SHOW
				# show brief message indicating state
				message = 'Hitboxes ON' if HITBOX_SHOW else 'Hitboxes OFF'
				message_time = pygame.time.get_ticks()
				print(message)


		if event.type == pygame.KEYUP:
			if event.key == pygame.K_LEFT:
				scroll_left = False
			if event.key == pygame.K_RIGHT:
				scroll_right = False
			if event.key == pygame.K_RSHIFT:
				scroll_speed = 1


	pygame.display.update()

pygame.quit()

