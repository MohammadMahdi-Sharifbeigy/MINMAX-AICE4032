import pygame
import pygame.gfxdraw
import sys
import math
import time
import copy
import threading
from enum import Enum
import random

# =============================================================================
# 1.Constants and Setup
# =============================================================================

# --- Screen Dimensions---
WIDTH, HEIGHT = 1200, 800
BOARD_SIZE = 560
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X = 40
BOARD_Y = (HEIGHT - BOARD_SIZE) // 2
DEBUG_PANEL_X = BOARD_X + BOARD_SIZE + 20
DEBUG_PANEL_WIDTH = 380
STATS_PANEL_X = DEBUG_PANEL_X + DEBUG_PANEL_WIDTH + 15
STATS_PANEL_WIDTH = 180

# --- Color Palette ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BOARD_BG_LIGHT = (0, 180, 50)
BOARD_BG_DARK = (0, 150, 40)
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
BOARD_BORDER = (139, 69, 19)
NEON_GREEN = (57, 255, 20)
DEEP_PURPLE = (75, 0, 130)
CORAL = (255, 127, 80)

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
    GRANDMASTER = 10

AI_DIFFICULTY = Difficulty.MEDIUM

# --- Positional Values Matrix ---
POSITION_VALUES = [
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100]
]

# =============================================================================
# 2.Game Logic Class
# =============================================================================

class Othello:
    def __init__(self, sounds):
        self.board = [[EMPTY for _ in range(8)] for _ in range(8)]
        self.board[3][3], self.board[4][4] = PLAYER_WHITE, PLAYER_WHITE
        self.board[3][4], self.board[4][3] = PLAYER_BLACK, PLAYER_BLACK
        self.current_player = PLAYER_BLACK
        self.valid_moves = self.get_valid_moves(self.current_player)
        self.ai_decision_log = []
        self.move_history = []
        self.game_history = []  # Full game history with timestamps
        self.ai_thinking = False
        self.last_move = None
        self.game_over = False
        self.winner = None
        self.animations = []
        self.hover_pos = None
        self.sounds = sounds
        self.turn_count = 0
        self.ai_think_time = 0
        self.evaluation_history = []
        self.move_start_time = time.time()
        
    def copy(self):
        """Creates a deep copy for AI simulation."""
        new_game = Othello(sounds={})
        new_game.board = copy.deepcopy(self.board)
        new_game.current_player = self.current_player
        new_game.valid_moves = new_game.get_valid_moves(new_game.current_player)
        new_game.turn_count = self.turn_count
        return new_game

    def is_on_board(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_valid_moves(self, player):
        moves = {}
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == EMPTY:
                    pieces_to_flip = self._get_pieces_to_flip(r, c, player)
                    if pieces_to_flip:
                        moves[(r, c)] = pieces_to_flip
        return moves

    def _get_pieces_to_flip(self, r, c, player):
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
        if (r, c) in self.valid_moves:
            # Record move in history
            move_time = time.time() - self.move_start_time
            self.game_history.append({
                'move': (r, c),
                'player': self.current_player,
                'turn': self.turn_count,
                'time': move_time,
                'board_state': copy.deepcopy(self.board)
            })
            
            self.move_history.append(copy.deepcopy(self.board))
            self.board[r][c] = self.current_player
            self.last_move = (r, c)
            self.turn_count += 1
            
            if self.sounds.get('place'):
                self.sounds['place'].play()
            
            pieces_to_flip = self.valid_moves[(r, c)]
            for i, piece_pos in enumerate(pieces_to_flip):
                self.board[piece_pos[0]][piece_pos[1]] = self.current_player
                self.animations.append({
                    'type': 'flip',
                    'pos': piece_pos,
                    'start_time': time.time() + i * 0.03,
                    'duration': 0.3,
                    'from_player': -self.current_player,
                    'to_player': self.current_player
                })
                if self.sounds.get('flip') and i % 3 == 0:
                    self.sounds['flip'].play()

            self._switch_player()
            return True
        return False

    def _switch_player(self):
        self.current_player *= -1
        self.valid_moves = self.get_valid_moves(self.current_player)
        self.move_start_time = time.time()
        
        if not self.valid_moves:
            self.current_player *= -1
            self.valid_moves = self.get_valid_moves(self.current_player)
            if not self.valid_moves:
                self.game_over = True
                self._determine_winner()

    def get_score(self):
        black_score = sum(row.count(PLAYER_BLACK) for row in self.board)
        white_score = sum(row.count(PLAYER_WHITE) for row in self.board)
        return black_score, white_score

    def _determine_winner(self):
        black_score, white_score = self.get_score()
        if black_score > white_score:
            self.winner = PLAYER_BLACK
        elif white_score > black_score:
            self.winner = PLAYER_WHITE
        else:
            self.winner = EMPTY

    def get_mobility_score(self, player):
        return len(self.get_valid_moves(player))

    def get_corner_score(self, player):
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        return sum(1 for r, c in corners if self.board[r][c] == player)

    def get_edge_score(self, player):
        edges = [(i, 0) for i in range(8)] + [(i, 7) for i in range(8)] + \
                [(0, i) for i in range(1, 7)] + [(7, i) for i in range(1, 7)]
        return sum(1 for r, c in edges if self.board[r][c] == player)

    def draw(self, win, font, small_font, game_mode):
        self._draw_enhanced_board(win)
        self._draw_pieces_with_effects(win)
        self._draw_smart_indicators(win)
        self.draw_enhanced_hud(win, font, small_font)
        
        if game_mode == "PvB" or game_mode == "BvB":
            self.draw_ai_analysis_panel(win, font, small_font)
            self.draw_statistics_panel(win, font, small_font)
        elif game_mode == "PvP":
            self.draw_pvp_stats_panel(win, font, small_font)

    def draw_pvp_stats_panel(self, win, font, small_font):
        """Simple statistics panel for Player vs Player games."""
        panel_rect = pygame.Rect(DEBUG_PANEL_X, BOARD_Y, DEBUG_PANEL_WIDTH, BOARD_SIZE)
        
        pygame.draw.rect(win, DARK_GRAY, panel_rect, border_radius=15)
        pygame.draw.rect(win, GOLD, panel_rect, 3, border_radius=15)
        
        title_text = font.render("Game Stats", True, GOLD)
        win.blit(title_text, (DEBUG_PANEL_X + 20, BOARD_Y + 20))
        
        y_offset = BOARD_Y + 80
        
        black_score, white_score = self.get_score()
        stats = [
            ("Current Turn:", str(self.turn_count)),
            ("", ""),
            ("Black Score:", str(black_score)),
            ("White Score:", str(white_score)),
            ("", ""),
            ("Black Mobility:", str(len(self.get_valid_moves(PLAYER_BLACK)))),
            ("White Mobility:", str(len(self.get_valid_moves(PLAYER_WHITE)))),
            ("", ""),
            ("Black Corners:", str(self.get_corner_score(PLAYER_BLACK))),
            ("White Corners:", str(self.get_corner_score(PLAYER_WHITE))),
            ("", ""),
            ("Current Player:", "Black" if self.current_player == PLAYER_BLACK else "White"),
            ("Valid Moves:", str(len(self.valid_moves))),
        ]
        
        for label, value in stats:
            if label == "": 
                y_offset += 15
                continue
                
            label_surf = small_font.render(label, True, WHITE)
            win.blit(label_surf, (DEBUG_PANEL_X + 30, y_offset))
            
            if value:
                value_color = CYAN if "Black" in label else CORAL if "White" in label else WHITE
                value_surf = small_font.render(value, True, value_color)
                win.blit(value_surf, (DEBUG_PANEL_X + 250, y_offset))
            
            y_offset += 25

    def _draw_enhanced_board(self, win):
        for i in range(5):
            border_rect = pygame.Rect(BOARD_X - 15 + i, BOARD_Y - 15 + i, 
                                    BOARD_SIZE + 30 - 2*i, BOARD_SIZE + 30 - 2*i)
            color_intensity = 139 - i * 20
            border_color = (color_intensity, color_intensity//2, 19)
            pygame.draw.rect(win, border_color, border_rect, border_radius=20-i)
        
        for r in range(8):
            for c in range(8):
                x, y = BOARD_X + c * SQUARE_SIZE, BOARD_Y + r * SQUARE_SIZE
                
                base_color = BOARD_BG_LIGHT if (r + c) % 2 == 0 else BOARD_BG_DARK
                if (r + c) % 2 == 0:
                    color = (
                        min(255, max(0, base_color[0] + 10)), 
                        min(255, max(0, base_color[1] + 10)), 
                        min(255, max(0, base_color[2] + 5))
                    )
                else:
                    color = (
                        min(255, max(0, base_color[0] - 10)), 
                        min(255, max(0, base_color[1] - 10)), 
                        min(255, max(0, base_color[2] - 5))
                    )
                
                pygame.draw.rect(win, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                
                pygame.draw.rect(win, (30, 30, 30), (x, y, SQUARE_SIZE, SQUARE_SIZE), 1)
                
                if self.last_move == (r, c):
                    pulse = int(30 + 25 * math.sin(time.time() * 4))
                    highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    highlight_surface.fill((255, 215, 0, pulse))
                    win.blit(highlight_surface, (x, y))
                    pygame.draw.rect(win, (255, 215, 0), (x, y, SQUARE_SIZE, SQUARE_SIZE), 4)

    def _draw_pieces_with_effects(self, win):
        active_animated_pieces = {anim['pos'] for anim in self.animations}
        
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != EMPTY and (r, c) not in active_animated_pieces:
                    self._draw_enhanced_piece(win, r, c, self.board[r][c])
                    
        current_time = time.time()
        self.animations = [anim for anim in self.animations 
                          if current_time - anim['start_time'] < anim['duration']]
        
        for anim in self.animations:
            if current_time >= anim['start_time']:
                progress = (current_time - anim['start_time']) / anim['duration']
                self._draw_animated_piece(win, anim, progress)

    def _draw_enhanced_piece(self, win, r, c, player, radius_mod=0, custom_pos=None):
        if custom_pos:
            center_x, center_y = custom_pos
        else:
            center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
        
        radius = SQUARE_SIZE // 2 - 10 + radius_mod
        if radius <= 5: 
            return

        if player == PLAYER_BLACK:
            main_color = (20, 20, 20)
            shadow_color = (0, 0, 0, 120)
            highlight_color = (100, 100, 100)
            rim_color = (60, 60, 60)
        else:
            main_color = (245, 245, 245)
            shadow_color = (50, 50, 50, 100)
            highlight_color = (255, 255, 255)
            rim_color = (200, 200, 200)
        
        for i in range(3):
            shadow_surface = pygame.Surface((radius*2 + i*2, radius*2 + i*2), pygame.SRCALPHA)
            shadow_alpha = 40 - i*10
            if shadow_alpha > 0:
                pygame.gfxdraw.filled_circle(shadow_surface, radius + i, radius + i, 
                                           radius, (*shadow_color[:3], shadow_alpha))
                win.blit(shadow_surface, (center_x - radius + 4 + i, center_y - radius + 4 + i))

        pygame.gfxdraw.filled_circle(win, center_x, center_y, radius, main_color)
        
        if radius > 4:
            pygame.gfxdraw.filled_circle(win, center_x, center_y, max(2, radius-2), rim_color)
        if radius > 6:
            pygame.gfxdraw.filled_circle(win, center_x, center_y, max(1, radius-4), main_color)
        
        if radius > 8:
            highlight_radius = max(1, radius // 3)
            pygame.gfxdraw.filled_circle(win, center_x - radius//4, center_y - radius//4, 
                                       highlight_radius, highlight_color)
        
        pygame.gfxdraw.aacircle(win, center_x, center_y, radius, (0, 0, 0))

    def _draw_animated_piece(self, win, anim, progress):
        r, c = anim['pos']
        
        if progress < 0.5:
            scale = 1 - (progress * 2)
            player = anim['from_player']
        else:
            scale = (progress - 0.5) * 2
            player = anim['to_player']
        
        rotation_angle = progress * math.pi
        scale_x = abs(math.cos(rotation_angle)) * scale
        
        radius_mod = int((SQUARE_SIZE // 2 - 10) * (scale_x - 1))
        self._draw_enhanced_piece(win, r, c, player, radius_mod)

    def _draw_smart_indicators(self, win):
        if self.hover_pos and self.hover_pos in self.valid_moves:
            r, c = self.hover_pos
            center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
            
            preview_color = (*((20, 20, 20) if self.current_player == PLAYER_BLACK 
                             else (245, 245, 245)), 120)
            radius = SQUARE_SIZE // 2 - 12
            
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(surface, radius, radius, radius, preview_color)
            win.blit(surface, (center_x - radius, center_y - radius))
            
            flip_count = len(self.valid_moves[self.hover_pos])
            if flip_count > 0:
                font = pygame.font.Font(None, 24)
                flip_text = font.render(f"+{flip_count}", True, GOLD)
                win.blit(flip_text, (center_x + 20, center_y - 30))

        for (r, c), pieces_to_flip in self.valid_moves.items():
            center_x = BOARD_X + c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = BOARD_Y + r * SQUARE_SIZE + SQUARE_SIZE // 2
            
            flip_count = len(pieces_to_flip)
            position_value = POSITION_VALUES[r][c]
            
            if position_value > 50:  # Corner
                color = GOLD
                base_radius = 12
            elif flip_count > 5:  # High-impact move
                color = ORANGE
                base_radius = 10
            elif position_value < -10:  # Dangerous move
                color = RED
                base_radius = 8
            else:  # Normal move
                color = CYAN if self.current_player == PLAYER_BLACK else CORAL
                base_radius = 8
            
            time_factor = (time.time() * 2) % (2 * math.pi)
            pulse = math.sin(time_factor)
            alpha = int(100 + 60 * pulse)
            radius = int(base_radius + 3 * pulse)
            
            surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.gfxdraw.filled_circle(surface, radius, radius, radius, (*color[:3], alpha))
            win.blit(surface, (center_x - radius, center_y - radius))

    def draw_enhanced_hud(self, win, font, small_font):
        hud_rect = pygame.Rect(BOARD_X, 10, BOARD_SIZE, 100)
        
        for i in range(hud_rect.height):
            ratio = i / hud_rect.height
            r = int(DARK_GRAY[0] * (1-ratio) + (DARK_GRAY[0]+20) * ratio)
            g = int(DARK_GRAY[1] * (1-ratio) + (DARK_GRAY[1]+20) * ratio)
            b = int(DARK_GRAY[2] * (1-ratio) + (DARK_GRAY[2]+20) * ratio)
            pygame.draw.line(win, (r, g, b), 
                           (hud_rect.x, hud_rect.y + i), 
                           (hud_rect.x + hud_rect.width, hud_rect.y + i))
        
        pygame.draw.rect(win, GOLD, hud_rect, 3, border_radius=15)
        
        black_score, white_score = self.get_score()
        
        score_y = hud_rect.y + 30
        
        self._draw_enhanced_piece(win, -1, -1, PLAYER_BLACK, custom_pos=(BOARD_X + 60, score_y))
        score_text = font.render(f"{black_score}", True, WHITE)
        win.blit(score_text, (BOARD_X + 100, score_y - score_text.get_height() // 2))
        
        black_mobility = len(self.get_valid_moves(PLAYER_BLACK))
        black_corners = self.get_corner_score(PLAYER_BLACK)
        stats_font = pygame.font.Font(None, 20)
        mobility_text = stats_font.render(f"Moves: {black_mobility}", True, CYAN)
        corner_text = stats_font.render(f"Corners: {black_corners}", True, GOLD)
        win.blit(mobility_text, (BOARD_X + 100, score_y + 15))
        win.blit(corner_text, (BOARD_X + 100, score_y + 30))
        
        self._draw_enhanced_piece(win, -1, -1, PLAYER_WHITE, custom_pos=(BOARD_X + BOARD_SIZE - 60, score_y))
        score_text = font.render(f"{white_score}", True, WHITE)
        win.blit(score_text, (BOARD_X + BOARD_SIZE - 140, score_y - score_text.get_height() // 2))
        
        white_mobility = len(self.get_valid_moves(PLAYER_WHITE))
        white_corners = self.get_corner_score(PLAYER_WHITE)
        mobility_text = stats_font.render(f"Moves: {white_mobility}", True, CYAN)
        corner_text = stats_font.render(f"Corners: {white_corners}", True, GOLD)
        win.blit(mobility_text, (BOARD_X + BOARD_SIZE - 140, score_y + 15))
        win.blit(corner_text, (BOARD_X + BOARD_SIZE - 140, score_y + 30))
        
        if not self.game_over:
            turn_text = "Black's Turn" if self.current_player == PLAYER_BLACK else "White's Turn"
            color = NEON_GREEN if self.current_player == PLAYER_BLACK else ORANGE
            
            pulse = int(200 + 55 * math.sin(time.time() * 3))
            text_color = (pulse, pulse, pulse)
            
            text_surface = font.render(turn_text, True, text_color)
            text_rect = text_surface.get_rect(center=(hud_rect.centerx, hud_rect.y + 70))
            
            bg_rect = text_rect.inflate(40, 20)
            glow_surface = pygame.Surface((bg_rect.width + 10, bg_rect.height + 10), pygame.SRCALPHA)
            pygame.gfxdraw.box(glow_surface, glow_surface.get_rect(), (*color[:3], 30))
            win.blit(glow_surface, (bg_rect.x - 5, bg_rect.y - 5))
            
            pygame.draw.rect(win, color, bg_rect, border_radius=10)
            win.blit(text_surface, text_rect)

    def draw_ai_analysis_panel(self, win, font, small_font):
        panel_rect = pygame.Rect(DEBUG_PANEL_X, BOARD_Y, DEBUG_PANEL_WIDTH, BOARD_SIZE)
        
        for i in range(panel_rect.height):
            ratio = i / panel_rect.height
            r = int(DARK_GRAY[0] * (1-ratio) + (DARK_GRAY[0]+15) * ratio)
            g = int(DARK_GRAY[1] * (1-ratio) + (DARK_GRAY[1]+15) * ratio)
            b = int(DARK_GRAY[2] * (1-ratio) + (DARK_GRAY[2]+15) * ratio)
            pygame.draw.line(win, (r, g, b), 
                           (panel_rect.x, panel_rect.y + i), 
                           (panel_rect.x + panel_rect.width, panel_rect.y + i))
        
        pygame.draw.rect(win, DEEP_PURPLE, panel_rect, 3, border_radius=15)
        
        title_text = font.render("AI Brain", True, GOLD)
        win.blit(title_text, (DEBUG_PANEL_X + 20, BOARD_Y + 15))
        
        diff_text = small_font.render(f"Level: {AI_DIFFICULTY.name} (Depth {AI_DIFFICULTY.value})", True, CYAN)
        win.blit(diff_text, (DEBUG_PANEL_X + 20, BOARD_Y + 45))
        
        if self.ai_thinking:
            thinking_dots = "." * ((int(time.time() * 3) % 3) + 1)
            status_text = small_font.render(f"Thinking{thinking_dots}", True, ORANGE)
            win.blit(status_text, (DEBUG_PANEL_X + 20, BOARD_Y + 70))
        
        y_offset = BOARD_Y + 100
        
        if not self.ai_decision_log:
            if self.ai_thinking:
                status_text = small_font.render("Analyzing positions...", True, ORANGE)
            else:
                status_text = small_font.render("Ready for next move", True, GRAY)
            win.blit(status_text, (DEBUG_PANEL_X + 20, y_offset))
            return
        
        headers = ["#", "Move", "Score", "Evaluation"]
        x_positions = [DEBUG_PANEL_X + 25, DEBUG_PANEL_X + 50, DEBUG_PANEL_X + 120, DEBUG_PANEL_X + 200]
        
        for i, header in enumerate(headers):
            header_surf = small_font.render(header, True, WHITE)
            win.blit(header_surf, (x_positions[i], y_offset))
        
        y_offset += 25
        
        max_score = max(abs(s) for s, m in self.ai_decision_log) if self.ai_decision_log else 1
        
        for i, (score, move) in enumerate(self.ai_decision_log[:15]):
            if y_offset > BOARD_Y + BOARD_SIZE - 40:
                break
            
            is_best_move = (i == 0)
            
            row_color = (80, 50, 120) if is_best_move else (50, 50, 70)
            line_rect = pygame.Rect(DEBUG_PANEL_X + 15, y_offset - 2, DEBUG_PANEL_WIDTH - 30, 22)
            pygame.draw.rect(win, row_color, line_rect, border_radius=5)
            
            move_notation = chr(ord('A') + move[1]) + str(move[0] + 1)
            rank_text = f"{i+1}"
            
            text_color = GOLD if is_best_move else WHITE
            
            rank_surf = small_font.render(rank_text, True, text_color)
            move_surf = small_font.render(move_notation, True, text_color)
            score_surf = small_font.render(f"{score:.1f}", True, text_color)
            
            win.blit(rank_surf, (x_positions[0], y_offset))
            win.blit(move_surf, (x_positions[1], y_offset))
            win.blit(score_surf, (x_positions[2], y_offset))
            
            bar_x = x_positions[3]
            bar_y = y_offset + 4
            bar_width = 180
            bar_height = 12
            
            pygame.draw.rect(win, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height), border_radius=6)
            
            normalized_score = score / max_score if max_score != 0 else 0
            fill_width = int((bar_width / 2) * abs(normalized_score))
            bar_mid = bar_x + bar_width // 2
            
            if score > 0:
                bar_color = (0, 255, 100) if is_best_move else (0, 200, 80)
                pygame.draw.rect(win, bar_color, (bar_mid, bar_y, fill_width, bar_height), border_radius=6)
            else:
                bar_color = (255, 80, 80) if is_best_move else (200, 60, 60)
                pygame.draw.rect(win, bar_color, (bar_mid - fill_width, bar_y, fill_width, bar_height), border_radius=6)
            
            y_offset += 25

    def draw_statistics_panel(self, win, font, small_font):
        panel_rect = pygame.Rect(STATS_PANEL_X, BOARD_Y, STATS_PANEL_WIDTH, BOARD_SIZE)
        
        pygame.draw.rect(win, DARK_GRAY, panel_rect, border_radius=10)
        pygame.draw.rect(win, SILVER, panel_rect, 2, border_radius=10)
        
        title_text = font.render("Stats", True, GOLD)
        win.blit(title_text, (STATS_PANEL_X + 10, BOARD_Y + 15))
        
        y_offset = BOARD_Y + 60
        
        stats = [
            ("Turn:", str(self.turn_count)),
            ("Total Pieces:", str(sum(self.get_score()))),
            ("Mobility Diff:", str(self.get_mobility_score(PLAYER_BLACK) - self.get_mobility_score(PLAYER_WHITE))),
            ("Corner Control:", f"{self.get_corner_score(PLAYER_BLACK)}-{self.get_corner_score(PLAYER_WHITE)}"),
            ("Edge Control:", f"{self.get_edge_score(PLAYER_BLACK)}-{self.get_edge_score(PLAYER_WHITE)}"),
        ]
        
        if self.ai_think_time > 0:
            stats.append(("AI Think Time:", f"{self.ai_think_time:.1f}s"))
        
        for label, value in stats:
            label_surf = small_font.render(label, True, WHITE)
            value_surf = small_font.render(value, True, CYAN)
            win.blit(label_surf, (STATS_PANEL_X + 10, y_offset))
            win.blit(value_surf, (STATS_PANEL_X + 10, y_offset + 15))
            y_offset += 40


# =============================================================================
# 3. Advanced AI
# =============================================================================

def advanced_evaluate_board(board, player, total_pieces, depth_remaining=0):

    opponent = -player
    
    if total_pieces < 20:  # Opening
        phase_weights = {
            'piece': 1, 'mobility': 20, 'corner': 150, 'edge': 10,
            'stability': 100, 'position': 15, 'parity': 5
        }
    elif total_pieces < 52:  # Mid-game
        phase_weights = {
            'piece': 8, 'mobility': 15, 'corner': 120, 'edge': 15,
            'stability': 120, 'position': 12, 'parity': 10
        }
    else:  # End-game
        phase_weights = {
            'piece': 25, 'mobility': 8, 'corner': 140, 'edge': 20,
            'stability': 140, 'position': 5, 'parity': 30
        }
    
    score = 0
    
    # 1. Piece count with parity consideration
    my_pieces = sum(row.count(player) for row in board)
    opp_pieces = sum(row.count(opponent) for row in board)
    piece_diff = my_pieces - opp_pieces
    
    # Parity bonus in endgame
    if total_pieces > 55:
        remaining_moves = 64 - total_pieces
        if remaining_moves % 2 == 1:  # Odd number of moves left
            piece_diff += 0.5  # Slight advantage to current player
    
    score += phase_weights['piece'] * piece_diff
    
    # 2. Enhanced mobility calculation
    temp_game = Othello(sounds={})
    temp_game.board = board
    my_moves = len(temp_game.get_valid_moves(player))
    opp_moves = len(temp_game.get_valid_moves(opponent))
    
    if my_moves + opp_moves > 0:
        mobility_ratio = (my_moves - opp_moves) / (my_moves + opp_moves + 1)
        score += phase_weights['mobility'] * mobility_ratio * 100
    
    # Mobility desperation factor
    if my_moves == 0 and opp_moves > 0:
        score -= 500  # Very bad position
    elif opp_moves == 0 and my_moves > 0:
        score += 500  # Very good position
    
    # 3. Corner control with adjacency penalties
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    corner_adjacencies = [
        [(0,1), (1,0), (1,1)],  # Adjacent to (0,0)
        [(0,6), (1,7), (1,6)],  # Adjacent to (0,7)
        [(6,0), (7,1), (6,1)],  # Adjacent to (7,0)
        [(6,7), (7,6), (6,6)]   # Adjacent to (7,7)
    ]
    
    my_corners = opp_corners = 0
    for i, (r, c) in enumerate(corners):
        if board[r][c] == player:
            my_corners += 1
        elif board[r][c] == opponent:
            opp_corners += 1
        elif board[r][c] == EMPTY:
            # Penalty for occupying squares adjacent to empty corners
            for adj_r, adj_c in corner_adjacencies[i]:
                if board[adj_r][adj_c] == player:
                    score -= 25
                elif board[adj_r][adj_c] == opponent:
                    score += 25
    
    score += phase_weights['corner'] * (my_corners - opp_corners)
    
    # 4. Edge control
    edges = [(i, 0) for i in range(8)] + [(i, 7) for i in range(8)] + \
            [(0, i) for i in range(1, 7)] + [(7, i) for i in range(1, 7)]
    
    my_edges = sum(1 for r, c in edges if board[r][c] == player)
    opp_edges = sum(1 for r, c in edges if board[r][c] == opponent)
    score += phase_weights['edge'] * (my_edges - opp_edges)
    
    # 5. Advanced stability calculation
    my_stable = count_advanced_stable_pieces(board, player)
    opp_stable = count_advanced_stable_pieces(board, opponent)
    score += phase_weights['stability'] * (my_stable - opp_stable)
    
    # 6. Positional values
    position_score = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                position_score += POSITION_VALUES[r][c]
            elif board[r][c] == opponent:
                position_score -= POSITION_VALUES[r][c]
    score += phase_weights['position'] * position_score
    
    # 7. Advanced pattern recognition
    score += evaluate_patterns(board, player) * 10
    
    # 8. Depth bonus for deeper search
    if depth_remaining > 0:
        score += depth_remaining * 2
    
    return score

def count_advanced_stable_pieces(board, player):
    stable_count = 0
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                stability_score = 0
                
                if (r, c) in [(0, 0), (0, 7), (7, 0), (7, 7)]:
                    stable_count += 1
                    continue
                
                if r == 0 or r == 7 or c == 0 or c == 7:
                    edge_stable = True
                    if r == 0 or r == 7:  # Top/bottom edge
                        for dc in [-1, 1]:
                            nc = c + dc
                            while 0 <= nc < 8:
                                if board[r][nc] != player:
                                    edge_stable = False
                                    break
                                nc += dc
                    if c == 0 or c == 7:  # Left/right edge
                        for dr in [-1, 1]:
                            nr = r + dr
                            while 0 <= nr < 8:
                                if board[nr][c] != player:
                                    edge_stable = False
                                    break
                                nr += dr
                    if edge_stable:
                        stability_score += 1
                
                # Internal stability (surrounded by own pieces)
                surrounded = True
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if board[nr][nc] != player:
                                surrounded = False
                                break
                    if not surrounded:
                        break
                
                if surrounded:
                    stability_score += 0.5
                
                stable_count += stability_score
    
    return stable_count

def evaluate_patterns(board, player):
    """Evaluate common Othello patterns."""
    score = 0
    opponent = -player
    
    # X-square pattern (bad squares next to corners)
    x_squares = [(1, 1), (1, 6), (6, 1), (6, 6)]
    corner_pairs = [((0, 0), (1, 1)), ((0, 7), (1, 6)), ((7, 0), (6, 1)), ((7, 7), (6, 6))]
    
    for (cr, cc), (xr, xc) in corner_pairs:
        if board[cr][cc] == EMPTY and board[xr][xc] == player:
            score -= 20  # Penalty for X-square occupation
    
    # C-square pattern (squares adjacent to corners)
    c_squares = [
        [(0, 1), (1, 0)],  # Adjacent to (0, 0)
        [(0, 6), (1, 7)],  # Adjacent to (0, 7)
        [(6, 0), (7, 1)],  # Adjacent to (7, 0)
        [(6, 7), (7, 6)]   # Adjacent to (7, 7)
    ]
    
    for i, adjacent_squares in enumerate(c_squares):
        corner_r, corner_c = [(0, 0), (0, 7), (7, 0), (7, 7)][i]
        if board[corner_r][corner_c] == EMPTY:
            for ar, ac in adjacent_squares:
                if board[ar][ac] == player:
                    score -= 10 
    
    # Wall patterns (edges controlled by one player)
    for edge in [0, 7]:  # Top and bottom edges
        edge_control = sum(1 if board[edge][c] == player else -1 if board[edge][c] == opponent else 0 
                          for c in range(8))
        if abs(edge_control) > 4:
            score += edge_control * 5
    
    for edge in [0, 7]:  # Left and right edges
        edge_control = sum(1 if board[r][edge] == player else -1 if board[r][edge] == opponent else 0 
                          for r in range(8))
        if abs(edge_control) > 4:
            score += edge_control * 5
    
    return score

def enhanced_minimax_alphabeta(game_state, depth, alpha, beta, maximizing_player, ai_player, total_pieces, start_time, time_limit=10.0):
    if time.time() - start_time > time_limit:
        return advanced_evaluate_board(game_state.board, ai_player, total_pieces, depth), None, []
    
    if depth == 0 or game_state.game_over:
        eval_score = advanced_evaluate_board(game_state.board, ai_player, total_pieces, depth)
        return eval_score, None, []

    valid_moves = game_state.valid_moves
    if not valid_moves:
        next_state = game_state.copy()
        next_state._switch_player()
        return enhanced_minimax_alphabeta(next_state, depth - 1, alpha, beta, not maximizing_player, 
                                        ai_player, total_pieces, start_time, time_limit)

    move_scores = []
    for move in valid_moves:
        quick_score = 0
        r, c = move
        
        if (r, c) in [(0, 0), (0, 7), (7, 0), (7, 7)]:
            quick_score += 1000
        
        quick_score += len(valid_moves[move]) * 10
        
        quick_score += POSITION_VALUES[r][c]
        
        move_scores.append((quick_score, move))
    
    move_scores.sort(key=lambda x: x[0], reverse=maximizing_player)
    ordered_moves = [move for _, move in move_scores]

    evaluated_moves = []
    best_move = ordered_moves[0]

    if maximizing_player:
        max_eval = -math.inf
        for move in ordered_moves:
            if time.time() - start_time > time_limit:
                break
            
            next_state = game_state.copy()
            next_state.make_move(move[0], move[1])
            evaluation, _, _ = enhanced_minimax_alphabeta(next_state, depth - 1, alpha, beta, False, 
                                                       ai_player, total_pieces + 1, start_time, time_limit)
            evaluated_moves.append((evaluation, move))
            
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        evaluated_moves.sort(key=lambda x: x[0], reverse=True)
        return max_eval, best_move, evaluated_moves
    else:
        min_eval = math.inf
        for move in ordered_moves:
            if time.time() - start_time > time_limit:
                break
            
            next_state = game_state.copy()
            next_state.make_move(move[0], move[1])
            evaluation, _, _ = enhanced_minimax_alphabeta(next_state, depth - 1, alpha, beta, True, 
                                                       ai_player, total_pieces + 1, start_time, time_limit)
            evaluated_moves.append((evaluation, move))
            
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            
            beta = min(beta, evaluation)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        evaluated_moves.sort(key=lambda x: x[0])
        return min_eval, best_move, evaluated_moves

# =============================================================================
# 4. Enhanced UI and Game Management
# =============================================================================

def draw_enhanced_button(win, rect, text, font, button_color, text_color, border_color=None, hover_color=None, icon=None):
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)
    
    final_color = hover_color if is_hovered and hover_color else button_color
    
    if is_hovered:
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect(), border_radius=15)
        win.blit(shadow_surface, shadow_rect)
    
    pygame.draw.rect(win, final_color, rect, border_radius=15)
    
    gradient_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    for i in range(rect.height // 3):
        alpha = int(40 * (1 - i / (rect.height // 3)))
        color = (*WHITE[:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (rect.width, i))
    win.blit(gradient_surface, rect.topleft)
    
    if border_color:
        pygame.draw.rect(win, border_color, rect, 3, border_radius=15)
        # Inner highlight
        inner_rect = rect.inflate(-6, -6)
        highlight_color = tuple(min(255, c + 30) for c in final_color)
        pygame.draw.rect(win, highlight_color, inner_rect, 1, border_radius=12)
    
    if is_hovered:
        glow_rect = rect.inflate(4, 4)
        glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*final_color, 60), glow_surface.get_rect(), border_radius=17)
        win.blit(glow_surface, (glow_rect.x, glow_rect.y))
    
    text_surf = font.render(text, True, text_color)
    
    shadow_surf = font.render(text, True, (0, 0, 0, 100))
    shadow_rect = shadow_surf.get_rect(center=(rect.centerx + 1, rect.centery + 1))
    win.blit(shadow_surf, shadow_rect)
    
    text_rect = text_surf.get_rect(center=rect.center)
    win.blit(text_surf, text_rect)

def draw_animated_background(win):
    time_factor = time.time() * 0.5
    
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        wave = math.sin(time_factor + ratio * math.pi) * 0.1
        
        r = int(20 + wave * 20 + ratio * 15)
        g = int(40 + wave * 30 + ratio * 25)
        b = int(20 + wave * 20 + ratio * 35)
        
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        pygame.draw.line(win, (r, g, b), (0, y), (WIDTH, y))

def enhanced_main_menu(win, font, big_font):
    global AI_DIFFICULTY
    
    pvp_button = pygame.Rect(WIDTH // 2 - 200, 300, 400, 70)
    pvb_button = pygame.Rect(WIDTH // 2 - 200, 390, 400, 70)
    bvb_button = pygame.Rect(WIDTH // 2 - 200, 480, 400, 70)
    quit_button = pygame.Rect(WIDTH // 2 - 200, 570, 400, 70)
    
    diff_buttons = {
        Difficulty.EASY: pygame.Rect(WIDTH // 2 - 250, 680, 90, 45),
        Difficulty.MEDIUM: pygame.Rect(WIDTH // 2 - 150, 680, 90, 45),
        Difficulty.HARD: pygame.Rect(WIDTH // 2 - 50, 680, 90, 45),
        Difficulty.EXPERT: pygame.Rect(WIDTH // 2 + 50, 680, 90, 45),
        Difficulty.GRANDMASTER: pygame.Rect(WIDTH // 2 + 150, 680, 90, 45),
    }

    play_as_black_button = pygame.Rect(WIDTH // 2 - 250, 390, 220, 70)
    play_as_white_button = pygame.Rect(WIDTH // 2 + 30, 390, 220, 70)
    back_button = pygame.Rect(WIDTH // 2 - 100, 480, 200, 60)
    
    clock = pygame.time.Clock()
    menu_state = "main"

    while True:
        draw_animated_background(win)
        
        title_time = time.time() * 2
        title_offset = int(math.sin(title_time) * 3)
        
        title_shadow = big_font.render("🏁 OTHELLO AI 🏁", True, (20, 20, 20))
        win.blit(title_shadow, (WIDTH // 2 - title_shadow.get_width() // 2 + 4, 154 + title_offset))
        
        title_text = big_font.render("OTHELLO AI", True, GOLD)
        win.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150 + title_offset))

        if menu_state == "main":
            subtitle_text = font.render("Choose Your Battle Mode", True, WHITE)
            win.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, 240))

            draw_enhanced_button(win, pvp_button, "Player vs Player", font, BLUE, WHITE, DARK_BLUE, (100, 160, 220))
            draw_enhanced_button(win, pvb_button, "Player vs AI", font, PURPLE, WHITE, DEEP_PURPLE, (150, 100, 200))
            draw_enhanced_button(win, bvb_button, "AI vs AI", font, ORANGE, WHITE, (200, 100, 0), (255, 180, 50))
            draw_enhanced_button(win, quit_button, "Quit", font, RED, WHITE, (150, 0, 0), (255, 100, 100))
        
        elif menu_state == "choose_color":
            subtitle_text = font.render("Choose Your Color", True, WHITE)
            win.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, 240))
            
            draw_enhanced_button(win, play_as_black_button, "Play as Black", font, (50, 50, 50), WHITE, BLACK, (80, 80, 80))
            draw_enhanced_button(win, play_as_white_button, "Play as White", font, (220, 220, 220), BLACK, GRAY, WHITE)
            draw_enhanced_button(win, back_button, "Back", font, GRAY, BLACK, DARK_GRAY, LIGHT_GRAY)

        diff_text = font.render("AI Intelligence Level:", True, WHITE)
        win.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 640))
        
        difficulty_colors = {
            Difficulty.EASY: (100, 255, 100),
            Difficulty.MEDIUM: (255, 255, 100),
            Difficulty.HARD: (255, 150, 100),
            Difficulty.EXPERT: (255, 100, 100),
            Difficulty.GRANDMASTER: (150, 100, 255)
        }
        
        for diff, button in diff_buttons.items():
            base_color = difficulty_colors[diff]
            is_selected = AI_DIFFICULTY == diff
            
            if is_selected:
                pulse = int(50 + 30 * math.sin(time.time() * 4))
                color = tuple(min(255, c + pulse) for c in base_color)
                border_color = GOLD
            else:
                color = base_color
                border_color = DARK_GRAY
            
            draw_enhanced_button(win, button, diff.name, pygame.font.Font(None, 20), 
                               color, BLACK, border_color, tuple(min(255, c + 50) for c in color))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if menu_state == "main":
                    if pvp_button.collidepoint(event.pos):
                        return "PvP", None
                    if pvb_button.collidepoint(event.pos):
                        menu_state = "choose_color"
                    if bvb_button.collidepoint(event.pos):
                        return "BvB", None
                    if quit_button.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
                elif menu_state == "choose_color":
                    if play_as_black_button.collidepoint(event.pos):
                        return "PvB", PLAYER_BLACK
                    if play_as_white_button.collidepoint(event.pos):
                        return "PvB", PLAYER_WHITE
                    if back_button.collidepoint(event.pos):
                        menu_state = "main"

                # Handle difficulty selection
                for diff, button in diff_buttons.items():
                    if button.collidepoint(event.pos):
                        AI_DIFFICULTY = diff
        
        pygame.display.flip()
        clock.tick(60)

def enhanced_ai_move_thread(game):
    try:
        start_time = time.time()
        total_pieces = sum(row.count(PLAYER_BLACK) + row.count(PLAYER_WHITE) for row in game.board)
        
        time_limits = {
            Difficulty.EASY: 1.0,
            Difficulty.MEDIUM: 3.0,
            Difficulty.HARD: 8.0,
            Difficulty.EXPERT: 15.0,
            Difficulty.GRANDMASTER: 30.0
        }
        
        time_limit = time_limits[AI_DIFFICULTY]
        
        _, best_move, evaluated_moves = enhanced_minimax_alphabeta(
            game, AI_DIFFICULTY.value, -math.inf, math.inf, True, 
            game.current_player, total_pieces, start_time, time_limit
        )
        
        game.ai_decision_log = evaluated_moves
        game.ai_think_time = time.time() - start_time
        
        # Minimum thinking time for realism
        min_think_time = 0.5
        if game.ai_think_time < min_think_time:
            time.sleep(min_think_time - game.ai_think_time)
        
        if best_move:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'move': best_move}))
    except Exception as e:
        print(f"AI Error: {e}")

def enhanced_game_over_screen(win, font, big_font, winner, final_score, game_stats):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    win.blit(overlay, (0, 0))
    
    winner_time = time.time() * 3
    winner_offset = int(math.sin(winner_time) * 5)
    
    if winner == PLAYER_BLACK:
        winner_text, color = "BLACK VICTORIES!", GOLD
    elif winner == PLAYER_WHITE:
        winner_text, color = "WHITE TRIUMPHS!", SILVER
    else:
        winner_text, color = "PERFECT TIE!", PURPLE
    
    text_shadow = big_font.render(winner_text, True, (30, 30, 30))
    win.blit(text_shadow, (WIDTH // 2 - text_shadow.get_width() // 2 + 4, 204 + winner_offset))
    
    text_surf = big_font.render(winner_text, True, color)
    win.blit(text_surf, (WIDTH // 2 - text_surf.get_width() // 2, 200 + winner_offset))
    
    black_score, white_score = final_score
    stats_y = 320
    
    stats_surface = pygame.Surface((600, 300), pygame.SRCALPHA)
    pygame.draw.rect(stats_surface, (40, 40, 40, 200), stats_surface.get_rect(), border_radius=20)
    pygame.draw.rect(stats_surface, GOLD, stats_surface.get_rect(), 3, border_radius=20)
    
    stats_font = pygame.font.Font(None, 32)
    stats = [
        f"Final Score: Black {black_score} - White {white_score}",
        f"Total Turns: {game_stats.get('turns', 0)}",
        f"Game Duration: {game_stats.get('duration', 0):.1f} seconds",
        f"Average Think Time: {game_stats.get('avg_think_time', 0):.1f}s"
    ]
    
    for i, stat in enumerate(stats):
        stat_surf = stats_font.render(stat, True, WHITE)
        stats_surface.blit(stat_surf, (20, 20 + i * 40))
    
    win.blit(stats_surface, (WIDTH // 2 - 300, stats_y))
    
    play_again_button = pygame.Rect(WIDTH // 2 - 250, 650, 200, 60)
    main_menu_button = pygame.Rect(WIDTH // 2 + 50, 650, 200, 60)
    
    while True:
        draw_enhanced_button(win, play_again_button, "Play Again", font, GREEN, WHITE, DARK_GREEN, (120, 220, 120))
        draw_enhanced_button(win, main_menu_button, "Main Menu", font, BLUE, WHITE, DARK_BLUE, (120, 180, 220))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_button.collidepoint(event.pos):
                    return "play_again"
                if main_menu_button.collidepoint(event.pos):
                    return "main_menu"
        
        pygame.display.flip()
        pygame.time.wait(100)

def enhanced_pause_screen(win, font, big_font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    win.blit(overlay, (0, 0))

    pause_time = time.time() * 2
    pause_offset = int(math.sin(pause_time) * 3)
    
    paused_shadow = big_font.render("⏸️ GAME PAUSED ⏸️", True, (30, 30, 30))
    win.blit(paused_shadow, (WIDTH // 2 - paused_shadow.get_width() // 2 + 4, 254 + pause_offset))
    
    paused_text = big_font.render("GAME PAUSED", True, GOLD)
    win.blit(paused_text, (WIDTH // 2 - paused_text.get_width() // 2, 250 + pause_offset))

    resume_button = pygame.Rect(WIDTH // 2 - 250, 450, 200, 60)
    main_menu_button = pygame.Rect(WIDTH // 2 + 50, 450, 200, 60)

    while True:
        draw_enhanced_button(win, resume_button, "Resume", font, GREEN, WHITE, DARK_GREEN, (120, 220, 120))
        draw_enhanced_button(win, main_menu_button, "Main Menu", font, BLUE, WHITE, DARK_BLUE, (120, 180, 220))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_button.collidepoint(event.pos):
                    return "resume"
                if main_menu_button.collidepoint(event.pos):
                    return "main_menu"

        pygame.display.flip()
        pygame.time.wait(100)

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    GAME_OVER = 3
    PAUSED = 4

def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    
    sounds = {}
    sound_files = {
        'place': 'place_sound.wav',
        'flip': 'flip_sound.wav',
        'menu_music': 'menu_music.mp3',
        'game_music': 'game_music.mp3'
    }
    
    for sound_name, filename in sound_files.items():
        try:
            if 'music' in sound_name:
                continue
            sounds[sound_name] = pygame.mixer.Sound(filename)
        except pygame.error:
            print(f"Warning: Could not load {filename}")

    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Enhanced Othello AI Championship")
    
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    big_font = pygame.font.Font(None, 80)
    
    clock = pygame.time.Clock()
    
    game_state = GameState.MENU
    game = None
    game_mode = None
    human_color = None
    game_start_time = None

    while True:
        if game_state == GameState.MENU:
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.load('menu_music.mp3')
                    pygame.mixer.music.set_volume(0.3)
                    pygame.mixer.music.play(-1)
                except pygame.error:
                    pass
            
            game_mode, human_color = enhanced_main_menu(win, font, big_font)
            game = Othello(sounds)
            game_start_time = time.time()
            game_state = GameState.PLAYING
            
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.load('game_music.mp3')
                pygame.mixer.music.set_volume(0.2)
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

            if (game_mode == "BvB") or (game_mode == "PvB" and human_color != game.current_player):
                if not game.ai_thinking and game.valid_moves:
                    game.ai_thinking = True
                    threading.Thread(target=enhanced_ai_move_thread, args=(game,), daemon=True).start()

        elif game_state == GameState.PLAYING:
            is_human_turn = (game_mode == "PvP") or (game_mode == "PvB" and game.current_player == human_color)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_state = GameState.PAUSED
                        pygame.mixer.music.pause()
                    elif event.key == pygame.K_r and pygame.key.get_pressed()[pygame.K_LCTRL]:
                        game = Othello(sounds)
                        if (game_mode == "BvB") or (game_mode == "PvB" and human_color != game.current_player):
                            if not game.ai_thinking and game.valid_moves:
                                game.ai_thinking = True
                                threading.Thread(target=enhanced_ai_move_thread, args=(game,), daemon=True).start()

                if event.type == pygame.USEREVENT:
                    if 'move' in event.dict:
                        made_move = game.make_move(event.move[0], event.move[1])
                        game.ai_thinking = False
                        
                        if made_move and not game.game_over:
                            is_still_ai_turn = (game_mode == "BvB") or (game_mode == "PvB" and game.current_player != human_color)
                            if is_still_ai_turn and not game.ai_thinking and game.valid_moves:
                                game.ai_thinking = True
                                threading.Thread(target=enhanced_ai_move_thread, args=(game,), daemon=True).start()

                if is_human_turn and event.type == pygame.MOUSEBUTTONDOWN and not game.ai_thinking:
                    x, y = event.pos
                    if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
                        col = (x - BOARD_X) // SQUARE_SIZE
                        row = (y - BOARD_Y) // SQUARE_SIZE
                        made_move = game.make_move(row, col)
                        
                        if made_move and not game.game_over:
                            is_now_ai_turn = (game_mode == "BvB") or (game_mode == "PvB" and game.current_player != human_color)
                            if is_now_ai_turn and not game.ai_thinking and game.valid_moves:
                                game.ai_thinking = True
                                threading.Thread(target=enhanced_ai_move_thread, args=(game,), daemon=True).start()
                
                if event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    if BOARD_X <= x < BOARD_X + BOARD_SIZE and BOARD_Y <= y < BOARD_Y + BOARD_SIZE:
                        game.hover_pos = ((y - BOARD_Y) // SQUARE_SIZE, (x - BOARD_X) // SQUARE_SIZE)
                    else:
                        game.hover_pos = None
            
            draw_animated_background(win)
            game.draw(win, font, small_font, game_mode)
            
            if game.game_over:
                game_state = GameState.GAME_OVER

        elif game_state == GameState.PAUSED:
            result = enhanced_pause_screen(win, font, big_font)
            if result == "resume":
                game_state = GameState.PLAYING
                pygame.mixer.music.unpause()
            elif result == "main_menu":
                game_state = GameState.MENU
                pygame.mixer.music.stop()

        elif game_state == GameState.GAME_OVER:
            game_duration = time.time() - game_start_time if game_start_time else 0
            avg_think_time = sum(entry.get('time', 0) for entry in game.game_history) / max(len(game.game_history), 1)
            
            game_stats = {
                'turns': game.turn_count,
                'duration': game_duration,
                'avg_think_time': avg_think_time
            }
            
            result = enhanced_game_over_screen(win, font, big_font, game.winner, game.get_score(), game_stats)
            if result == "play_again":
                game = Othello(sounds)
                game_start_time = time.time()
                game_state = GameState.PLAYING
                
                if (game_mode == "BvB") or (game_mode == "PvB" and human_color != game.current_player):
                    if not game.ai_thinking and game.valid_moves:
                        game.ai_thinking = True
                        threading.Thread(target=enhanced_ai_move_thread, args=(game,), daemon=True).start()
            else:
                game_state = GameState.MENU
                pygame.mixer.music.stop()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()