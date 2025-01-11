import pygame
import random
import json
import os
from pygame.locals import *
from PIL import Image
import io

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
PLAYER_SIZE = 40
OBSTACLE_SIZE = 40
COIN_SIZE = 30
GROUND_HEIGHT = 40
GRAVITY = 0.8
JUMP_FORCE = -15
MOVE_SPEED = 7
ANIMATION_SPEED = 100  # milliseconds per frame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

def load_gif_frames(gif_path, size):
    """Load all frames from a GIF file"""
    frames = []
    try:
        gif = Image.open(gif_path)
        for frame_index in range(gif.n_frames):
            gif.seek(frame_index)
            frame = gif.convert('RGBA')
            frame = frame.resize((size, size))
            pygame_image = pygame.image.fromstring(
                frame.tobytes(), frame.size, frame.mode)
            frames.append(pygame_image)
        return frames
    except Exception as e:
        print(f"Error loading GIF: {e}")
        default_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        default_surf.fill(BLUE)
        return [default_surf]

def load_image(image_path, size):
    """Load and scale a single image"""
    try:
        image = pygame.image.load(image_path)
        return pygame.transform.scale(image, (size, size))
    except Exception as e:
        print(f"Error loading image: {e}")
        default_surf = pygame.Surface((size, size))
        default_surf.fill(RED)
        return default_surf

class Player:
    def __init__(self, gif_path):
        self.rect = pygame.Rect(WINDOW_WIDTH // 4, 
                              WINDOW_HEIGHT - GROUND_HEIGHT - PLAYER_SIZE, 
                              PLAYER_SIZE, PLAYER_SIZE)
        self.vel_y = 0
        self.on_ground = False
        self.score = 0
        
        self.frames = load_gif_frames(gif_path, PLAYER_SIZE)
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = ANIMATION_SPEED
        
    def move(self, dx):
        self.rect.x += dx
        self.rect.x = max(0, min(self.rect.x, WINDOW_WIDTH - PLAYER_SIZE))
        
    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            
    def update(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        if self.rect.bottom > WINDOW_HEIGHT - GROUND_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT - GROUND_HEIGHT
            self.vel_y = 0
            self.on_ground = True
            
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
    def draw(self, surface):
        surface.blit(self.frames[self.current_frame], self.rect)

class Obstacle:
    def __init__(self, x, image_path):
        self.rect = pygame.Rect(x, WINDOW_HEIGHT - GROUND_HEIGHT - OBSTACLE_SIZE, 
                              OBSTACLE_SIZE, OBSTACLE_SIZE)
        self.image = load_image(image_path, OBSTACLE_SIZE)
        
    def update(self, speed):
        self.rect.x -= speed
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Coin:
    def __init__(self, x, image_path):
        self.rect = pygame.Rect(x, 
                              WINDOW_HEIGHT - GROUND_HEIGHT - COIN_SIZE - random.randint(0, 200), 
                              COIN_SIZE, COIN_SIZE)
        self.image = load_image(image_path, COIN_SIZE)
        
    def update(self, speed):
        self.rect.x -= speed
            
    def draw(self, surface):
        surface.blit(self.image, self.rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Turmac Roll")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.load_high_score()
        
        # Load obstacle images
        self.obstacle_images = [
            'obstacle1.png',
            'obstacle2.png',
            'obstacle3.png'
        ]
        
    def load_high_score(self):
        try:
            with open('high_score.json', 'r') as f:
                self.high_score = json.load(f)['high_score']
        except:
            self.high_score = 0
            
    def save_high_score(self):
        with open('high_score.json', 'w') as f:
            json.dump({'high_score': self.high_score}, f)
            
    def run(self):
        running = True
        game_speed = 5
        spawn_timer = 0
        
        # Create game objects with image paths
        player = Player('rolling_turmac_roll.gif')
        obstacles = []
        coins = []
        
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        player.jump()
                        
            keys = pygame.key.get_pressed()
            if keys[K_LEFT]:
                player.move(-MOVE_SPEED)
            if keys[K_RIGHT]:
                player.move(MOVE_SPEED)
                
            player.update()
            
            spawn_timer += 1
            if spawn_timer >= 60:
                spawn_timer = 0
                if random.random() < 0.5:
                    obstacle_image = random.choice(self.obstacle_images)
                    obstacles.append(Obstacle(WINDOW_WIDTH, obstacle_image))
                else:
                    coins.append(Coin(WINDOW_WIDTH, 'coin.gif'))
                    
            for obstacle in obstacles[:]:
                obstacle.update(game_speed)
                if obstacle.rect.right < 0:
                    obstacles.remove(obstacle)
                elif player.rect.colliderect(obstacle.rect):
                    if player.score > self.high_score:
                        self.high_score = player.score
                        self.save_high_score()
                    return player.score
                    
            for coin in coins[:]:
                coin.update(game_speed)
                if coin.rect.right < 0:
                    coins.remove(coin)
                elif player.rect.colliderect(coin.rect):
                    coins.remove(coin)
                    player.score += 10
                    
            game_speed = 5 + (player.score // 100)
            
            # Draw everything
            self.screen.fill(WHITE)
            pygame.draw.rect(self.screen, GREEN, 
                           (0, WINDOW_HEIGHT - GROUND_HEIGHT, WINDOW_WIDTH, GROUND_HEIGHT))
            
            player.draw(self.screen)
            
            for obstacle in obstacles:
                obstacle.draw(self.screen)
                
            for coin in coins:
                coin.draw(self.screen)
                
            score_text = self.font.render(f'Score: {player.score}', True, BLACK)
            high_score_text = self.font.render(f'High Score: {self.high_score}', True, BLACK)
            self.screen.blit(score_text, (10, 10))
            self.screen.blit(high_score_text, (10, 50))
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        return player.score

def main():
    while True:
        game = Game()
        final_score = game.run()
        
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        font = pygame.font.Font(None, 74)
        
        game_over_text = font.render('Game Over!', True, BLACK)
        score_text = font.render(f'Final Score: {final_score}', True, BLACK)
        restart_text = font.render('Press SPACE to restart', True, BLACK)
        quit_text = font.render('Press Q to quit', True, BLACK)
        
        waiting = True
        while waiting:
            screen.fill(WHITE)
            screen.blit(game_over_text, (WINDOW_WIDTH//2 - game_over_text.get_width()//2, 150))
            screen.blit(score_text, (WINDOW_WIDTH//2 - score_text.get_width()//2, 250))
            screen.blit(restart_text, (WINDOW_WIDTH//2 - restart_text.get_width()//2, 350))
            screen.blit(quit_text, (WINDOW_WIDTH//2 - quit_text.get_width()//2, 450))
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return
                elif event.type == KEYDOWN:
                    if event.key == K_SPACE:
                        waiting = False
                    elif event.key == K_q:
                        pygame.quit()
                        return

if __name__ == '__main__':
    main()