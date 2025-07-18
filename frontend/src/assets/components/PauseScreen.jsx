import React from 'react';

const PauseScreen = ({ handleAction }) => {
    return (
        <div className="bg-gray-800 p-8 rounded-xl shadow-lg text-center bg-opacity-90">
            <h1 className="text-5xl text-yellow-400 mb-6">Game Paused</h1>
            <button
                className="bg-green-600 text-white px-6 py-3 rounded-lg mr-4 hover:bg-green-400"
                onClick={() => handleAction('resume')}
            >
                Resume
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

export default PauseScreen;