import copy
import math
from enum import Enum

# Constants
PLAYER_BLACK = 1
PLAYER_WHITE = -1
EMPTY = 0
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

class Difficulty(Enum):
    EASY = 2
    MEDIUM = 4
    HARD = 6
    EXPERT = 8

class Othello:
    def __init__(self, sounds):
        self.board = [[EMPTY for _ in range(8)] for _ in range(8)]
        self.board[3][3], self.board[4][4] = PLAYER_WHITE, PLAYER_WHITE
        self.board[3][4], self.board[4][3] = PLAYER_BLACK, PLAYER_BLACK
        self.current_player = PLAYER_BLACK
        self.valid_moves = self.get_valid_moves(self.current_player)
        self.ai_decision_log = []
        self.game_over = False
        self.winner = None
        self.sounds = sounds

    def copy(self):
        new_game = Othello({})
        new_game.board = copy.deepcopy(self.board)
        new_game.current_player = self.current_player
        new_game.valid_moves = new_game.get_valid_moves(new_game.current_player)
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
            self.board[r][c] = self.current_player
            pieces_to_flip = self.valid_moves[(r, c)]
            for piece_pos in pieces_to_flip:
                self.board[piece_pos[0]][piece_pos[1]] = self.current_player
            self._switch_player()
            return True
        return False

    def _switch_player(self):
        self.current_player *= -1
        self.valid_moves = self.get_valid_moves(self.current_player)
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

def dynamic_evaluate_board(board, player, total_pieces):
    opponent = -player
    if total_pieces < 20:
        piece_weight, mobility_weight, corner_weight, stability_weight = 1, 15, 100, 80
    elif total_pieces < 52:
        piece_weight, mobility_weight, corner_weight, stability_weight = 5, 10, 100, 100
    else:
        piece_weight, mobility_weight, corner_weight, stability_weight = 20, 5, 120, 120

    score = 0
    my_pieces = sum(row.count(player) for row in board)
    opp_pieces = sum(row.count(opponent) for row in board)
    score += piece_weight * (my_pieces - opp_pieces)

    temp_game = Othello({})
    temp_game.board = board
    my_moves = len(temp_game.get_valid_moves(player))
    opp_moves = len(temp_game.get_valid_moves(opponent))
    if my_moves + opp_moves > 0:
        score += mobility_weight * (my_moves - opp_moves)

    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    my_corners, opp_corners = 0, 0
    for r, c in corners:
        if board[r][c] == player:
            my_corners += 1
        elif board[r][c] == opponent:
            opp_corners += 1
    score += corner_weight * (my_corners - opp_corners)

    for r_c, c_c in corners:
        if board[r_c][c_c] == EMPTY:
            for dr, dc in [(0,1), (1,0), (1,1)]:
                if 0 <= r_c+dr < 8 and 0 <= c_c+dc < 8 and board[r_c+dr][c_c+dc] == player:
                    score -= 15
                if 0 <= r_c-dr < 8 and 0 <= c_c+dc < 8 and board[r_c-dr][c_c+dc] == player:
                    score -= 15
                if 0 <= r_c+dr < 8 and 0 <= c_c-dc < 8 and board[r_c+dr][c_c-dc] == player:
                    score -= 15

    my_stable = count_stable_pieces(board, player)
    opp_stable = count_stable_pieces(board, opponent)
    score += stability_weight * (my_stable - opp_stable)
    return score

def count_stable_pieces(board, player):
    stable_count = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                is_stable = True
                for dr, dc in [(1, 0), (1, 1), (0, 1), (-1, 1)]:
                    side1_secure = False
                    curr_r, curr_c = r + dr, c + dc
                    while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                        if board[curr_r][curr_c] != player:
                            side1_secure = True
                            break
                        curr_r, curr_c = curr_r + dr, curr_c + dc
                    if not (0 <= curr_r < 8 and 0 <= curr_c < 8):
                        side1_secure = True
                    
                    side2_secure = False
                    curr_r, curr_c = r - dr, c - dc
                    while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                        if board[curr_r][curr_c] != player:
                            side2_secure = True
                            break
                        curr_r, curr_c = curr_r - dr, curr_c - dc
                    if not (0 <= curr_r < 8 and 0 <= curr_c < 8):
                        side2_secure = True
                        
                    if not (side1_secure and side2_secure):
                        is_stable = False
                        break
                if is_stable:
                    stable_count += 1
    return stable_count

def minimax_alphabeta(game_state, depth, alpha, beta, maximizing_player, ai_player, total_pieces):
    if depth == 0 or game_state.game_over:
        return dynamic_evaluate_board(game_state.board, ai_player, total_pieces), None, []

    valid_moves = game_state.valid_moves
    if not valid_moves:
        next_state = game_state.copy()
        next_state._switch_player()
        return minimax_alphabeta(next_state, depth - 1, alpha, beta, not maximizing_player, ai_player, total_pieces)

    evaluated_moves = []
    best_move = list(valid_moves.keys())[0]

    if maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            next_state = game_state.copy()
            next_state.make_move(move[0], move[1])
            evaluation, _, _ = minimax_alphabeta(next_state, depth - 1, alpha, beta, False, ai_player, total_pieces + 1)
            evaluated_moves.append((evaluation, move))
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        evaluated_moves.sort(key=lambda x: x[0], reverse=True)
        return max_eval, best_move, evaluated_moves
    else:
        min_eval = math.inf
        for move in valid_moves:
            next_state = game_state.copy()
            next_state.make_move(move[0], move[1])
            evaluation, _, _ = minimax_alphabeta(next_state, depth - 1, alpha, beta, True, ai_player, total_pieces + 1)
            evaluated_moves.append((evaluation, move))
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        evaluated_moves.sort(key=lambda x: x[0])
        return min_eval, best_move, evaluated_moves