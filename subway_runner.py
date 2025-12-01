import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (173, 216, 230)

# Lane positions (3 lanes)
LANE_WIDTH = SCREEN_WIDTH // 3
LANE_POSITIONS = [
    LANE_WIDTH // 2,           # Left lane center
    SCREEN_WIDTH // 2,         # Middle lane center  
    SCREEN_WIDTH - LANE_WIDTH // 2  # Right lane center
]

class Player:
    """Player character that can move between 3 lanes"""
    def __init__(self):
        self.width = 40
        self.height = 60
        self.current_lane = 1  # Start in middle lane (0=left, 1=middle, 2=right)
        self.x = LANE_POSITIONS[self.current_lane] - self.width // 2
        self.y = SCREEN_HEIGHT - 150  # Position near bottom of screen
        self.move_speed = 12
        self.moving = False
        self.target_x = self.x
        
        # Animation and effects
        self.bob_offset = 0
        self.bob_speed = 0.2
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.flash_timer = 0
        
    def move_left(self, game=None):
        """Move player to left lane"""
        if self.current_lane > 0 and not self.moving:
            self.current_lane -= 1
            self.target_x = LANE_POSITIONS[self.current_lane] - self.width // 2
            self.moving = True
            if game:
                game.play_sound(game.move_sound)
    
    def move_right(self, game=None):
        """Move player to right lane"""
        if self.current_lane < 2 and not self.moving:
            self.current_lane += 1
            self.target_x = LANE_POSITIONS[self.current_lane] - self.width // 2
            self.moving = True
            if game:
                game.play_sound(game.move_sound)
    
    def update(self):
        """Update player position for smooth lane switching"""
        if self.moving:
            # Move towards target position
            if abs(self.x - self.target_x) < self.move_speed:
                self.x = self.target_x
                self.moving = False
            elif self.x < self.target_x:
                self.x += self.move_speed
            else:
                self.x -= self.move_speed
        
        # Update running animation (bobbing effect)
        self.bob_offset = math.sin(pygame.time.get_ticks() * self.bob_speed) * 3
        
        # Update invulnerability
        if self.invulnerable:
            self.invulnerable_timer -= 1
            self.flash_timer += 1
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                self.flash_timer = 0
    
    def draw(self, screen):
        """Draw the player with animation and effects"""
        # Apply bobbing animation
        draw_y = self.y + self.bob_offset
        
        # Flash effect when invulnerable
        if self.invulnerable and self.flash_timer % 10 < 5:
            return  # Skip drawing to create flashing effect
        
        # Draw player body with gradient effect
        player_color = LIGHT_BLUE if self.invulnerable else BLUE
        pygame.draw.rect(screen, player_color, (self.x, draw_y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, draw_y, self.width, self.height), 2)
        
        # Add a simple face
        pygame.draw.circle(screen, WHITE, (self.x + 20, draw_y + 15), 8)
        pygame.draw.circle(screen, BLACK, (self.x + 20, draw_y + 15), 3)
        
        # Add running legs animation
        leg_offset = int(math.sin(pygame.time.get_ticks() * 0.3) * 5)
        pygame.draw.rect(screen, player_color, (self.x + 10 + leg_offset, draw_y + 50, 8, 15))
        pygame.draw.rect(screen, player_color, (self.x + 22 - leg_offset, draw_y + 50, 8, 15))
    
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Obstacle:
    """Obstacles that spawn in lanes and move down the screen"""
    def __init__(self, lane, obstacle_type="normal"):
        self.width = 50
        self.height = 50
        self.lane = lane
        self.x = LANE_POSITIONS[lane] - self.width // 2
        self.y = -self.height  # Start above screen
        self.speed = 8
        self.type = obstacle_type
        self.rotation = 0
        
    def update(self):
        """Move obstacle down the screen"""
        self.y += self.speed
        self.rotation += 2  # Rotating animation
        
    def draw(self, screen):
        """Draw obstacle with different types"""
        if self.type == "spike":
            # Draw spiky obstacle
            points = []
            center_x, center_y = self.x + self.width//2, self.y + self.height//2
            for i in range(8):
                angle = (i * 45 + self.rotation) * math.pi / 180
                if i % 2 == 0:
                    radius = 25
                else:
                    radius = 15
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            pygame.draw.polygon(screen, RED, points)
            pygame.draw.polygon(screen, BLACK, points, 2)
        else:
            # Normal obstacle
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, BLACK, (self.x + 5, self.y + 5, self.width - 10, self.height - 10), 2)
        
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x + 5, self.y + 5, self.width - 10, self.height - 10)
    
    def is_off_screen(self):
        """Check if obstacle has moved off the bottom of screen"""
        return self.y > SCREEN_HEIGHT

class Coin:
    """Collectible coins that give points"""
    def __init__(self, lane):
        self.width = 30
        self.height = 30
        self.lane = lane
        self.x = LANE_POSITIONS[lane] - self.width // 2
        self.y = -self.height
        self.speed = 8
        self.rotation = 0
        self.bob_offset = 0
        
    def update(self):
        """Move coin down and animate"""
        self.y += self.speed
        self.rotation += 5
        self.bob_offset = math.sin(pygame.time.get_ticks() * 0.1) * 2
        
    def draw(self, screen):
        """Draw animated coin"""
        draw_y = self.y + self.bob_offset
        # Draw coin with rotation effect
        pygame.draw.circle(screen, YELLOW, (self.x + 15, draw_y + 15), 15)
        pygame.draw.circle(screen, ORANGE, (self.x + 15, draw_y + 15), 12)
        pygame.draw.circle(screen, YELLOW, (self.x + 15, draw_y + 15), 8)
        pygame.draw.circle(screen, BLACK, (self.x + 15, draw_y + 15), 15, 2)
        
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def is_off_screen(self):
        """Check if coin has moved off screen"""
        return self.y > SCREEN_HEIGHT

class PowerUp:
    """Power-ups that give special abilities"""
    def __init__(self, lane, power_type):
        self.width = 40
        self.height = 40
        self.lane = lane
        self.x = LANE_POSITIONS[lane] - self.width // 2
        self.y = -self.height
        self.speed = 8
        self.type = power_type  # "shield", "magnet", "double_score"
        self.pulse = 0
        
    def update(self):
        """Move power-up down and animate"""
        self.y += self.speed
        self.pulse += 0.2
        
    def draw(self, screen):
        """Draw power-up with type-specific appearance"""
        pulse_size = int(math.sin(self.pulse) * 3)
        
        if self.type == "shield":
            # Shield power-up (blue)
            pygame.draw.circle(screen, CYAN, (self.x + 20, self.y + 20), 20 + pulse_size)
            pygame.draw.circle(screen, BLUE, (self.x + 20, self.y + 20), 15 + pulse_size)
            pygame.draw.circle(screen, BLACK, (self.x + 20, self.y + 20), 20 + pulse_size, 2)
        elif self.type == "magnet":
            # Magnet power-up (purple)
            pygame.draw.rect(screen, PURPLE, (self.x + 5, self.y + 5, 30, 30))
            pygame.draw.circle(screen, WHITE, (self.x + 20, self.y + 20), 8)
            pygame.draw.circle(screen, BLACK, (self.x + 20, self.y + 20), 15, 2)
        elif self.type == "double_score":
            # Double score power-up (green)
            pygame.draw.circle(screen, GREEN, (self.x + 20, self.y + 20), 20 + pulse_size)
            pygame.draw.circle(screen, WHITE, (self.x + 20, self.y + 20), 15 + pulse_size)
            # Draw "2X" text
            font = pygame.font.Font(None, 24)
            text = font.render("2X", True, BLACK)
            text_rect = text.get_rect(center=(self.x + 20, self.y + 20))
            screen.blit(text, text_rect)
        
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def is_off_screen(self):
        """Check if power-up has moved off screen"""
        return self.y > SCREEN_HEIGHT

class Particle:
    """Particle effects for visual enhancement"""
    def __init__(self, x, y, color, velocity_x=0, velocity_y=0):
        self.x = x
        self.y = y
        self.color = color
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.life = 30
        self.max_life = 30
        
    def update(self):
        """Update particle position and life"""
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.life -= 1
        
    def draw(self, screen):
        """Draw particle with fading effect"""
        if self.life > 0:
            alpha = int(255 * (self.life / self.max_life))
            size = max(1, int(5 * (self.life / self.max_life)))
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)
    
    def is_dead(self):
        """Check if particle should be removed"""
        return self.life <= 0

class Game:
    """Main game class that handles game logic"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Subway Runner - Enhanced Endless Runner")
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.power_ups = []
        self.particles = []
        
        # Game state
        self.score = 0
        self.coins_collected = 0
        self.high_score = 0
        self.game_over = False
        self.background_y = 0
        self.speed_multiplier = 1.0
        
        # Spawn timers
        self.obstacle_spawn_timer = 0
        self.obstacle_spawn_delay = 60
        self.coin_spawn_timer = 0
        self.coin_spawn_delay = 90
        self.powerup_spawn_timer = 0
        self.powerup_spawn_delay = 600  # Less frequent power-ups
        
        # Power-up effects
        self.shield_active = False
        self.shield_timer = 0
        self.magnet_active = False
        self.magnet_timer = 0
        self.double_score_active = False
        self.double_score_timer = 0
        
        # Font for text
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 72)
        
        # Initialize sound system with working audio
        self.sound_enabled = True
        print("Initializing sound system...")
        
        try:
            # Set up pygame mixer properly
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            
            # Create actual sound effects
            self.coin_sound = self.create_beep_sound(800, 0.1)
            self.powerup_sound = self.create_beep_sound(600, 0.2)
            self.crash_sound = self.create_beep_sound(200, 0.3)
            self.magnet_sound = self.create_beep_sound(450, 0.05)
            self.shield_sound = self.create_beep_sound(500, 0.25)
            self.move_sound = self.create_beep_sound(350, 0.05)
            
            print("Sound system initialized successfully!")
            
        except Exception as e:
            print(f"Sound initialization failed: {e}")
            print("Running without sound effects...")
            self.sound_enabled = False
            self.coin_sound = None
            self.powerup_sound = None
            self.crash_sound = None
            self.magnet_sound = None
            self.shield_sound = None
            self.move_sound = None
    
    def create_beep_sound(self, frequency, duration):
        """Create a simple beep sound with proper 2D array format"""
        try:
            import numpy as np
            
            # Audio parameters
            sample_rate = 22050
            frames = int(duration * sample_rate)
            
            # Generate time array
            t = np.linspace(0, duration, frames, False)
            
            # Generate sine wave
            wave = np.sin(frequency * 2 * np.pi * t)
            
            # Convert to 16-bit integers
            wave = (wave * 16000).astype(np.int16)
            
            # Create stereo array (2D: frames x 2 channels)
            stereo_wave = np.column_stack((wave, wave))
            
            # Create pygame sound
            sound = pygame.sndarray.make_sound(stereo_wave)
            return sound
            
        except ImportError:
            print("NumPy not available, using basic sound generation")
            return self.create_basic_beep(frequency, duration)
        except Exception as e:
            print(f"Sound creation error: {e}")
            return None
    
    def create_basic_beep(self, frequency, duration):
        """Fallback sound creation without NumPy"""
        try:
            # Create a simple click sound as fallback
            sample_rate = 22050
            frames = int(0.05 * sample_rate)  # Short click
            
            # Create 2D array manually
            sound_array = []
            for i in range(frames):
                # Simple envelope to avoid clicks
                if i < frames // 4:
                    amplitude = i / (frames // 4)
                elif i > 3 * frames // 4:
                    amplitude = (frames - i) / (frames // 4)
                else:
                    amplitude = 1.0
                
                value = int(8000 * amplitude)
                sound_array.append([value, value])  # [left, right]
            
            # Convert to numpy array for pygame
            import numpy as np
            stereo_array = np.array(sound_array, dtype=np.int16)
            
            sound = pygame.sndarray.make_sound(stereo_array)
            return sound
            
        except Exception as e:
            print(f"Basic sound creation error: {e}")
            return None
    
    def play_sound(self, sound):
        """Play a sound effect if available"""
        if sound and self.sound_enabled:
            try:
                sound.play()
            except Exception as e:
                print(f"Sound play error: {e}")
                self.sound_enabled = False
        
    def handle_events(self):
        """Handle keyboard input and events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.restart_game()
                else:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player.move_left(self)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player.move_right(self)
        
        return True
    
    def spawn_obstacle(self):
        """Spawn a new obstacle in a random lane"""
        lane = random.randint(0, 2)  # Random lane (0, 1, or 2)
        # 20% chance for spike obstacle
        obstacle_type = "spike" if random.random() < 0.2 else "normal"
        self.obstacles.append(Obstacle(lane, obstacle_type))
    
    def spawn_coin(self):
        """Spawn a coin in a random lane"""
        lane = random.randint(0, 2)
        self.coins.append(Coin(lane))
    
    def spawn_powerup(self):
        """Spawn a random power-up"""
        lane = random.randint(0, 2)
        power_types = ["shield", "magnet", "double_score"]
        power_type = random.choice(power_types)
        self.power_ups.append(PowerUp(lane, power_type))
    
    def create_particles(self, x, y, color, count=5):
        """Create particle effects at given position"""
        for _ in range(count):
            vel_x = random.uniform(-3, 3)
            vel_y = random.uniform(-3, 3)
            self.particles.append(Particle(x, y, color, vel_x, vel_y))
    
    def activate_powerup(self, power_type):
        """Activate a power-up effect"""
        if power_type == "shield":
            self.shield_active = True
            self.shield_timer = 300  # 5 seconds at 60 FPS
            self.player.invulnerable = True
            self.player.invulnerable_timer = 300
            self.play_sound(self.shield_sound)
        elif power_type == "magnet":
            self.magnet_active = True
            self.magnet_timer = 300
            self.play_sound(self.powerup_sound)  # Special sound for magnet activation
        elif power_type == "double_score":
            self.double_score_active = True
            self.double_score_timer = 300
    
    def update_game(self):
        """Update all game objects"""
        if self.game_over:
            return
            
        # Update player
        self.player.update()
        
        # Update obstacles
        for obstacle in self.obstacles[:]:
            obstacle.update()
            if obstacle.is_off_screen():
                self.obstacles.remove(obstacle)
                score_gain = 10
                if self.double_score_active:
                    score_gain *= 2
                self.score += score_gain
        
        # Update coins
        for coin in self.coins[:]:
            coin.update()
            if coin.is_off_screen():
                self.coins.remove(coin)
        
        # Update power-ups
        for powerup in self.power_ups[:]:
            powerup.update()
            if powerup.is_off_screen():
                self.power_ups.remove(powerup)
        
        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.is_dead():
                self.particles.remove(particle)
        
        # Spawn new obstacles
        self.obstacle_spawn_timer += 1
        if self.obstacle_spawn_timer >= self.obstacle_spawn_delay:
            self.spawn_obstacle()
            self.obstacle_spawn_timer = 0
            if self.obstacle_spawn_delay > 30:
                self.obstacle_spawn_delay -= 0.3
        
        # Spawn coins
        self.coin_spawn_timer += 1
        if self.coin_spawn_timer >= self.coin_spawn_delay:
            self.spawn_coin()
            self.coin_spawn_timer = 0
        
        # Spawn power-ups
        self.powerup_spawn_timer += 1
        if self.powerup_spawn_timer >= self.powerup_spawn_delay:
            self.spawn_powerup()
            self.powerup_spawn_timer = 0
        
        # Update power-up timers
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
        
        if self.magnet_active:
            self.magnet_timer -= 1
            if self.magnet_timer <= 0:
                self.magnet_active = False
        
        if self.double_score_active:
            self.double_score_timer -= 1
            if self.double_score_timer <= 0:
                self.double_score_active = False
        
        # Check collisions
        player_rect = self.player.get_rect()
        
        # Obstacle collisions
        for obstacle in self.obstacles[:]:
            if player_rect.colliderect(obstacle.get_rect()):
                if not self.player.invulnerable:
                    self.game_over = True
                    self.play_sound(self.crash_sound)
                    self.create_particles(self.player.x + 20, self.player.y + 30, RED, 10)
                    if self.score > self.high_score:
                        self.high_score = self.score
                else:
                    # Destroy obstacle if player is invulnerable
                    self.obstacles.remove(obstacle)
                    self.create_particles(obstacle.x + 25, obstacle.y + 25, CYAN, 8)
                break
        
        # Coin collisions
        for coin in self.coins[:]:
            coin_rect = coin.get_rect()
            collected = False
            
            # Magnet effect - attract coins
            if self.magnet_active:
                player_center_x = self.player.x + self.player.width // 2
                player_center_y = self.player.y + self.player.height // 2
                coin_center_x = coin.x + coin.width // 2
                coin_center_y = coin.y + coin.height // 2
                
                dx = player_center_x - coin_center_x
                dy = player_center_y - coin_center_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Much larger magnet range and stronger attraction
                if distance < 200:  # Increased magnet range
                    # Auto-collect if within collection radius
                    if distance < 80:  # Larger auto-collection radius
                        collected = True
                        # Play magnet collection sound
                        if random.random() < 0.3:  # 30% chance to avoid spam
                            self.play_sound(self.magnet_sound)
                    elif distance > 0:  # Attract if not collected yet
                        # Much stronger attraction that scales with distance
                        attraction_strength = min(1.5, 3.0 / (distance / 50))  # Stronger when closer
                        coin.x += dx * attraction_strength
                        coin.y += dy * attraction_strength
                        
                        # Create continuous magnet particle effects
                        self.create_particles(coin_center_x, coin_center_y, PURPLE, 3)
            
            # Normal collision detection or magnet collection
            if collected or player_rect.colliderect(coin_rect):
                self.coins.remove(coin)
                self.coins_collected += 1
                score_gain = 50
                if self.double_score_active:
                    score_gain *= 2
                self.score += score_gain
                self.play_sound(self.coin_sound)
                self.create_particles(coin.x + 15, coin.y + 15, YELLOW, 6)
        
        # Power-up collisions
        for powerup in self.power_ups[:]:
            if player_rect.colliderect(powerup.get_rect()):
                self.power_ups.remove(powerup)
                self.activate_powerup(powerup.type)
                self.play_sound(self.powerup_sound)
                self.create_particles(powerup.x + 20, powerup.y + 20, GREEN, 8)
        
        # Update background scroll position
        self.background_y += 5
        if self.background_y >= SCREEN_HEIGHT:
            self.background_y = 0
        
        # Increase score over time
        score_gain = 1
        if self.double_score_active:
            score_gain *= 2
        self.score += score_gain
    
    def draw_background(self):
        """Draw scrolling background with lane lines"""
        # Fill background
        self.screen.fill(GRAY)
        
        # Draw lane dividers
        for i in range(1, 3):  # Draw 2 divider lines for 3 lanes
            x = i * LANE_WIDTH
            # Draw dashed lines that scroll
            for y in range(-20, SCREEN_HEIGHT + 20, 40):
                line_y = (y + self.background_y) % (SCREEN_HEIGHT + 40) - 20
                pygame.draw.rect(self.screen, WHITE, (x - 2, line_y, 4, 20))
    
    def draw_ui(self):
        """Draw user interface elements"""
        # Draw score and stats
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        coins_text = self.small_font.render(f"Coins: {self.coins_collected}", True, YELLOW)
        self.screen.blit(coins_text, (10, 50))
        
        high_score_text = self.small_font.render(f"High Score: {self.high_score}", True, WHITE)
        self.screen.blit(high_score_text, (10, 75))
        
        # Draw active power-ups
        y_offset = 100
        if self.shield_active:
            shield_text = self.small_font.render(f"Shield: {self.shield_timer // 60 + 1}s", True, CYAN)
            self.screen.blit(shield_text, (10, y_offset))
            y_offset += 25
        
        if self.magnet_active:
            magnet_text = self.small_font.render(f"Magnet: {self.magnet_timer // 60 + 1}s", True, PURPLE)
            self.screen.blit(magnet_text, (10, y_offset))
            y_offset += 25
        
        if self.double_score_active:
            double_text = self.small_font.render(f"2X Score: {self.double_score_timer // 60 + 1}s", True, GREEN)
            self.screen.blit(double_text, (10, y_offset))
        
        # Draw controls hint
        controls_text = self.small_font.render("Use A/D or Arrow Keys to move", True, WHITE)
        self.screen.blit(controls_text, (10, SCREEN_HEIGHT - 50))
        
        # Draw legend
        legend_text = self.small_font.render("Collect coins, avoid obstacles, grab power-ups!", True, WHITE)
        self.screen.blit(legend_text, (10, SCREEN_HEIGHT - 25))
        
        if self.game_over:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            # Draw game over screen
            game_over_text = self.big_font.render("GAME OVER!", True, RED)
            final_score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            coins_final_text = self.font.render(f"Coins Collected: {self.coins_collected}", True, YELLOW)
            high_score_final_text = self.font.render(f"High Score: {self.high_score}", True, WHITE)
            restart_text = self.font.render("Press SPACE to restart", True, WHITE)
            
            # Center the text
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80))
            score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            coins_rect = coins_final_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            high_rect = high_score_final_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(final_score_text, score_rect)
            self.screen.blit(coins_final_text, coins_rect)
            self.screen.blit(high_score_final_text, high_rect)
            self.screen.blit(restart_text, restart_rect)
    
    def draw(self):
        """Draw all game elements"""
        # Draw background
        self.draw_background()
        
        # Draw particles (behind everything)
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw magnet field effect (behind player)
        if self.magnet_active and not self.game_over:
            player_center_x = self.player.x + self.player.width // 2
            player_center_y = self.player.y + self.player.height // 2
            # Draw pulsing magnet field
            pulse = int(math.sin(pygame.time.get_ticks() * 0.01) * 20)
            pygame.draw.circle(self.screen, (128, 0, 128, 50), (player_center_x, player_center_y), 100 + pulse, 3)
            pygame.draw.circle(self.screen, (128, 0, 128, 30), (player_center_x, player_center_y), 150 + pulse, 2)
        
        # Draw game objects
        if not self.game_over:
            self.player.draw(self.screen)
            
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
            
        for coin in self.coins:
            coin.draw(self.screen)
            
        for powerup in self.power_ups:
            powerup.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        # Update display
        pygame.display.flip()
    
    def restart_game(self):
        """Reset game to initial state"""
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.power_ups = []
        self.particles = []
        
        # Reset game state (keep high score)
        self.score = 0
        self.coins_collected = 0
        self.game_over = False
        self.background_y = 0
        self.speed_multiplier = 1.0
        
        # Reset spawn timers
        self.obstacle_spawn_timer = 0
        self.obstacle_spawn_delay = 60
        self.coin_spawn_timer = 0
        self.coin_spawn_delay = 90
        self.powerup_spawn_timer = 0
        self.powerup_spawn_delay = 600
        
        # Reset power-up effects
        self.shield_active = False
        self.shield_timer = 0
        self.magnet_active = False
        self.magnet_timer = 0
        self.double_score_active = False
        self.double_score_timer = 0
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Handle events
            running = self.handle_events()
            
            # Update game
            self.update_game()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()