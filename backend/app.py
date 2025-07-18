import asyncio
import json
import threading
import math
import time
from flask import Flask, jsonify
from flask_sock import Sock
from game_logic import Othello, Difficulty, minimax_alphabeta


app = Flask(__name__)
sock = Sock(app)

# Game state
game = None
game_mode = None
human_color = None
ai_thinking = False
ai_thread = None
connected_clients = set()

@app.route('/')
def index():
    return jsonify({"message": "Othello Webapp Backend"})

@sock.route('/ws')
def websocket_handler(ws):
    global game, ai_thinking
    connected_clients.add(ws)
    print(f"New WebSocket connection from {ws.remote_address}")
    if game:
        ws.send(json.dumps({
            'board': game.board,
            'current_player': game.current_player,
            'valid_moves': list(game.valid_moves.keys()),
            'game_over': game.game_over,
            'winner': game.winner,
            'score': game.get_score(),
            'ai_decision_log': game.ai_decision_log,
            'ai_thinking': ai_thinking
        }))
    while True:
        data = json.loads(ws.receive())
        print(f"Received from {ws.remote_address}: {data}")
        if data.get('action') == 'start_game':
            global game_mode, human_color
            game_mode = data['mode']
            human_color = data.get('human_color')
            difficulty = Difficulty[data['difficulty'].upper()]
            game = Othello({})
            game.ai_decision_log = []
            ai_thinking = False
            broadcast_game_state()
            if game_mode == 'BvB' or (game_mode == 'PvB' and human_color != game.current_player):
                trigger_ai_move()
        elif data.get('action') == 'make_move':
            row, col = data['row'], data['col']
            if game and (row, col) in game.valid_moves:
                game.make_move(row, col)
                ai_thinking = False
                broadcast_game_state()
                if not game.game_over and (game_mode == 'BvB' or (game_mode == 'PvB' and game.current_player != human_color)):
                    trigger_ai_move()

def broadcast_game_state():
    state = {
        'board': game.board,
        'current_player': game.current_player,
        'valid_moves': list(game.valid_moves.keys()),
        'game_over': game.game_over,
        'winner': game.winner,
        'score': game.get_score(),
        'ai_decision_log': game.ai_decision_log,
        'ai_thinking': ai_thinking
    }
    for client in connected_clients:
        client.send(json.dumps(state))

def trigger_ai_move():
    global ai_thinking, ai_thread
    if not ai_thinking and game and game.valid_moves:
        ai_thinking = True
        broadcast_game_state()
        ai_thread = threading.Thread(target=ai_move_thread_worker)
        ai_thread.start()

def ai_move_thread_worker():
    global ai_thinking
    try:
        total_pieces = sum(row.count(1) + row.count(-1) for row in game.board)
        _, best_move, evaluated_moves = minimax_alphabeta(
            game, Difficulty[game_mode.upper()].value if game_mode != 'PvP' else Difficulty.MEDIUM.value,
            -math.inf, math.inf, True, game.current_player, total_pieces
        )
        game.ai_decision_log = evaluated_moves
        time.sleep(0.5)  # Simulate thinking time
        if best_move:
            game.make_move(best_move[0], best_move[1])
        ai_thinking = False
        broadcast_game_state()
    except Exception as e:
        print(f"AI Error: {e}")
        ai_thinking = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)