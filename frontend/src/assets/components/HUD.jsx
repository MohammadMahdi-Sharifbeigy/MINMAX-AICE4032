import React from 'react';

const HUD = ({ gameState, gameMode, humanColor }) => {
    const { score, current_player, ai_thinking } = gameState;
    const isHumanTurn = gameMode === 'PvP' || (gameMode === 'PvB' && current_player === humanColor);

    return (
        <div className="bg-gray-800 p-4 rounded-xl shadow-lg mb-4 flex justify-between items-center" style={{ width: '560px' }}>
            <div className="flex items-center">
                <div className="w-10 h-10 bg-black rounded-full shadow-md mr-2" />
                <span className="text-white text-xl">{score[0]}</span>
            </div>
            <div className="text-white text-xl">
                {ai_thinking ? 'AI Thinking...' : (current_player === 1 ? "Black's Turn" : "White's Turn")}
            </div>
            <div className="flex items-center">
                <span className="text-white text-xl mr-2">{score[1]}</span>
                <div className="w-10 h-10 bg-white rounded-full shadow-md" />
            </div>
        </div>
    );
};

export default HUD;