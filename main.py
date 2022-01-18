import pygame
import random
import os
import sys
SCORE = 0


def load_image(name, colorkey=None):
	fullname = os.path.join('data', name)
	if not os.path.isfile(fullname):
		print(f"Файл с изображением '{fullname}' не найден")
		sys.exit()
	image = pygame.image.load(fullname)
	if colorkey is not None:
		image = image.convert()
		if colorkey == -1:
			colorkey = image.get_at((0, 0))
		image.set_colorkey(colorkey)
	else:
		image = image.convert_alpha()
	return image


class Button:
	def __init__(self, width, height, color):
		self.width = width
		self.height = height
		self.font = pygame.font.Font('data/Pixeled.ttf', 15)
		self.color = color

	def draw(self, x, y, text='', action=None, active=True):
		mouse = pygame.mouse.get_pos()
		click = pygame.mouse.get_pressed()
		if x < mouse[0] < x + self.width and y < mouse[1] < y + self.height:
				pygame.draw.rect(screen, self.color, (x, y, self.width, self.height), 3)
				if click[0] == 1 and active:
					pygame.time.delay(300)
					action()
		else:
			pygame.draw.rect(screen, (35, 35, 35), (x, y, self.width, self.height), 3)
		text_surf = self.font.render(text, False, self.color)
		text_rect = text_surf.get_rect(topleft=(x + (self.width - text_surf.get_width()) / 2,
												y + (self.height - text_surf.get_height()) / 2))
		screen.blit(text_surf, text_rect)


class Alien(pygame.sprite.Sprite):
	def __init__(self, color, x, y):
		super().__init__()
		self.image = load_image(f'enemy_skins/{color}.png')
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.mask = pygame.mask.from_surface(self.image)

	def update(self, direction):
		self.rect.x += direction


class Player(pygame.sprite.Sprite):
	def __init__(self, pos, speed, skin):
		super().__init__()
		self.pos = pos
		if skin == 0:
			self.image = load_image('hero_skins/player_.png')
		else:
			self.image = load_image('hero_skins/player3.png')
		self.rect = self.image.get_rect(midbottom=pos)
		self.mask = pygame.mask.from_surface(self.image)
		self.speed = speed
		self.leave = False
		# Для лазера и ускорения
		self.ready = True
		self.laser_time = 0
		self.speed_time = 0
		# кд на выстрел
		self.laser_cd = 600
		# группа лазеров
		self.lasers = pygame.sprite.Group()
		# Направления полета
		self.directions = {'left': False, 'right': False, 'up': False, 'down': False}

	def action(self):
		# Движение
		keys = pygame.key.get_pressed()
		if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
			self.directions['right'] = True
		if keys[pygame.K_LEFT] or keys[pygame.K_a]:
			self.directions['left'] = True
		if keys[pygame.K_UP] or keys[pygame.K_w]:
			self.directions['up'] = True
		if keys[pygame.K_DOWN] or keys[pygame.K_s]:
			self.directions['down'] = True
		if not (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
			self.directions['right'] = False
		if not (keys[pygame.K_LEFT] or keys[pygame.K_a]):
			self.directions['left'] = False
		if not (keys[pygame.K_UP] or keys[pygame.K_w]):
			self.directions['up'] = False
		if not (keys[pygame.K_DOWN] or keys[pygame.K_s]):
			self.directions['down'] = False
		# Выстрел
		if keys[pygame.K_SPACE] and self.ready:
			self.shoot_laser()
			self.ready = False
			self.laser_time = pygame.time.get_ticks()
		# для тестов
		# if keys[pygame.K_k]:
		# 	self.laser_cd = 10
		# 	self.speed_time = pygame.time.get_ticks()
		if keys[pygame.K_ESCAPE]:
			self.leave = True
		if self.directions['right']:
			self.rect.x += self.speed
		if self.directions['left']:
			self.rect.x -= self.speed
		if self.directions['up']:
			self.rect.y -= self.speed
		if self.directions['down']:
			self.rect.y += self.speed

	def recharge(self):
		if not self.ready:
			current_time = pygame.time.get_ticks()
			if current_time - self.laser_time >= self.laser_cd:
				self.ready = True

	# Ограничение, чтобы игрок не вылетал за экран
	def check_borders(self):
		if self.rect.left <= 0:
			self.rect.left = 0
		if self.rect.right >= 900:
			self.rect.right = 900
		if self.rect.bottom >= 900:
			self.rect.bottom = 900

	def shoot_laser(self):
		self.lasers.add(Laser(self.rect.center, -8, (255, 255, 255)))

	# Отключает ускорение
	def deny_speed(self):
		current_time = pygame.time.get_ticks()
		if current_time - self.speed_time >= 5000:
			self.laser_cd = 600

	def update(self):
		self.action()
		self.check_borders()
		self.recharge()
		self.deny_speed()
		self.lasers.update()


class Laser(pygame.sprite.Sprite):
	def __init__(self, pos, speed, color):
		super().__init__()
		self.image = pygame.Surface((6, 22))
		self.image.fill(color)
		self.rect = self.image.get_rect(center=pos)
		self.speed = speed

	# Убирает лазеры, когда те улетают за экран
	def destroy_laser(self):
		global SCORE
		if self.rect.y <= -50:
			SCORE -= 50
			self.kill()
		elif self.rect.y >= 950:
			self.kill()


	def update(self):
		self.rect.y += self.speed
		self.destroy_laser()


class Game:
	def __init__(self):
		global SCORE
		# Игрок
		self.skin = 0
		self.score_board = {1: 4800, 2: 6000, 3: 6400, 4: 100, 5: 100, 6: 100, 7: 100, 8: 100}
		player = Player((screen_width / 2, screen_height), 5, self.skin)
		self.player_mask = player
		self.player = pygame.sprite.GroupSingle(player)
		# Жизини и очки
		self.lives = 3
		self.live_surf = load_image('heart/heart.png')
		self.live_x_start_pos = screen_width - (self.live_surf.get_size()[0] * 2 + 20)
		SCORE = 0
		self.font = pygame.font.Font('data/Pixeled.ttf', 20)

		# Враги, их лазеры
		self.aliens = pygame.sprite.Group()
		self.alien_lasers = pygame.sprite.Group()
		self.alien_direction = 1
		self.starting_screen = True
		self.choosing_level = False
		self.lost_screen = False
		self.shop = False
		self.current_level = 1

	def leave(self):
		pygame.quit()
		sys.exit()

	def show_starting_screen(self):
		if self.starting_screen:
			screen.fill((35, 35, 35))
			background = load_image('Starting_screen.png')
			back_rect = background.get_rect(topleft=(0, 0))
			screen.blit(background, back_rect)
			button_new_game = Button(200, 60, (230, 230, 230))
			button_new_game.draw(560, 600, 'Начать игру', self.switch_screens)
			text_surf = pygame.font.Font('data/Pixeled.ttf', 30).render('Space Invaders', False, 'white')
			text_rect = text_surf.get_rect(bottomleft=(470, 550))
			screen.blit(text_surf, text_rect)
			button_new_game = Button(170, 60, (230, 230, 230))
			button_new_game.draw(580, 680, 'Магазин', self.switch_shop)
			button_new_game = Button(150, 60, (230, 230, 230))
			button_new_game.draw(590, 760, 'Выйти', self.leave)

	def switch_shop(self):
		self.shop = not self.shop
		self.starting_screen = not self.starting_screen

	def show_lose_screen(self):
		if SCORE < 0:
			self.lost_screen = True
		if self.lost_screen:
			self.aliens = pygame.sprite.Group()
			self.alien_lasers = pygame.sprite.Group()
			player = Player((screen_width / 2, screen_height), 5, self.skin)
			self.player_mask = player
			self.player = pygame.sprite.GroupSingle(player)
			screen.fill((35, 35, 35))
			background = load_image('Lost_screen.png')
			back_rect = background.get_rect(topleft=(0, 0))
			screen.blit(background, back_rect)
			victory_surf = self.font.render('Вы проиграли :(', False, 'white')
			victory_rect = victory_surf.get_rect(center=(screen_width / 2, screen_height / 2 + 50))
			button_next = Button(150, 50, (230, 230, 230))
			button_next.draw(screen_width / 2 - 70, screen_height / 2 + 90, 'В меню', self.next_level)
			screen.blit(victory_surf, victory_rect)

	def show_shop_screen(self):
		if self.shop:
			screen.fill((35, 35, 35))
			background = load_image('Shop_screen.png')
			back_rect = background.get_rect(topleft=(0, 0))
			screen.blit(background, back_rect)
			button_new_game = Button(300, 60, (230, 230, 230))
			button_new_game.draw(20, 20, 'В главное меню', self.switch_shop)
			with open('data/levels/coins.txt', 'r') as f:
				coins = int(f.read().strip())
			money_surf = self.font.render(f'Монет: {coins}', False, 'white')
			money_rect = money_surf.get_rect(topright=(800, 20))
			screen.blit(money_surf, money_rect)
			# -- #
			with open('data/hero_skins/own_skin3.txt', 'r') as f:
				own_skin3 = f.read().strip()
			button_buy= Button(250, 60, (230, 230, 230))
			button_buy.draw(150, 600, 'Выбрать', self.choose_skin_0)
			if own_skin3 == '0':
				button_buy= Button(250, 60, (230, 230, 230))
				button_buy.draw(510, 600, 'Купить (400)', self.buy_ship)
			else:
				button_buy= Button(250, 60, (230, 230, 230))
				button_buy.draw(510, 600, 'Выбрать', self.choose_skin_1)

	def choose_skin_0(self):
		self.skin = 0
		player = Player((screen_width / 2, screen_height), 5, self.skin)
		self.player_mask = player
		self.player = pygame.sprite.GroupSingle(player)
		self.shop = False
		self.starting_screen = True

	def choose_skin_1(self):
		self.skin = 1
		player = Player((screen_width / 2, screen_height), 5, self.skin)
		self.player_mask = player
		self.player = pygame.sprite.GroupSingle(player)
		self.shop = False
		self.starting_screen = True

	def buy_ship(self):
		with open('data/levels/coins.txt', 'r') as f:
			coins = int(f.read().strip())
		if coins >= 400:
			coins -= 400
			with open('data/levels/coins.txt', 'w') as f:
				f.write(str(coins))
			with open('data/hero_skins/own_skin3.txt', 'w') as f:
				f.write('1')

	def switch_screens(self):
		self.starting_screen = not self.starting_screen
		self.choosing_level = not self.choosing_level

	def show_choose_level_screen(self):
		if self.choosing_level:
			screen.fill((35, 35, 35))
			text_surf = self.font.render('Уровни', False, 'white')
			text_rect = text_surf.get_rect(topleft=(450 - text_surf.get_height(), 100))
			screen.blit(text_surf, text_rect)
			# Вернуться в меню
			button_new_game = Button(300, 60, (230, 230, 230))
			button_new_game.draw(20, 20, 'В главное меню', self.switch_screens)
			# уровни
			levels = '12345678'
			with open('data/levels/progress.txt') as f:
				completed_levels = f.read()
			for i, level in enumerate(levels):
				if level in completed_levels:
					exec(f'button = Button(50, 50, (230, 230, 230))')
					exec(f'button.draw(i * 60 + 220, 180, "{level}", self.load_level, True)')
				else:
					exec(f'button = Button(50, 50, (70, 70, 70))')
					exec(f'button.draw(i * 60 + 220, 180, "{level}", None, False)')
			b_inf = Button(200, 50, (230, 230, 230))
			b_inf.draw(355, 300, 'Случайный', self.load_random_level, True)

	def load_level(self):
		if not self.player_mask.leave:
			screen.fill((35, 35, 35))
			self.starting_screen = False
			self.choosing_level = False
			mouse = pygame.mouse.get_pos()
			self.current_level = (mouse[0] - 220) // 60 + 1
			with open(f'data/levels/level{self.current_level}.txt') as content:
				lev = content.readlines()
			x = 0
			y = 0
			for line in lev:
				for spot in line:
					if spot == '.':
						pass
					elif spot == 'g':
						alien_sprite = Alien('green', x, y)
						self.aliens.add(alien_sprite)
					elif spot == 'r':
						alien_sprite = Alien('red', x, y)
						self.aliens.add(alien_sprite)
					elif spot == 'y':
						alien_sprite = Alien('yellow', x, y)
						self.aliens.add(alien_sprite)
					x += 50
				y += 32
				x = 0

	def load_random_level(self):
		self.starting_screen = False
		self.choosing_level = False
		lev = []
		for _ in range(8):
			line = ''
			for _ in range(16):
				line += random.choice(['.', 'g', 'r', 'y', '.'])
			lev.append(line)
		x = 0
		y = 0
		for line in lev:
			for spot in line:
				if spot == '.':
					pass
				elif spot == 'g':
					alien_sprite = Alien('green', x, y)
					self.aliens.add(alien_sprite)
				elif spot == 'r':
					alien_sprite = Alien('red', x, y)
					self.aliens.add(alien_sprite)
				elif spot == 'y':
					alien_sprite = Alien('yellow', x, y)
					self.aliens.add(alien_sprite)
				x += 50
			y += 32
			x = 0

	def check_aliens(self):
		all_aliens = self.aliens.sprites()
		# Если один враг ударяется о край экрана, то все меняют направление и спускаются вниз
		for alien in all_aliens:
			if alien.rect.right >= screen_width:
				self.alien_direction = -1
				self.move_down()
			elif alien.rect.left <= 0:
				self.alien_direction = 1
				self.move_down()

	def move_down(self):
		if self.aliens:
			for alien in self.aliens.sprites():
				alien.rect.y += 2

	def shoot(self):
		if self.aliens.sprites():
			random_alien = random.choice(self.aliens.sprites())
			laser_sprite = Laser(random_alien.rect.center, 6, (255, 255, 255))
			self.alien_lasers.add(laser_sprite)

	def check_collision(self):
		global SCORE
		# Попадание лазера игрока во врага
		if self.player.sprite.lasers:
			for laser in self.player.sprite.lasers:
				if pygame.sprite.spritecollide(laser, self.aliens, True):
					SCORE += 100
					laser.kill()

		# Попадание лазера врага в игрока
		if self.alien_lasers:
			for laser in self.alien_lasers:
				if pygame.sprite.collide_mask(laser, self.player_mask):
					laser.kill()
					self.lives -= 1
					SCORE -= 200
					screen.fill((80, 35, 35))
					if self.lives == 0:
						self.lost_screen = True

		# При столкновении игрока с врагом
		if self.aliens:
			for alien in self.aliens:
				if pygame.sprite.spritecollide(alien, self.player, False):
					self.lost_screen = True

	def display_score_and_lives(self):
		global SCORE
		score_surf = self.font.render(f'Счет: {SCORE}', False, 'white')
		score_rect = score_surf.get_rect(topleft=(10, -10))
		screen.blit(score_surf, score_rect)
		for live in range(self.lives):
			x = self.live_x_start_pos + (live * (self.live_surf.get_size()[0] - 10)) - 50
			screen.blit(self.live_surf, (x, 8))

	def victory(self):
		if not self.aliens.sprites():
			self.aliens = pygame.sprite.Group()
			self.alien_lasers = pygame.sprite.Group()
			player = Player((screen_width / 2, screen_height), 5, self.skin)
			self.player_mask = player
			self.player = pygame.sprite.GroupSingle(player)
			screen.fill((35, 35, 35))
			victory_surf = self.font.render('Уровень пройден', False, 'white')
			victory_rect = victory_surf.get_rect(center=(screen_width / 2, screen_height / 2 - 20))
			screen.blit(victory_surf, victory_rect)
			#
			score_surf = self.font.render(f'Счет: {SCORE}/{self.score_board[self.current_level]}', False, 'white')
			score_rect = score_surf.get_rect(center=(screen_width / 2, screen_height / 2 + 50))
			screen.blit(score_surf, score_rect)
			#
			score_surf = self.font.render(f'Получено монет: {SCORE // 10}', False, 'white')
			score_rect = score_surf.get_rect(center=(screen_width / 2, screen_height / 2 + 100))
			screen.blit(score_surf, score_rect)
			button_next = Button(150, 50, (230, 230, 230))
			button_next.draw(screen_width / 2 - 70, screen_height / 2 + 140, 'Дальше', self.next_level)
			with open('data/levels/progress.txt', 'r') as f:
				all_levels = f.read()
			if not str(self.current_level) in all_levels:
				with open('data/levels/progress.txt', 'a') as f:
					f.seek(0, 2)
					f.write(str(self.current_level))

	def next_level(self):
		global SCORE
		screen.fill((35, 35, 35))
		self.current_level += 1
		self.choosing_level = True
		self.lost_screen = False
		with open('data/levels/coins.txt', 'r') as f:
			cur_coins = f.read().strip()
		cur_coins = int(cur_coins)
		with open('data/levels/coins.txt', 'w') as f:
			f.write(str(SCORE // 10 + cur_coins))
		SCORE = 0
		self.lives = 3

	def run(self):
		global SCORE
		if self.player_mask.leave:
			self.choosing_level = True
			self.aliens = pygame.sprite.Group()
			self.alien_lasers = pygame.sprite.Group()
			player = Player((screen_width / 2, screen_height), 5, self.skin)
			self.player_mask = player
			self.player = pygame.sprite.GroupSingle(player)
			SCORE = 0
		self.show_starting_screen()
		self.show_choose_level_screen()
		self.show_lose_screen()
		self.show_shop_screen()
		if self.starting_screen == self.choosing_level == self.lost_screen == self.shop == False:
			self.player.update()
			self.alien_lasers.update()
			self.aliens.update(self.alien_direction)
			self.check_aliens()
			self.check_collision()
			self.player.sprite.lasers.draw(screen)
			self.player.draw(screen)
			self.aliens.draw(screen)
			self.alien_lasers.draw(screen)
			self.display_score_and_lives()
			self.victory()


if __name__ == '__main__':
	pygame.init()
	screen_width = 900
	screen_height = 900
	screen = pygame.display.set_mode((screen_width, screen_height))
	pygame.display.set_caption('Space-Invaders')
	icon = load_image('hero_skins\player3_temp.png')
	pygame.display.set_icon(icon)
	clock = pygame.time.Clock()
	game = Game()
	alien_laser_ready = 0
	pygame.time.set_timer(alien_laser_ready, 600)
	time_start = 0
	game.show_starting_screen()
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == alien_laser_ready:
				game.shoot()
		screen.fill((35, 35, 35))
		game.run()
		pygame.display.flip()
		clock.tick(60)
