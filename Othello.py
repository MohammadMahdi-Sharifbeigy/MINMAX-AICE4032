import pygame
import sys
import math
import time
import copy

# =============================================================================
# 1. Constants and Setup
# =============================================================================

# --- Screen Dimensions ---
WIDTH, HEIGHT = 800, 600
BOARD_SIZE = 560  # Size of the game board (must be a multiple of 8)
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X = (WIDTH - BOARD_SIZE) // 2
BOARD_Y = (HEIGHT - BOARD_SIZE) // 2

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
DARK_GREEN = (0, 100, 0)
GRAY = (200, 200, 200)
BLUE = (50, 50, 255)
RED = (255, 50, 50)
TRANSPARENT_GRAY = (50, 50, 50, 150)

# --- Game Constants ---
PLAYER_BLACK = 1
PLAYER_WHITE = -1
EMPTY = 0
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# --- AI Settings ---
AI_DEPTH = 4 

# =============================================================================
# 2. Game Logic Class (The "Model")
# =============================================================================

class Othello:
    """
    Manages the game state, rules, and rendering of the Othello board.
    """
    def __init__(self):
        """Initializes the game board and state."""
        self.board = [[EMPTY for _ in range(8)] for _ in range(8)]
        # Standard Othello starting position
        self.board[3][3] = PLAYER_WHITE
        self.board[3][4] = PLAYER_BLACK
        self.board[4][3] = PLAYER_BLACK
        self.board[4][4] = PLAYER_WHITE
        self.current_player = PLAYER_BLACK
        self.valid_moves = []
        self.update_valid_moves()

    def is_on_board(self, r, c):
        """Checks if a given (row, col) is within the 8x8 board."""
        return 0 <= r < 8 and 0 <= c < 8

    def get_valid_moves(self, player):
        """
        Calculates all valid moves for the given player.
        A move is valid if it's on an empty square and flips at least one opponent piece.
        """
        moves = {}
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == EMPTY:
                    pieces_to_flip = self.get_pieces_to_flip(r, c, player)
                    if pieces_to_flip:
                        moves[(r, c)] = pieces_to_flip
        return moves

    def get_pieces_to_flip(self, r, c, player):
        """
        Finds all opponent pieces that would be flipped by placing a piece at (r, c).
        """
        opponent = -player
        pieces_to_flip = []
        for dr, dc in DIRECTIONS:
            line = []
            curr_r, curr_c = r + dr, c + dc
            while self.is_on_board(curr_r, curr_c) and self.board[curr_r][curr_c] == opponent:
                line.append((curr_r, curr_c))
                curr_r += dr
                curr_c += dc
            if self.is_on_board(curr_r, curr_c) and self.board[curr_r][curr_c] == player:
                pieces_to_flip.extend(line)
        return pieces_to_flip

    def make_move(self, r, c):
        """
        Places a piece on the board, flips opponent pieces, and updates the turn.
        Returns True if the move was successful, False otherwise.
        """
        if (r, c) in self.valid_moves:
            self.board[r][c] = self.current_player
            for piece_pos in self.valid_moves[(r, c)]:
                self.board[piece_pos[0]][piece_pos[1]] = self.current_player
            
            # Switch player and update valid moves for the new player
            self.current_player *= -1
            self.update_valid_moves()
            
            # If the new player has no moves, skip their turn
            if not self.valid_moves:
                self.current_player *= -1
                self.update_valid_moves()
            return True
        return False

    def update_valid_moves(self):
        """Updates the list of valid moves for the current player."""
        self.valid_moves = self.get_valid_moves(self.current_player)

    def get_score(self):
        """Returns the score as a tuple (black_score, white_score)."""
        black_score = sum(row.count(PLAYER_BLACK) for row in self.board)
        white_score = sum(row.count(PLAYER_WHITE) for row in self.board)
        return black_score, white_score

    def is_game_over(self):
        """Checks if the game has ended (no valid moves for either player)."""
        return not self.valid_moves

    def draw(self, win, font):
        """Draws the entire game state: board, pieces, scores, and valid moves."""
        # Draw board grid
        for r in range(8):
            for c in range(8):
                color = DARK_GREEN if (r + c) % 2 == 0 else GREEN
                pygame.draw.rect(win, color, (BOARD_X + c * SQUARE_SIZE, BOARD_Y + r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
                pygame.draw.rect(win, BLACK, (BOARD_X + c * SQUARE_SIZE, BOARD_Y + r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 1)

        # Draw pieces
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != EMPTY:
                    color = BLACK if self.board[r][c] == PLAYER_BLACK else WHITE
                    center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
                    center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
                    pygame.draw.circle(win, color, (center_x, center_y), SQUARE_SIZE // 2 - 5)

        # Highlight valid moves for the current player
        for r, c in self.valid_moves.keys():
            surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            color = (0, 0, 0, 60) if self.current_player == PLAYER_BLACK else (255, 255, 255, 60)
            pygame.draw.circle(surface, color, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 10)
            win.blit(surface, (BOARD_X + c * SQUARE_SIZE, BOARD_Y + r * SQUARE_SIZE))
            
        # Draw score and turn info
        self.draw_hud(win, font)

    def draw_hud(self, win, font):
        """Draws the Heads-Up Display (score, turn indicator)."""
        black_score, white_score = self.get_score()

        # Score Box
        pygame.draw.rect(win, GRAY, (BOARD_X, 10, BOARD_SIZE, 50), border_radius=10)
        
        # Black Score
        pygame.draw.circle(win, BLACK, (BOARD_X + 40, 35), 18)
        score_text = font.render(f"{black_score}", True, BLACK)
        win.blit(score_text, (BOARD_X + 70, 20))

        # White Score
        pygame.draw.circle(win, WHITE, (BOARD_X + BOARD_SIZE - 40, 35), 18)
        score_text = font.render(f"{white_score}", True, BLACK)
        win.blit(score_text, (BOARD_X + BOARD_SIZE - 80, 20))

        # Turn Indicator
        turn_text = "Black's Turn" if self.current_player == PLAYER_BLACK else "White's Turn"
        text_surface = font.render(turn_text, True, WHITE)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, 35))
        pygame.draw.rect(win, BLUE, (text_rect.x - 10, text_rect.y - 5, text_rect.width + 20, text_rect.height + 10), border_radius=8)
        win.blit(text_surface, text_rect)

# =============================================================================
# 3. AI Logic (Minimax with Alpha-Beta Pruning)
# =============================================================================

def evaluate_board(board, player):
    """
    Heuristic function to evaluate the 'goodness' of a board state for the AI.
    A positive score is good for the AI, negative is bad.
    """
    score = 0
    opponent = -player

    # Heuristic weights
    PIECE_COUNT_WEIGHT = 1
    MOBILITY_WEIGHT = 5
    CORNER_WEIGHT = 50

    # 1. Piece Count
    my_pieces = sum(row.count(player) for row in board)
    opp_pieces = sum(row.count(opponent) for row in board)
    score += PIECE_COUNT_WEIGHT * (my_pieces - opp_pieces)

    # 2. Mobility (number of available moves)
    # Create a temporary game object to use its methods
    temp_game = Othello()
    temp_game.board = board
    my_moves = len(temp_game.get_valid_moves(player))
    opp_moves = len(temp_game.get_valid_moves(opponent))
    score += MOBILITY_WEIGHT * (my_moves - opp_moves)

    # 3. Corner Control
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    my_corners = 0
    opp_corners = 0
    for r, c in corners:
        if board[r][c] == player:
            my_corners += 1
        elif board[r][c] == opponent:
            opp_corners += 1
    score += CORNER_WEIGHT * (my_corners - opp_corners)
    
    return score


def minimax(game_state, depth, alpha, beta, maximizing_player, ai_player):
    """
    Minimax algorithm with alpha-beta pruning.
    Returns the best score and the corresponding move (r, c).
    """
    if depth == 0 or game_state.is_game_over():
        return evaluate_board(game_state.board, ai_player), None

    valid_moves = game_state.get_valid_moves(game_state.current_player)
    
    if not valid_moves:
        # If no moves, pass the turn and continue search
        next_state = copy.deepcopy(game_state)
        next_state.current_player *= -1
        return minimax(next_state, depth - 1, alpha, beta, not maximizing_player, ai_player)

    best_move = list(valid_moves.keys())[0]

    if maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            # Create a new game state for the simulated move
            next_state = copy.deepcopy(game_state)
            next_state.make_move(move[0], move[1])
            
            evaluation, _ = minimax(next_state, depth - 1, alpha, beta, False, ai_player)
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # Prune
        return max_eval, best_move
    else:  # Minimizing player
        min_eval = math.inf
        for move in valid_moves:
            next_state = copy.deepcopy(game_state)
            next_state.make_move(move[0], move[1])
            
            evaluation, _ = minimax(next_state, depth - 1, alpha, beta, True, ai_player)
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # Prune
        return min_eval, best_move

# =============================================================================
# 4. Main Game Loop and UI
# =============================================================================

def draw_button(win, rect, text, font, button_color, text_color):
    """Helper function to draw a button."""
    pygame.draw.rect(win, button_color, rect, border_radius=15)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    win.blit(text_surf, text_rect)

def main_menu(win, font, big_font):
    """Displays the main menu and returns the selected game mode."""
    pvp_button = pygame.Rect(WIDTH // 2 - 150, 200, 300, 50)
    pvb_button = pygame.Rect(WIDTH // 2 - 150, 270, 300, 50)
    bvb_button = pygame.Rect(WIDTH // 2 - 150, 340, 300, 50)

    while True:
        win.fill(DARK_GREEN)
        
        title_text = big_font.render("Othello AI", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 100))
        win.blit(title_text, title_rect)

        draw_button(win, pvp_button, "Player vs Player", font, BLUE, WHITE)
        draw_button(win, pvb_button, "Player vs Bot", font, BLUE, WHITE)
        draw_button(win, bvb_button, "Bot vs Bot", font, BLUE, WHITE)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pvp_button.collidepoint(event.pos):
                    return "pvp"
                if pvb_button.collidepoint(event.pos):
                    return "pvb"
                if bvb_button.collidepoint(event.pos):
                    return "bvb"

def main():
    """Main function to run the game."""
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Othello")
    font = pygame.font.SysFont("Arial", 24, bold=True)
    big_font = pygame.font.SysFont("Arial", 50, bold=True)
    clock = pygame.time.Clock()

    game_mode = main_menu(win, font, big_font)
    game = Othello()
    run = True
    
    # Bot vs Bot specific timer
    last_bot_move_time = time.time()
    bot_move_delay = 1.0 # seconds

    while run:
        clock.tick(60)

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if game.is_game_over():
                continue

            # --- Player vs Player ---
            if game_mode == "pvp":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
                        row = (y - BOARD_Y) // SQUARE_SIZE
                        col = (x - BOARD_X) // SQUARE_SIZE
                        game.make_move(row, col)

            # --- Player vs Bot ---
            elif game_mode == "pvb":
                if game.current_player == PLAYER_BLACK: # Human player
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
                            row = (y - BOARD_Y) // SQUARE_SIZE
                            col = (x - BOARD_X) // SQUARE_SIZE
                            game.make_move(row, col)
                else: # Bot player (White)
                    pygame.display.update() # Show board before AI thinks
                    _, best_move = minimax(game, AI_DEPTH, -math.inf, math.inf, True, PLAYER_WHITE)
                    if best_move:
                        game.make_move(best_move[0], best_move[1])

        # --- Bot vs Bot ---
        if game_mode == "bvb" and not game.is_game_over():
            current_time = time.time()
            if current_time - last_bot_move_time > bot_move_delay:
                ai_player = game.current_player
                _, best_move = minimax(game, AI_DEPTH, -math.inf, math.inf, True, ai_player)
                if best_move:
                    game.make_move(best_move[0], best_move[1])
                last_bot_move_time = current_time

        # --- Drawing ---
        win.fill(DARK_GREEN)
        game.draw(win, font)

        # --- Game Over Screen ---
        if game.is_game_over():
            # Create a semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            win.blit(overlay, (0, 0))
            
            black_score, white_score = game.get_score()
            if black_score > white_score:
                winner_text = "Black Wins!"
            elif white_score > black_score:
                winner_text = "White Wins!"
            else:
                winner_text = "It's a Tie!"
            
            end_text = big_font.render(winner_text, True, WHITE)
            end_rect = end_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            win.blit(end_text, end_rect)
            
            score_text_surf = font.render(f"Final Score: Black {black_score} - {white_score} White", True, GRAY)
            score_rect = score_text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            win.blit(score_text_surf, score_rect)

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
