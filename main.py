import pygame
from random import choice
import os
import sys


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


class Alien(pygame.sprite.Sprite):
	def __init__(self, color, x, y):
		super().__init__()
		file = 'enemy_skins/' + color + '.png'
		self.image = load_image(file )
		self.rect = self.image.get_rect(topleft=(x, y))
		self.mask = pygame.mask.from_surface(self.image)

	def update(self, direction):
		self.rect.x += direction


class Player(pygame.sprite.Sprite):
	def __init__(self, pos, speed):
		super().__init__()
		self.image = load_image('hero_skins/player.png')
		self.rect = self.image.get_rect(midbottom=pos)
		self.mask = pygame.mask.from_surface(self.image)
		self.speed = speed
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
		# Ускорение
		if keys[pygame.K_k]:
			self.laser_cd = 200
			self.speed_time = pygame.time.get_ticks()

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
		if self.rect.right >= 1000:
			self.rect.right = 1000
		if self.rect.bottom >= 1000:
			self.rect.bottom = 1000

	def shoot_laser(self):
		self.lasers.add(Laser(self.rect.center, -8))

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
	def __init__(self, pos, speed):
		super().__init__()
		self.image = pygame.Surface((4, 20))
		self.image.fill('white')
		self.rect = self.image.get_rect(center=pos)
		self.speed = speed

	# Убирает лазеры, когда те улетают за экран
	def destroy_laser(self):
		if self.rect.y <= -50 or self.rect.y >= 1050:
			self.kill()

	def update(self):
		self.rect.y += self.speed
		self.destroy_laser()


class StartScreen:
	pass


class Game:
	def __init__(self):
		# Игрок
		player = Player((screen_width / 2, screen_height), 5)
		self.player_mask = player
		self.player = pygame.sprite.GroupSingle(player)

		# Жизини и очки
		self.lives = 3
		self.live_surf = load_image('heart/heart.png')
		self.live_x_start_pos = screen_width - (self.live_surf.get_size()[0] * 2 + 20)
		self.score = 0
		self.font = pygame.font.Font('data/Pixeled.ttf', 20)

		# Враги, их лазеры
		self.aliens = pygame.sprite.Group()
		self.alien_lasers = pygame.sprite.Group()
		self.alien_direction = 1

		# Загрузка уровня, которая пока не работает
		self.load_level(1)

	def load_level(self, level):
		with open(f'data/levels/level{level}.txt') as content:
			lev = content.readlines()
		x = 0
		y = 0
		for line in lev:
			for spot in line:
				if spot == '.':
					x += 50
				elif spot == 'g':
					alien_sprite = Alien('green', x, y)
					self.aliens.add(alien_sprite)
				elif spot == 'r':
					alien_sprite = Alien('red', x, y)
					self.aliens.add(alien_sprite)
				elif spot == 'y':
					alien_sprite = Alien('yellow', x, y)
					self.aliens.add(alien_sprite)
				x += 20
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
			random_alien = choice(self.aliens.sprites())
			laser_sprite = Laser(random_alien.rect.center, 6)
			self.alien_lasers.add(laser_sprite)

	def check_collision(self):
		# Попадание лазера игрока во врага
		if self.player.sprite.lasers:
			for laser in self.player.sprite.lasers:
				if pygame.sprite.spritecollide(laser, self.aliens, True):
					laser.kill()
					self.score += 100

		# Попадание лазера врага в игрока
		if self.alien_lasers:
			for laser in self.alien_lasers:
				if pygame.sprite.collide_mask(laser, self.player_mask):
					laser.kill()
					self.lives -= 1
					if self.lives == 0:
						pygame.quit()
						sys.exit()

		# При столкновении игрока с врагом
		if self.aliens:
			for alien in self.aliens:
				if pygame.sprite.spritecollide(alien, self.player, False):
					pygame.quit()
					sys.exit()

	def display_score_and_lives(self):
		score_surf = self.font.render(f'Счет: {self.score}', False, 'white')
		score_rect = score_surf.get_rect(topleft=(10, -10))
		screen.blit(score_surf, score_rect)
		for live in range(self.lives):
			x = self.live_x_start_pos + (live * (self.live_surf.get_size()[0] - 10)) - 50
			screen.blit(self.live_surf, (x, 8))

	def victory_message(self):
		if not self.aliens.sprites():
			victory_surf = self.font.render('You won', False, 'white')
			victory_rect = victory_surf.get_rect(center=(screen_width / 2, screen_height / 2))
			screen.blit(victory_surf, victory_rect)

	def run(self):
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
		self.victory_message()


if __name__ == '__main__':
	pygame.init()
	screen_width = 1000
	screen_height = 1000
	screen = pygame.display.set_mode((screen_width, screen_height))
	clock = pygame.time.Clock()
	game = Game()
	alien_laser_ready = 0
	pygame.time.set_timer(alien_laser_ready, 600)
	time_start = 0
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == alien_laser_ready:
				game.shoot()
		screen.fill((30, 30, 30))
		game.run()
		pygame.display.flip()
		clock.tick(60)
