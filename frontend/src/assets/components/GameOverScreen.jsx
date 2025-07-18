import React from 'react';

const GameOverScreen = ({ gameState, handleAction }) => {
    const { winner, score } = gameState;
    let winnerText, color;
    if (winner === 1) {
        winnerText = "Black Wins!";
        color = 'text-yellow-400';
    } else if (winner === -1) {
        winnerText = "White Wins!";
        color = 'text-gray-300';
    } else {
        winnerText = "It's a Tie!";
        color = 'text-purple-400';
    }

    return (
        <div className="bg-gray-800 p-8 rounded-xl shadow-lg text-center bg-opacity-90">
            <h1 className={`text-5xl ${color} mb-6`}>{winnerText}</h1>
            <p className="text-white text-xl mb-6">Final Score: Black {score[0]} - White {score[1]}</p>
            <button
                className="bg-green-600 text-white px-6 py-3 rounded-lg mr-4 hover:bg-green-400"
                onClick={() => handleAction('play_again')}
            >
                Play Again
            </button>
            <button
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-400"
                onClick={() => handleAction('main_menu')}
            >
                Main Menu
            </button>
        </div>
    );
};

export default GameOverScreen;