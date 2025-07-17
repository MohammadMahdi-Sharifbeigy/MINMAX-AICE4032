import pygame
import pygame.gfxdraw
import sys
import math
import time
import copy
import threading
from enum import Enum

# =============================================================================
# 1. Constants and Setup
# =============================================================================

# --- Screen Dimensions ---
WIDTH, HEIGHT = 1200, 800
BOARD_SIZE = 560
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X = 50
BOARD_Y = (HEIGHT - BOARD_SIZE) // 2
DEBUG_PANEL_X = BOARD_X + BOARD_SIZE + 50
DEBUG_PANEL_WIDTH = 450 # Increased width for better display

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BOARD_BG_LIGHT = (0, 150, 0)
BOARD_BG_DARK = (0, 120, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (150, 150, 150)
BLUE = (70, 130, 180)
DARK_BLUE = (25, 25, 112)
RED = (220, 20, 60)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
ORANGE = (255, 140, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
BOARD_BORDER = (139, 69, 19) # A nice brown for the board border

# --- Game Constants ---
PLAYER_BLACK = 1
PLAYER_WHITE = -1
EMPTY = 0
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# --- AI Settings ---
class Difficulty(Enum):
    EASY = 2
    MEDIUM = 4
    HARD = 6
    EXPERT = 8

AI_DIFFICULTY = Difficulty.MEDIUM

# =============================================================================
# 2. Enhanced Game Logic Class
# =============================================================================

class Othello:
    """ Manages the entire game state, logic, and rendering. """
    def __init__(self):
        self.board = [[EMPTY for _ in range(8)] for _ in range(8)]
        self.board[3][3], self.board[4][4] = PLAYER_WHITE, PLAYER_WHITE
        self.board[3][4], self.board[4][3] = PLAYER_BLACK, PLAYER_BLACK
        self.current_player = PLAYER_BLACK
        self.valid_moves = self.get_valid_moves(self.current_player)
        self.ai_decision_log = []
        self.move_history = []
        self.ai_thinking = False
        self.last_move = None
        self.game_over = False
        self.winner = None
        self.animations = []
        self.hover_pos = None

    def is_on_board(self, r, c):
        """ Check if a coordinate is on the 8x8 board. """
        return 0 <= r < 8 and 0 <= c < 8

    def get_valid_moves(self, player):
        """ Get a dictionary of all valid moves for a player. """
        moves = {}
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == EMPTY:
                    pieces_to_flip = self._get_pieces_to_flip(r, c, player)
                    if pieces_to_flip:
                        moves[(r, c)] = pieces_to_flip
        return moves

    def _get_pieces_to_flip(self, r, c, player):
        """ Helper to find which pieces a move would flip. """
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
        """ Executes a move, flips pieces, and switches the player. """
        if (r, c) in self.valid_moves:
            self.move_history.append(copy.deepcopy(self.board))
            self.board[r][c] = self.current_player
            self.last_move = (r, c)
            
            pieces_to_flip = self.valid_moves[(r, c)]
            for piece_pos in pieces_to_flip:
                self.board[piece_pos[0]][piece_pos[1]] = self.current_player
                # Add a flip animation for each piece
                self.animations.append({
                    'type': 'flip', 'pos': piece_pos, 'start_time': time.time(),
                    'duration': 0.4, 'from_player': -self.current_player, 'to_player': self.current_player
                })

            self._switch_player()
            return True
        return False

    def _switch_player(self):
        """ Switches player and checks for game over conditions. """
        self.current_player *= -1
        self.valid_moves = self.get_valid_moves(self.current_player)
        if not self.valid_moves:
            self.current_player *= -1 # Pass turn back
            self.valid_moves = self.get_valid_moves(self.current_player)
            if not self.valid_moves:
                self.game_over = True
                self._determine_winner()

    def get_score(self):
        """ Returns the scores for black and white players. """
        black_score = sum(row.count(PLAYER_BLACK) for row in self.board)
        white_score = sum(row.count(PLAYER_WHITE) for row in self.board)
        return black_score, white_score

    def _determine_winner(self):
        """ Determines the winner based on the final score. """
        black_score, white_score = self.get_score()
        if black_score > white_score: self.winner = PLAYER_BLACK
        elif white_score > black_score: self.winner = PLAYER_WHITE
        else: self.winner = EMPTY # Tie

    def draw(self, win, font, small_font):
        """ Main drawing function, called every frame. """
        self._draw_board_and_grid(win)
        self._draw_pieces_and_animations(win)
        self._draw_hover_and_valid_moves(win)
        self.draw_hud(win, font, small_font)
        self.draw_ai_debug_panel(win, font, small_font)

    def _draw_board_and_grid(self, win):
        """ Draws the board background, border, and grid lines. """
        board_rect = pygame.Rect(BOARD_X - 10, BOARD_Y - 10, BOARD_SIZE + 20, BOARD_SIZE + 20)
        pygame.draw.rect(win, BOARD_BORDER, board_rect, border_radius=15)
        
        for r in range(8):
            for c in range(8):
                x, y = BOARD_X + c * SQUARE_SIZE, BOARD_Y + r * SQUARE_SIZE
                color = BOARD_BG_LIGHT if (r + c) % 2 == 0 else BOARD_BG_DARK
                pygame.draw.rect(win, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                pygame.draw.rect(win, DARK_GRAY, (x, y, SQUARE_SIZE, SQUARE_SIZE), 1)
                
                if self.last_move == (r, c):
                    pygame.draw.rect(win, GOLD, (x, y, SQUARE_SIZE, SQUARE_SIZE), 3)

    def _draw_pieces_and_animations(self, win):
        """ Draws all static and animated pieces on the board. """
        active_animated_pieces = {anim['pos'] for anim in self.animations}
        
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != EMPTY and (r, c) not in active_animated_pieces:
                    self._draw_piece(win, r, c, self.board[r][c])
                    
        current_time = time.time()
        # Filter out completed animations and draw active ones
        self.animations = [anim for anim in self.animations if current_time - anim['start_time'] < anim['duration']]
        for anim in self.animations:
            progress = (current_time - anim['start_time']) / anim['duration']
            self._draw_animated_piece(win, anim, progress)

    def _draw_piece(self, win, r, c, player, radius_mod=0, custom_pos=None):
        """ Draws a single, anti-aliased piece with a subtle 3D effect. """
        if custom_pos:
            center_x, center_y = custom_pos
        else:
            center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
        
        radius = SQUARE_SIZE // 2 - 8 + radius_mod
        if radius <= 0: return

        color = BLACK if player == PLAYER_BLACK else WHITE
        shadow_color = (30, 30, 30, 150)
        highlight_color = (200, 200, 200) if player == PLAYER_BLACK else (80, 80, 80)
        
        # Draw shadow using a transparent surface for a softer look
        shadow_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.gfxdraw.filled_circle(shadow_surface, radius, radius, radius, shadow_color)
        win.blit(shadow_surface, (center_x - radius + 3, center_y - radius + 3))

        # Using gfxdraw for anti-aliased shapes for a smoother look
        pygame.gfxdraw.filled_circle(win, center_x, center_y, radius, color)
        pygame.gfxdraw.aacircle(win, center_x, center_y, radius, DARK_GRAY)
        
        # Add a small highlight for a 3D effect
        pygame.gfxdraw.filled_circle(win, center_x - radius//3, center_y - radius//3, radius//3, highlight_color)


    def _draw_animated_piece(self, win, anim, progress):
        """ Draws a piece during its flip animation (shrink and grow). """
        r, c = anim['pos']
        if progress < 0.5:
            scale = 1 - (progress * 2) # Shrink
            player = anim['from_player']
        else:
            scale = (progress - 0.5) * 2 # Grow
            player = anim['to_player']
        
        radius_mod = int((SQUARE_SIZE // 2 - 8) * (scale - 1))
        self._draw_piece(win, r, c, player, radius_mod)

    def _draw_hover_and_valid_moves(self, win):
        """ Draws indicators for valid moves and a preview on hover. """
        if self.hover_pos and self.hover_pos in self.valid_moves:
            r, c = self.hover_pos
            center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
            radius = SQUARE_SIZE // 2 - 10
            
            color = (*(BLACK if self.current_player == PLAYER_BLACK else WHITE), 100)
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(surface, radius, radius, radius, color)
            win.blit(surface, (center_x - radius, center_y - radius))

        for r, c in self.valid_moves.keys():
            center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
            
            time_factor = (time.time() * 3) % (2 * math.pi)
            alpha = int(120 + 80 * math.sin(time_factor))
            radius = int(8 + 3 * math.sin(time_factor))
            
            color = (*CYAN[:3], alpha) if self.current_player == PLAYER_BLACK else (*ORANGE[:3], alpha)
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(surface, radius, radius, radius, color)
            win.blit(surface, (center_x - radius, center_y - radius))

    def draw_hud(self, win, font, small_font):
        """ Draws the Heads-Up Display for scores and turn status. """
        hud_rect = pygame.Rect(BOARD_X, 10, BOARD_SIZE, 80)
        pygame.draw.rect(win, DARK_GRAY, hud_rect, border_radius=15)
        pygame.draw.rect(win, SILVER, hud_rect, 3, border_radius=15)
        
        black_score, white_score = self.get_score()
        score_y = hud_rect.centery
        
        self._draw_piece(win, -1, -1, PLAYER_BLACK, radius_mod=0, custom_pos=(BOARD_X + 50, score_y))
        score_text = font.render(f"{black_score}", True, WHITE)
        win.blit(score_text, (BOARD_X + 85, score_y - score_text.get_height() // 2))
        
        self._draw_piece(win, -1, -1, PLAYER_WHITE, radius_mod=0, custom_pos=(BOARD_X + BOARD_SIZE - 50, score_y))
        score_text = font.render(f"{white_score}", True, WHITE)
        win.blit(score_text, (BOARD_X + BOARD_SIZE - 85 - score_text.get_width(), score_y - score_text.get_height() // 2))

        if not self.game_over:
            # Always show whose turn it is, regardless of AI thinking state.
            turn_text = "Black's Turn" if self.current_player == PLAYER_BLACK else "White's Turn"
            color = BLUE # Use the standard color for turn indication
            text_surface = font.render(turn_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(hud_rect.centerx, hud_rect.centery))
            bg_rect = text_rect.inflate(30, 16)
            pygame.draw.rect(win, color, bg_rect, border_radius=10)
            win.blit(text_surface, text_rect)

    def draw_ai_debug_panel(self, win, font, small_font):
        """ Draws the side panel showing the AI's analysis. """
        panel_rect = pygame.Rect(DEBUG_PANEL_X, BOARD_Y, DEBUG_PANEL_WIDTH, BOARD_SIZE)
        pygame.draw.rect(win, DARK_GRAY, panel_rect, border_radius=15)
        pygame.draw.rect(win, SILVER, panel_rect, 2, border_radius=15)
        title_text = font.render("AI Analysis", True, WHITE)
        win.blit(title_text, (DEBUG_PANEL_X + 20, BOARD_Y + 15))
        diff_text = small_font.render(f"Difficulty: {AI_DIFFICULTY.name} (Depth: {AI_DIFFICULTY.value})", True, CYAN)
        win.blit(diff_text, (DEBUG_PANEL_X + 20, BOARD_Y + 50))
        
        y_offset = BOARD_Y + 90
        if not self.ai_decision_log:
            status_text = "Analyzing moves..." if self.ai_thinking else "Waiting for AI move..."
            color = ORANGE if self.ai_thinking else GRAY
            text = small_font.render(status_text, True, color)
            win.blit(text, (DEBUG_PANEL_X + 20, y_offset))
            return
            
        header = small_font.render("Move", True, WHITE)
        win.blit(header, (DEBUG_PANEL_X + 25, y_offset))
        header = small_font.render("Score", True, WHITE)
        win.blit(header, (DEBUG_PANEL_X + 120, y_offset))
        y_offset += 25
        
        max_score = max(abs(s) for s, m in self.ai_decision_log) if self.ai_decision_log else 1

        for i, (score, move) in enumerate(self.ai_decision_log[:12]):
            if y_offset > BOARD_Y + BOARD_SIZE - 35: break
            
            is_best_move = (i == 0)
            bg_color = (100, 100, 0) if is_best_move else (60, 60, 60)
            
            line_rect = pygame.Rect(DEBUG_PANEL_X + 10, y_offset, DEBUG_PANEL_WIDTH - 20, 28)
            pygame.draw.rect(win, bg_color, line_rect, border_radius=5)

            move_notation = chr(ord('A') + move[1]) + str(move[0] + 1)
            move_text = f"{i+1}. {move_notation}"
            score_text = f"{score:.1f}"
            text_color = GOLD if is_best_move else WHITE
            
            move_surf = small_font.render(move_text, True, text_color)
            score_surf = small_font.render(score_text, True, text_color)
            
            win.blit(move_surf, (DEBUG_PANEL_X + 20, y_offset + 5))
            win.blit(score_surf, (DEBUG_PANEL_X + 120, y_offset + 5))
            
            # Score visualization bar
            bar_x, bar_y = DEBUG_PANEL_X + 200, y_offset + 8
            bar_width, bar_height = 220, 12
            pygame.draw.rect(win, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
            
            normalized_score = score / max_score if max_score != 0 else 0
            fill_width = int((bar_width / 2) * normalized_score)
            bar_mid = bar_x + bar_width // 2
            bar_color = GREEN if score > 0 else RED
            if fill_width > 0:
                pygame.draw.rect(win, bar_color, (bar_mid, bar_y, fill_width, bar_height), border_radius=3)
            else:
                pygame.draw.rect(win, bar_color, (bar_mid + fill_width, bar_y, -fill_width, bar_height), border_radius=3)
            
            y_offset += 35


# =============================================================================
# 3. Enhanced AI with Dynamic Evaluation
# =============================================================================
def dynamic_evaluate_board(board, player, total_pieces):
    """
    Enhanced evaluation function with weights that change based on the game phase.
    """
    opponent = -player

    # --- Phase-dependent Weighting ---
    if total_pieces < 20:  # Opening
        piece_weight = 1
        mobility_weight = 15
        corner_weight = 100
        stability_weight = 80
    elif total_pieces < 52:  # Mid-game
        piece_weight = 5
        mobility_weight = 10
        corner_weight = 100
        stability_weight = 100
    else:  # End-game
        piece_weight = 20
        mobility_weight = 5
        corner_weight = 120
        stability_weight = 120

    score = 0
    
    # 1. Piece Count (Parity)
    my_pieces = sum(row.count(player) for row in board)
    opp_pieces = sum(row.count(opponent) for row in board)
    score += piece_weight * (my_pieces - opp_pieces)

    # 2. Mobility
    temp_game = Othello()
    temp_game.board = board
    my_moves = len(temp_game.get_valid_moves(player))
    opp_moves = len(temp_game.get_valid_moves(opponent))
    if my_moves + opp_moves > 0:
        score += mobility_weight * (my_moves - opp_moves)
    
    # 3. Corner and Edge Control
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    my_corners, opp_corners = 0, 0
    for r, c in corners:
        if board[r][c] == player: my_corners += 1
        elif board[r][c] == opponent: opp_corners += 1
    score += corner_weight * (my_corners - opp_corners)
    
    # Penalty for pieces adjacent to empty corners
    for r_c, c_c in corners:
        if board[r_c][c_c] == EMPTY:
            for dr, dc in [(0,1), (1,0), (1,1)]:
                if 0 <= r_c+dr < 8 and 0 <= c_c+dc < 8 and board[r_c+dr][c_c+dc] == player: score -= 15
                if 0 <= r_c-dr < 8 and 0 <= c_c+dc < 8 and board[r_c-dr][c_c+dc] == player: score -= 15
                if 0 <= r_c+dr < 8 and 0 <= c_c-dc < 8 and board[r_c+dr][c_c-dc] == player: score -= 15
    
    # 4. Stability
    my_stable = count_stable_pieces(board, player)
    opp_stable = count_stable_pieces(board, opponent)
    score += stability_weight * (my_stable - opp_stable)
    
    return score

def count_stable_pieces(board, player):
    """ Counts pieces that are 'stable' and cannot be flipped. """
    stable_count = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                is_stable = True
                # Check all 4 axes (horizontal, vertical, 2 diagonals)
                for dr, dc in [(1, 0), (1, 1), (0, 1), (-1, 1)]:
                    # Check one side
                    side1_secure = False
                    curr_r, curr_c = r + dr, c + dc
                    while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                        if board[curr_r][curr_c] != player:
                            side1_secure = True; break
                        curr_r, curr_c = curr_r + dr, curr_c + dc
                    if not (0 <= curr_r < 8 and 0 <= curr_c < 8): side1_secure = True # Edge is secure
                    
                    # Check other side
                    side2_secure = False
                    curr_r, curr_c = r - dr, c - dc
                    while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                        if board[curr_r][curr_c] != player:
                            side2_secure = True; break
                        curr_r, curr_c = curr_r - dr, curr_c - dc
                    if not (0 <= curr_r < 8 and 0 <= curr_c < 8): side2_secure = True # Edge is secure
                        
                    if not (side1_secure and side2_secure):
                        is_stable = False; break
                if is_stable:
                    stable_count += 1
    return stable_count

def minimax_alphabeta(game_state, depth, alpha, beta, maximizing_player, ai_player, total_pieces):
    """ The core AI logic using minimax with alpha-beta pruning. """
    if depth == 0 or game_state.game_over:
        return dynamic_evaluate_board(game_state.board, ai_player, total_pieces), None, []

    valid_moves = game_state.valid_moves
    if not valid_moves:
        next_state = copy.deepcopy(game_state)
        next_state._switch_player() # Pass turn
        return minimax_alphabeta(next_state, depth - 1, alpha, beta, not maximizing_player, ai_player, total_pieces)

    evaluated_moves = []
    best_move = list(valid_moves.keys())[0]

    if maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            next_state = copy.deepcopy(game_state)
            next_state.make_move(move[0], move[1])
            evaluation, _, _ = minimax_alphabeta(next_state, depth - 1, alpha, beta, False, ai_player, total_pieces + 1)
            evaluated_moves.append((evaluation, move))
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
        evaluated_moves.sort(key=lambda x: x[0], reverse=True)
        return max_eval, best_move, evaluated_moves
    else: # Minimizing player
        min_eval = math.inf
        for move in valid_moves:
            next_state = copy.deepcopy(game_state)
            next_state.make_move(move[0], move[1])
            evaluation, _, _ = minimax_alphabeta(next_state, depth - 1, alpha, beta, True, ai_player, total_pieces + 1)
            evaluated_moves.append((evaluation, move))
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha: break
        evaluated_moves.sort(key=lambda x: x[0])
        return min_eval, best_move, evaluated_moves

# =============================================================================
# 4. UI Screens and Main Loop
# =============================================================================

def draw_button(win, rect, text, font, button_color, text_color, border_color=None, hover_color=None):
    """ Helper function to draw a styled button with hover effect. """
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)
    
    final_button_color = hover_color if is_hovered and hover_color else button_color
    pygame.draw.rect(win, final_button_color, rect, border_radius=15)
    if border_color:
        pygame.draw.rect(win, border_color, rect, 3, border_radius=15)
    
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    win.blit(text_surf, text_rect)

def draw_gradient_background(win, color1, color2):
    """ Draws a vertical gradient background. """
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        pygame.draw.line(win, (r, g, b), (0, y), (WIDTH, y))

def main_menu(win, font, big_font):
    """ Displays the main menu and handles mode/difficulty selection. """
    # Main menu buttons
    pvp_button = pygame.Rect(WIDTH // 2 - 150, 300, 300, 60)
    pvb_button = pygame.Rect(WIDTH // 2 - 150, 380, 300, 60)
    bvb_button = pygame.Rect(WIDTH // 2 - 150, 460, 300, 60)
    
    # Difficulty buttons
    diff_buttons = {
        Difficulty.EASY: pygame.Rect(WIDTH // 2 - 225, 600, 100, 40),
        Difficulty.MEDIUM: pygame.Rect(WIDTH // 2 - 110, 600, 100, 40),
        Difficulty.HARD: pygame.Rect(WIDTH // 2 + 5, 600, 100, 40),
        Difficulty.EXPERT: pygame.Rect(WIDTH // 2 + 120, 600, 100, 40),
    }

    # Color choice buttons (for PvB)
    play_as_black_button = pygame.Rect(WIDTH // 2 - 220, 380, 200, 60)
    play_as_white_button = pygame.Rect(WIDTH // 2 + 20, 380, 200, 60)
    back_button = pygame.Rect(WIDTH // 2 - 75, 460, 150, 50)
    
    global AI_DIFFICULTY
    clock = pygame.time.Clock()
    menu_state = "main" # "main" or "choose_color"

    while True:
        draw_gradient_background(win, (20, 40, 20), (0, 80, 0))
        
        # Title is always visible
        title_text = big_font.render("Othello AI", True, (30,30,30))
        win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2 + 4, 154))
        title_text = big_font.render("Othello AI", True, GOLD)
        win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))

        if menu_state == "main":
            subtitle_text = font.render("Choose your game mode", True, WHITE)
            win.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, 240))

            draw_button(win, pvp_button, "Player vs Player", font, BLUE, WHITE, DARK_BLUE, (100, 160, 200))
            draw_button(win, pvb_button, "Player vs Bot", font, BLUE, WHITE, DARK_BLUE, (100, 160, 200))
            draw_button(win, bvb_button, "Bot vs Bot", font, BLUE, WHITE, DARK_BLUE, (100, 160, 200))
        
        elif menu_state == "choose_color":
            subtitle_text = font.render("Choose your color", True, WHITE)
            win.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, 240))
            
            draw_button(win, play_as_black_button, "Play as Black", font, BLUE, WHITE, DARK_BLUE, (100, 160, 200))
            draw_button(win, play_as_white_button, "Play as White", font, BLUE, WHITE, DARK_BLUE, (100, 160, 200))
            draw_button(win, back_button, "Back", font, GRAY, BLACK, DARK_GRAY, LIGHT_GRAY)

        # Difficulty selection is always visible
        diff_text = font.render("AI Difficulty:", True, WHITE)
        win.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 560))
        for diff, button in diff_buttons.items():
            color = ORANGE if AI_DIFFICULTY == diff else GRAY
            border = GOLD if AI_DIFFICULTY == diff else DARK_GRAY
            draw_button(win, button, diff.name, font, color, WHITE, border, LIGHT_GRAY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if menu_state == "main":
                    if pvp_button.collidepoint(event.pos): return "PvP", None
                    if pvb_button.collidepoint(event.pos): menu_state = "choose_color"
                    if bvb_button.collidepoint(event.pos): return "BvB", None
                elif menu_state == "choose_color":
                    if play_as_black_button.collidepoint(event.pos): return "PvB", PLAYER_BLACK
                    if play_as_white_button.collidepoint(event.pos): return "PvB", PLAYER_WHITE
                    if back_button.collidepoint(event.pos): menu_state = "main"

                # Handle difficulty clicks regardless of state
                for diff, button in diff_buttons.items():
                    if button.collidepoint(event.pos):
                        AI_DIFFICULTY = diff
        
        pygame.display.flip()
        clock.tick(60)

def ai_move_thread_worker(game):
    """ The actual work for the AI thread to keep the UI responsive. """
    game.ai_thinking = True
    game.ai_decision_log = []
    
    try:
        total_pieces = sum(row.count(PLAYER_BLACK) + row.count(PLAYER_WHITE) for row in game.board)
        _, best_move, evaluated_moves = minimax_alphabeta(
            game, AI_DIFFICULTY.value, -math.inf, math.inf, True, game.current_player, total_pieces
        )
        game.ai_decision_log = evaluated_moves
        time.sleep(0.5) # Simulate thinking time for better UX
        if best_move:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'move': best_move}))
    except Exception as e:
        print(f"AI Error: {e}")
    finally:
        game.ai_thinking = False

def game_over_screen(win, font, big_font, winner, final_score):
    """ Displays the game over screen with results and options. """
    overlay = pygame.Surface((WIDTH, HEIGHT)); overlay.set_alpha(200); overlay.fill(BLACK)
    win.blit(overlay, (0, 0))
    
    if winner == PLAYER_BLACK: winner_text, color = "Black Wins!", GOLD
    elif winner == PLAYER_WHITE: winner_text, color = "White Wins!", SILVER
    else: winner_text, color = "It's a Tie!", PURPLE
    
    text_surf = big_font.render(winner_text, True, (30,30,30))
    win.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2 + 4, 254))
    text_surf = big_font.render(winner_text, True, color)
    win.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, 250))
    
    black_score, white_score = final_score
    score_text = font.render(f"Final Score: Black {black_score} - White {white_score}", True, WHITE)
    win.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 350))
    
    play_again_button = pygame.Rect(WIDTH // 2 - 200, 450, 180, 50)
    main_menu_button = pygame.Rect(WIDTH // 2 + 20, 450, 180, 50)
    
    while True:
        draw_button(win, play_again_button, "Play Again", font, GREEN, WHITE, DARK_GREEN, (100, 200, 100))
        draw_button(win, main_menu_button, "Main Menu", font, BLUE, WHITE, DARK_BLUE, (100, 160, 200))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_button.collidepoint(event.pos): return "play_again"
                if main_menu_button.collidepoint(event.pos): return "main_menu"
        
        pygame.display.flip()
        pygame.time.wait(100)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3

def main():
    """ Main game function that orchestrates everything using a state machine. """
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Polished Othello AI")
    
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    big_font = pygame.font.Font(None, 72)
    
    clock = pygame.time.Clock()

    game_state = GameState.MENU
    game = None
    game_mode = None
    human_color = None

    while True:
        if game_state == GameState.MENU:
            game_mode, human_color = main_menu(win, font, big_font)
            game = Othello()
            game_state = GameState.PLAYING

        elif game_state == GameState.PLAYING:
            is_human_turn = False
            if game_mode == "PvP":
                is_human_turn = True
            elif game_mode == "PvB":
                is_human_turn = (game.current_player == human_color)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    game_state = GameState.MENU

                if event.type == pygame.USEREVENT:
                    game.make_move(event.move[0], event.move[1])

                if event.type == pygame.MOUSEBUTTONDOWN and is_human_turn and not game.ai_thinking:
                    x, y = event.pos
                    if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
                        col = (x - BOARD_X) // SQUARE_SIZE
                        row = (y - BOARD_Y) // SQUARE_SIZE
                        game.make_move(row, col)
                
                if event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
                        game.hover_pos = ((y - BOARD_Y) // SQUARE_SIZE, (x - BOARD_X) // SQUARE_SIZE)
                    else:
                        game.hover_pos = None
            
            if not is_human_turn and not game.game_over and not game.ai_thinking and game.valid_moves:
                threading.Thread(target=ai_move_thread_worker, args=(game,)).start()
            
            win.fill(DARK_GREEN)
            game.draw(win, font, small_font)
            
            if game.game_over:
                game_state = GameState.GAME_OVER

        elif game_state == GameState.GAME_OVER:
            result = game_over_screen(win, font, big_font, game.winner, game.get_score())
            if result == "play_again":
                game = Othello()
                game_state = GameState.PLAYING
            else: # main_menu
                game_state = GameState.MENU

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
