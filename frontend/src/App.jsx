import React, { useState, useEffect, useCallback, useRef } from 'react';
import MainMenu from './components/MainMenu';
import Board from './components/Board';
import HUD from './components/HUD';
import AIDebugPanel from './components/AIDebugPanel';
import GameOverScreen from './components/GameOverScreen';
import PauseScreen from './components/PauseScreen';
import './index.css';

const App = () => {
    const [gameState, setGameState] = useState(null);
    const [screen, setScreen] = useState('menu');
    const [gameMode, setGameMode] = useState(null);
    const [humanColor, setHumanColor] = useState(null);
    const [difficulty, setDifficulty] = useState('MEDIUM');
    const wsRef = useRef(null); // Use ref to persist WebSocket across renders

    // Initialize WebSocket connection
    const connectWebSocket = useCallback(() => {
        const websocket = new WebSocket('ws://localhost:3000/ws');
        wsRef.current = websocket;

        websocket.onopen = () => {
            console.log('WebSocket Connected');
        };

        websocket.onmessage = (event) => {
            console.log('Received:', event.data); // Debug received data
            const data = JSON.parse(event.data);
            setGameState(data);
            if (data.game_over) {
                setScreen('game_over');
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };

        websocket.onclose = (event) => {
            console.log('WebSocket Disconnected:', event);
            wsRef.current = null; // Reset on close
            // Attempt to reconnect after 1 second
            setTimeout(connectWebSocket, 1000);
        };

        return websocket;
    }, []);

    useEffect(() => {
        connectWebSocket();

        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && screen === 'playing') {
                setScreen('paused');
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            if (wsRef.current) wsRef.current.close();
        };
    }, [connectWebSocket]);

    // Send message only if WebSocket is open
    const sendMessage = useCallback((message) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
            console.log('Sent:', message); // Debug sent message
        } else {
            console.warn('WebSocket not open, message not sent:', message);
            if (!wsRef.current) connectWebSocket(); // Reconnect if closed
        }
    }, [connectWebSocket]);

    const startGame = (mode, color) => {
        setGameMode(mode);
        setHumanColor(color);
        sendMessage({ action: 'start_game', mode, human_color: color, difficulty });
        setScreen('playing');
    };

    const makeMove = (row, col) => {
        if (gameState && !gameState.ai_thinking && gameState.valid_moves.some(([r, c]) => r === row && c === col)) {
            sendMessage({ action: 'make_move', row, col });
        }
    };

    const handleGameOverAction = (action) => {
        if (action === 'play_again') {
            sendMessage({ action: 'start_game', mode: gameMode, human_color: humanColor, difficulty });
            setScreen('playing');
        } else {
            setScreen('menu');
        }
    };

    const handlePauseAction = (action) => {
        if (action === 'resume') {
            setScreen('playing');
        } else {
            setScreen('menu');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-green-900 to-green-700 flex items-center justify-center">
            {screen === 'menu' && (
                <MainMenu startGame={startGame} setDifficulty={setDifficulty} difficulty={difficulty} />
            )}
            {screen === 'playing' && gameState && (
                <div className="flex flex-col lg:flex-row items-start space-y-4 lg:space-y-0 lg:space-x-4">
                    <div>
                        <HUD gameState={gameState} gameMode={gameMode} humanColor={humanColor} />
                        <Board gameState={gameState} makeMove={makeMove} gameMode={gameMode} humanColor={humanColor} />
                    </div>
                    {(gameMode !== 'PvP') && (
                        <AIDebugPanel gameState={gameState} difficulty={difficulty} />
                    )}
                </div>
            )}
            {screen === 'game_over' && gameState && (
                <GameOverScreen gameState={gameState} handleAction={handleGameOverAction} />
            )}
            {screen === 'paused' && (
                <PauseScreen handleAction={handlePauseAction} />
            )}
        </div>
    );
};

export default App;