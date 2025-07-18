import React, { useState, useEffect } from 'react';

const Board = ({ gameState, makeMove, gameMode, humanColor }) => {
    const [hoverPos, setHoverPos] = useState(null);
    const [animations, setAnimations] = useState([]);
    const isHumanTurn = gameMode === 'PvP' || (gameMode === 'PvB' && gameState.current_player === humanColor);

    useEffect(() => {
        const interval = setInterval(() => {
            setAnimations((prev) => prev.filter(anim => (Date.now() - anim.start_time) / 1000 < anim.duration));
        }, 50);
        return () => clearInterval(interval);
    }, []);

    const handleClick = (row, col) => {
        if (isHumanTurn && !gameState.ai_thinking) {
            makeMove(row, col);
            const piecesToFlip = gameState.valid_moves.find(([r, c]) => r === row && c === col)?.[1] || [];
            const newAnimations = piecesToFlip.map((pos, i) => ({
                type: 'flip',
                pos,
                start_time: Date.now() + i * 50,
                duration: 0.4,
                from_player: -gameState.current_player,
                to_player: gameState.current_player
            }));
            setAnimations([...animations, ...newAnimations]);
        }
    };

    const getPieceStyle = (row, col, player, progress = 1) => {
        const size = progress < 0.5 ? 1 - progress * 2 : (progress - 0.5) * 2;
        const radius = 40 * size;
        return {
            width: `${radius}px`,
            height: `${radius}px`,
            backgroundColor: player === 1 ? 'black' : player === -1 ? 'white' : 'transparent',
            borderRadius: '50%',
            boxShadow: player !== 0 ? '2px 2px 5px rgba(0,0,0,0.5), -2px -2px 5px rgba(255,255,255,0.3)' : 'none',
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)'
        };
    };

    return (
        <div className="bg-amber-900 p-4 rounded-xl shadow-lg" style={{ width: '560px', height: '560px' }}>
            <div className="grid grid-cols-8 gap-0" style={{ width: '100%', height: '100%' }}>
                {gameState.board.map((row, r) => (
                    row.map((cell, c) => {
                        const isValidMove = gameState.valid_moves.some(([vr, vc]) => vr === r && vc === c);
                        const isLastMove = gameState.last_move && gameState.last_move[0] === r && gameState.last_move[1] === c;
                        const animation = animations.find(anim => anim.pos[0] === r && anim.pos[1] === c);
                        const progress = animation ? Math.min((Date.now() - animation.start_time) / (animation.duration * 1000), 1) : 1;
                        const player = animation ? (progress < 0.5 ? animation.from_player : animation.to_player) : cell;

                        return (
                            <div
                                key={`${r}-${c}`}
                                className={`relative border border-gray-700 ${(r + c) % 2 === 0 ? 'bg-green-600' : 'bg-green-800'} ${isLastMove ? 'ring-2 ring-yellow-400' : ''}`}
                                style={{ width: '70px', height: '70px' }}
                                onClick={() => handleClick(r, c)}
                                onMouseEnter={() => setHoverPos([r, c])}
                                onMouseLeave={() => setHoverPos(null)}
                            >
                                {player !== 0 && !animation && (
                                    <div style={getPieceStyle(r, c, player)} />
                                )}
                                {animation && (
                                    <div style={getPieceStyle(r, c, player, progress)} />
                                )}
                                {isValidMove && isHumanTurn && !gameState.ai_thinking && (
                                    <div
                                        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                                        style={{
                                            width: '16px',
                                            height: '16px',
                                            backgroundColor: gameState.current_player === 1 ? 'rgba(0,255,255,0.6)' : 'rgba(255,165,0,0.6)',
                                            borderRadius: '50%',
                                            animation: 'pulse 1.5s infinite'
                                        }}
                                    />
                                )}
                                {hoverPos && hoverPos[0] === r && hoverPos[1] === c && isValidMove && (
                                    <div
                                        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                                        style={{
                                            width: '40px',
                                            height: '40px',
                                            backgroundColor: gameState.current_player === 1 ? 'rgba(0,0,0,0.4)' : 'rgba(255,255,255,0.4)',
                                            borderRadius: '50%'
                                        }}
                                    />
                                )}
                            </div>
                        );
                    })
                ))}
            </div>
        </div>
    );
};

export default Board;