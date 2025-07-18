import React from 'react';

const AIDebugPanel = ({ gameState, difficulty }) => {
    const { ai_decision_log } = gameState;
    const maxScore = ai_decision_log.length > 0 ? Math.max(...ai_decision_log.map(([score]) => Math.abs(score))) : 1;

    return (
        <div className="bg-gray-800 p-4 rounded-xl shadow-lg" style={{ width: '450px', height: '560px', overflowY: 'auto' }}>
            <h2 className="text-white text-xl mb-2">AI Analysis</h2>
            <p className="text-cyan-400 mb-4">Difficulty: {difficulty} (Depth: {['EASY', 'MEDIUM', 'HARD', 'EXPERT'].indexOf(difficulty) * 2 + 2})</p>
            {!ai_decision_log.length && (
                <p className={gameState.ai_thinking ? 'text-orange-400' : 'text-gray-400'}>
                    {gameState.ai_thinking ? 'Analyzing moves...' : 'Waiting for AI move...'}
                </p>
            )}
            {ai_decision_log.length > 0 && (
                <div>
                    <div className="flex text-white font-bold">
                        <span className="w-24">Move</span>
                        <span className="w-24">Score</span>
                        <span>Score Bar</span>
                    </div>
                    {ai_decision_log.slice(0, 12).map(([score, move], i) => (
                        <div key={i} className={`flex items-center p-2 rounded ${i === 0 ? 'bg-yellow-600' : 'bg-gray-700'} mt-2`}>
                            <span className="w-24 text-white">{`${i + 1}. ${String.fromCharCode(65 + move[1])}${move[0] + 1}`}</span>
                            <span className="w-24 text-white">{score.toFixed(1)}</span>
                            <div className="flex-1 bg-gray-900 h-3 rounded">
                                <div
                                    className={`h-3 rounded ${score > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                                    style={{
                                        width: `${Math.abs(score) / maxScore * 50}%`,
                                        marginLeft: score > 0 ? '50%' : `${50 - Math.abs(score) / maxScore * 50}%`
                                    }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AIDebugPanel;