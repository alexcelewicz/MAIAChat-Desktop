import pygame
import random
from typing import List, Tuple

# Constants
GRID_SIZE = 20 # Size of each grid cell (pixels)
WINDOW_WIDTH = GRID_SIZE * 30 # 30 cells wide
WINDOW_HEIGHT = GRID_SIZE * 20 # 20 cells tall
BASE_FPS = 10 # Base speed (updates per second)
MAX_SPEED = 25 # Maximum speed cap (FPS)
SPEED_INCREMENT = 0.02 # Speed increases by 2% per food eaten
GRID_COLOR = (50, 50, 50) # Subtle grid lines
SNAKE_HEAD_COLOR = (0, 255, 0) # Bright green
SNAKE_BODY_COLOR = (0, 200, 0) # Dark green
FOOD_COLOR = (255, 0, 0) # Red
GAME_OVER_COLOR = (255, 255, 255) # White text
PULSE_DURATION = 1000 # Pulsing animation duration (ms)

class SnakeGame:
    def __init__(self) -> None:
        """Initialize game state, window, and assets."""
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Visually Appealing Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        # Load sound effects
        #self.eat_sound = pygame.mixer.Sound("eat.wav")
        #self.game_over_sound = pygame.mixer.Sound("gameover.wav")
        # Initialize game state
        self.reset_game()

    def reset_game(self) -> None:
        """Reset game to initial state (snake, food, score, etc.)."""
        self.snake: List[Tuple[int, int]] = [(10, 10)] # Snake starts at (10,10)
        self.direction: str = "RIGHT" # Initial direction
        self.next_direction: str = "RIGHT" # Next direction (prevents immediate reversal)
        self.score: int = 0
        self.speed: float = BASE_FPS # Start at base speed
        self.game_over: bool = False
        self.food: Tuple[int, int] = self.spawn_food()
        #self.eat_sound.stop()
        #self.game_over_sound.stop()

    def spawn_food(self) -> Tuple[int, int]:
        """Spawn food at a random position not overlapping the snake.
        Safeguards against infinite loops by limiting attempts.
        """
        max_attempts = (WINDOW_WIDTH // GRID_SIZE) * (WINDOW_HEIGHT // GRID_SIZE)
        for _ in range(max_attempts):
            x = random.randint(0, (WINDOW_WIDTH // GRID_SIZE) - 1)
            y = random.randint(0, (WINDOW_HEIGHT // GRID_SIZE) - 1)
            if (x, y) not in self.snake:
                return (x, y)
        raise RuntimeError("Failed to spawn food: snake fills the grid.")

    def handle_input(self) -> bool:
        """Process user input and update direction.
        Returns False if the window is closed.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False # Exit game
            if event.type == pygame.KEYDOWN:
                # Update next direction (prevents 180° reversal)
                if event.key == pygame.K_UP and self.direction != "DOWN":
                    self.next_direction = "UP"
                elif event.key == pygame.K_DOWN and self.direction != "UP":
                    self.next_direction = "DOWN"
                elif event.key == pygame.K_LEFT and self.direction != "RIGHT":
                    self.next_direction = "LEFT"
                elif event.key == pygame.K_RIGHT and self.direction != "LEFT":
                    self.next_direction = "RIGHT"
                # Restart game after game over
                elif event.key == pygame.K_SPACE and self.game_over:
                    self.reset_game()
        return True

    def _check_collisions(self) -> bool:
        """Check for wall or self-collision. Returns True if collision occurs."""
        head_x, head_y = self.snake[0]
        grid_width = WINDOW_WIDTH // GRID_SIZE
        grid_height = WINDOW_HEIGHT // GRID_SIZE
        # Wall collision
        if not (0 <= head_x < grid_width and 0 <= head_y < grid_height):
            return True
        # Self-collision (head overlaps with body segments)
        if self.snake[0] in self.snake[1:]:
            return True
        return False

    def update(self) -> None:
        """Update game state (snake movement, collisions, food)."""
        if self.game_over:
            return
        # Update direction (use next_direction to prevent immediate reversal)
        self.direction = self.next_direction
        # Calculate new head position
        head_x, head_y = self.snake[0]
        if self.direction == "UP":
            new_head = (head_x, head_y - 1)
        elif self.direction == "DOWN":
            new_head = (head_x, head_y + 1)
        elif self.direction == "LEFT":
            new_head = (head_x - 1, head_y)
        elif self.direction == "RIGHT":
            new_head = (head_x + 1, head_y)
        else:
            new_head = (head_x, head_y)
        # Add new head to snake
        self.snake.insert(0, new_head)
        # Check for collisions
        if self._check_collisions():
            self.game_over = True
            #self.game_over_sound.play()
            return
        # Check if food is eaten
        if new_head == self.food:
            self.score += 1
            #self.eat_sound.play()
            # Increase speed (capped at MAX_SPEED)
            self.speed = min(BASE_FPS + (self.score * SPEED_INCREMENT), MAX_SPEED)
            self.food = self.spawn_food()
        else:
            # Remove tail if no food eaten
            self.snake.pop()

    def _draw_grid(self) -> None:
        """Draw subtle grid lines."""
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y), 1)

    def _draw_snake(self) -> None:
        """Draw snake with distinct head and body colors."""
        for i, (x, y) in enumerate(self.snake):
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_BODY_COLOR
            pygame.draw.rect(self.screen, color, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE))

    def _draw_food(self) -> None:
        """Draw pulsing food effect."""
        current_time = pygame.time.get_ticks()
        pulse_size = abs(5 * (current_time % PULSE_DURATION - PULSE_DURATION // 2)) / (PULSE_DURATION // 2) * 5 # Pulses 0-5px
        food_rect = pygame.Rect(
            self.food[0] * GRID_SIZE + pulse_size,
            self.food[1] * GRID_SIZE + pulse_size,
            GRID_SIZE - 2 * pulse_size,
            GRID_SIZE - 2 * pulse_size)
        pygame.draw.rect(self.screen, FOOD_COLOR, food_rect)

    def _draw_hud(self) -> None:
        """Draw score display."""
        score_text = self.font.render(f"Score: {self.score}", True, GAME_OVER_COLOR)
        self.screen.blit(score_text, (10, 10))

    def _draw_game_over(self) -> None:
        """Draw game-over screen with pulsing restart prompt."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        # Game over text
        game_over_text = self.font.render("Game Over!", True, GAME_OVER_COLOR)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        # Pulsing "Press SPACE" prompt
        current_time = pygame.time.get_ticks()
        pulse_value = abs(int(255 * (current_time % PULSE_DURATION - PULSE_DURATION // 2) / (PULSE_DURATION // 2)))
        restart_text_surface = self.small_font.render(
            "Press SPACE to restart", True, GAME_OVER_COLOR
        )
        # Create a surface with alpha for pulsing effect
        restart_text_surface.set_alpha(pulse_value)
        restart_rect = restart_text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        self.screen.blit(restart_text_surface, restart_rect)
        # Final score text
        final_score_text = self.font.render(f"Final Score: {self.score}", True, GAME_OVER_COLOR)
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        self.screen.blit(final_score_text, final_score_rect)

    def render(self) -> None:
        """Draw all game elements to the screen."""
        self.screen.fill(0) # Clear screen with black
        self._draw_grid()
        self._draw_snake()
        self._draw_food()
        self._draw_hud()
        if self.game_over:
            self._draw_game_over()
        pygame.display.flip() # Update display

    def run(self) -> None:
        """Main game loop."""
        running = True
        while running:
            running = self.handle_input() # Handle window close/quit
            self.update() # Update game state
            self.render() # Render visuals
            self.clock.tick(self.speed) # Maintain FPS

    def __del__(self) -> None:
        """Clean up Pygame resources on exit."""
        pygame.quit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()

