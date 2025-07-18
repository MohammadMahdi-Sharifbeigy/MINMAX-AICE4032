import React, { useState } from 'react';

const MainMenu = ({ startGame, setDifficulty, difficulty }) => {
    const [menuState, setMenuState] = useState('main');

    return (
        <div className="bg-gray-800 p-8 rounded-xl shadow-lg text-center">
            <h1 className="text-5xl text-yellow-400 mb-6">Othello AI</h1>
            {menuState === 'main' ? (
                <>
                    <p className="text-white text-xl mb-6">Choose your game mode</p>
                    <button
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400"
                        onClick={() => startGame('PvP', null)}
                    >
                        Player vs Player
                    </button>
                    <button
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400"
                        onClick={() => setMenuState('choose_color')}
                    >
                        Player vs Bot
                    </button>
                    <button
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400"
                        onClick={() => startGame('BvB', null)}
                    >
                        Bot vs Bot
                    </button>
                    <button
                        className="bg-red-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-red-400"
                        onClick={() => window.close()}
                    >
                        Quit
                    </button>
                </>
            ) : (
                <>
                    <p className="text-white text-xl mb-6">Choose your color</p>
                    <button
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400 mr-4"
                        onClick={() => startGame('PvB', 1)}
                    >
                        Play as Black
                    </button>
                    <button
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400"
                        onClick={() => startGame('PvB', -1)}
                    >
                        Play as White
                    </button>
                    <button
                        className="bg-gray-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-gray-400"
                        onClick={() => setMenuState('main')}
                    >
                        Back
                    </button>
                </>
            )}
            <div className="mt-6">
                <p className="text-white text-xl mb-2">AI Difficulty:</p>
                <div className="flex justify-center space-x-2">
                    {['EASY', 'MEDIUM', 'HARD', 'EXPERT'].map((diff) => (
                        <button
                            key={diff}
                            className={`px-4 py-2 rounded-lg ${difficulty === diff ? 'bg-orange-500' : 'bg-gray-600'} text-white hover:bg-gray-400`}
                            onClick={() => setDifficulty(diff)}
                        >
                            {diff}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default MainMenu;