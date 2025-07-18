import React from 'react';

const PLAYER_BLACK = 1;
const PLAYER_WHITE = -1;
const EMPTY = 0;
const DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
const DIFFICULTIES = { EASY: 2, MEDIUM: 4, HARD: 6, EXPERT: 8 };

const worker = new Worker(new URL('./aiWorker.js', import.meta.url), { type: 'module' });

function App() {
  function createInitialBoard() {
    const board = Array(8).fill().map(() => Array(8).fill(EMPTY));
    board[3][3] = board[4][4] = PLAYER_WHITE;
    board[3][4] = board[4][3] = PLAYER_BLACK;
    console.log('Initial board created:', board);
    return board;
  }

  const initialBoard = React.useMemo(() => createInitialBoard(), []);
  const [gameState, setGameState] = React.useState('MENU');
  const [board, setBoard] = React.useState(initialBoard);
  const [currentPlayer, setCurrentPlayer] = React.useState(PLAYER_BLACK);
  const [validMoves, setValidMoves] = React.useState({});
  const [aiThinking, setAIThinking] = React.useState(false);
  const [lastMove, setLastMove] = React.useState(null);
  const [gameOver, setGameOver] = React.useState(false);
  const [winner, setWinner] = React.useState(null);
  const [animations, setAnimations] = React.useState([]);
  const [hoverPos, setHoverPos] = React.useState(null);
  const [aiDecisionLog, setAIDecisionLog] = React.useState([]);
  const [gameMode, setGameMode] = React.useState(null);
  const [humanColor, setHumanColor] = React.useState(null);
  const [difficulty, setDifficulty] = React.useState('EASY');

  React.useEffect(() => {
    console.log('useEffect triggered:', { gameState, gameOver, gameMode, currentPlayer });
    if (gameState === 'PLAYING' && !gameOver) {
      console.log('Calculating valid moves for player:', currentPlayer);
      const newValidMoves = getValidMoves(board, currentPlayer);
      console.log('Setting validMoves:', newValidMoves);
      if (JSON.stringify(newValidMoves) !== JSON.stringify(validMoves)) {
        setValidMoves(newValidMoves);
      }
      if (Object.keys(newValidMoves).length === 0) {
        console.log('No valid moves, handling...');
        setTimeout(() => handleNoValidMoves(), 0);
      } else if (isAITurn()) {
        console.log('AI turn detected, scheduling move...');
        setAIThinking(true);
        const timer = setTimeout(() => {
          if (isAITurn()) makeAIMove();
        }, 500);
        return () => clearTimeout(timer);
      }
    }
  }, [board, currentPlayer, gameState, gameOver, gameMode, humanColor, validMoves]);

  const isOnBoard = (r, c) => r >= 0 && r < 8 && c >= 0 && c < 8;

  const getValidMoves = (board, player) => {
    const moves = {};
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        if (board[r][c] === EMPTY) {
          const piecesToFlip = getPiecesToFlip(board, r, c, player);
          if (piecesToFlip.length > 0) {
            moves[`${r},${c}`] = piecesToFlip;
            console.log(`Valid move at [${r},${c}]:`, piecesToFlip);
          }
        }
      }
    }
    console.log('Valid moves for player', player, ':', moves);
    return moves;
  };

  const getPiecesToFlip = (board, r, c, player) => {
    const opponent = -player;
    const piecesToFlip = [];
    for (const [dr, dc] of DIRECTIONS) {
      const line = [];
      let currR = r + dr, currC = c + dc;
      while (isOnBoard(currR, currC) && board[currR][currC] === opponent) {
        line.push([currR, currC]);
        currR += dr;
        currC += dc;
      }
      if (isOnBoard(currR, currC) && board[currR][currC] === player) {
        piecesToFlip.push(...line);
      }
    }
    console.log(`getPiecesToFlip(${r},${c},${player}):`, piecesToFlip);
    return piecesToFlip;
  };

  const placeSound = new Audio('/place_sound.wav');
  const flipSound = new Audio('/flip_sound.mp3');

  const makeMove = (r, c) => {
    if (!validMoves[`${r},${c}`]) {
      console.log('Invalid move attempted:', { r, c, validMoves });
      return false;
    }
    const newBoard = board.map(row => [...row]);
    newBoard[r][c] = currentPlayer;
    placeSound.play().catch(err => console.error('Audio play failed:', err));
    const newAnimations = [];
    validMoves[`${r},${c}`].forEach(([fr, fc], i) => {
      newBoard[fr][fc] = currentPlayer;
      newAnimations.push({
        pos: [fr, fc],
        startTime: Date.now() + i * 50,
        duration: 400,
        fromPlayer: -currentPlayer,
        toPlayer: currentPlayer
      });
      if (i % 2 === 0) flipSound.play().catch(err => console.error('Audio play failed:', err));
    });
    console.log('New board after move:', newBoard);
    setBoard(newBoard);
    setLastMove([r, c]);
    setAnimations(newAnimations);
    switchPlayer();
    return true;
  };

  const switchPlayer = () => {
    const nextPlayer = -currentPlayer;
    const nextValidMoves = getValidMoves(board, nextPlayer);
    console.log('Switching to player:', nextPlayer, 'Valid moves:', nextValidMoves);
    if (Object.keys(nextValidMoves).length === 0) {
      const backValidMoves = getValidMoves(board, currentPlayer);
      if (Object.keys(backValidMoves).length === 0) {
        console.log('Game over: no valid moves for either player');
        setGameOver(true);
        setTimeout(() => determineWinner(), 0);
      } else {
        console.log('No valid moves for next player, staying with current player');
        setCurrentPlayer(currentPlayer);
        setValidMoves(backValidMoves);
      }
    } else {
      setCurrentPlayer(nextPlayer);
      setValidMoves(nextValidMoves);
    }
  };

  const handleNoValidMoves = () => {
    const nextPlayer = -currentPlayer;
    const nextValidMoves = getValidMoves(board, nextPlayer);
    console.log('Handling no valid moves, checking next player:', nextPlayer, 'Valid moves:', nextValidMoves);
    if (Object.keys(nextValidMoves).length === 0) {
      console.log('Game over: no valid moves for either player');
      setGameOver(true);
      setTimeout(() => determineWinner(), 0);
    } else {
      setCurrentPlayer(nextPlayer);
      setValidMoves(nextValidMoves);
    }
  };

  const determineWinner = () => {
    const [blackScore, whiteScore] = getScore();
    if (blackScore > whiteScore) setWinner(PLAYER_BLACK);
    else if (whiteScore > blackScore) setWinner(PLAYER_WHITE);
    else setWinner(EMPTY);
  };

  const getScore = () => {
    let blackScore = 0, whiteScore = 0;
    board.forEach(row => {
      blackScore += row.filter(cell => cell === PLAYER_BLACK).length;
      whiteScore += row.filter(cell => cell === PLAYER_WHITE).length;
    });
    return [blackScore, whiteScore];
  };

  const makeAIMove = () => {
    if (!isAITurn()) {
      console.log('makeAIMove aborted: not AI turn');
      setAIThinking(false);
      return;
    }
    console.log('Starting AI move calculation...');
    setAIThinking(true);
    const totalPieces = board.reduce((sum, row) => sum + row.filter(cell => cell !== EMPTY).length, 0);
    worker.postMessage({ board, depth: DIFFICULTIES[difficulty], aiPlayer: currentPlayer, totalPieces });
    worker.onmessage = (e) => {
      console.log('AI move received:', e.data);
      setAIDecisionLog(e.data.log);
      if (e.data.move) makeMove(e.data.move[0], e.data.move[1]);
      setAIThinking(false);
    };
    worker.onerror = (e) => {
      console.error('Worker error:', e);
      setAIThinking(false);
    };
  };

  const isAITurn = () => {
    const result = gameMode === 'BvB' || (gameMode === 'PvB' && currentPlayer !== humanColor);
    console.log('isAITurn:', { gameMode, currentPlayer, humanColor, result });
    return result;
  };

  const handleSquareClick = (r, c) => {
    console.log('Square clicked:', { r, c, gameState, gameOver, aiThinking, gameMode, currentPlayer, humanColor, validMove: validMoves[`${r},${c}`] });
    if (gameState !== 'PLAYING' || gameOver || aiThinking || (gameMode === 'PvB' && currentPlayer !== humanColor) || gameMode === 'BvB') {
      console.log('Click blocked by conditions:', { gameState, gameOver, aiThinking, isPvBBlocked: gameMode === 'PvB' && currentPlayer !== humanColor, isBvB: gameMode === 'BvB' });
      return;
    }
    if (makeMove(r, c)) {
      console.log('Move made successfully at:', { r, c });
      if (gameMode === 'PvB' && !gameOver && currentPlayer !== humanColor) {
        console.log('Scheduling AI move');
        setAIThinking(true);
        setTimeout(() => makeAIMove(), 500);
      }
    } else {
      console.log('Move failed: invalid move at:', { r, c });
    }
  };

  const startGame = (mode, color) => {
    console.log('startGame called:', { mode, color });
    setGameMode(mode);
    setHumanColor(color);
    const newBoard = createInitialBoard();
    console.log('startGame board:', newBoard);
    setBoard(newBoard);
    setCurrentPlayer(PLAYER_BLACK);
    setValidMoves({});
    setAIThinking(false);
    setLastMove(null);
    setGameOver(false);
    setWinner(null);
    setAnimations([]);
    setHoverPos(null);
    setAIDecisionLog([]);
    setGameState('PLAYING');
  };

  const resetGame = () => {
    console.log('resetGame called');
    startGame(gameMode, humanColor);
  };

  const GameBoard = () => {
    React.useEffect(() => {
      const interval = setInterval(() => {
        const now = Date.now();
        setAnimations(prevAnimations => prevAnimations.filter(anim => now - anim.startTime < anim.duration));
      }, 100);
      return () => clearInterval(interval);
    }, []);

    return (
      <div className="relative bg-amber-900 p-2 rounded-xl shadow-lg" style={{ width: 'min(90vw, 560px)', aspectRatio: '1/1' }}>
        <div className="grid grid-cols-8 gap-0 bg-green-800">
          {board.map((row, r) =>
            row.map((cell, c) => {
              const isValidMove = validMoves[`${r},${c}`];
              const isLastMove = lastMove && lastMove[0] === r && lastMove[1] === c;
              const anim = animations.find(a => a.pos[0] === r && a.pos[1] === c);
              const isAnimated = !!anim;
              const now = Date.now();
              const progress = anim ? (now - anim.startTime) / anim.duration : 0;
              const pieceClass = anim
                ? progress < 0.5
                  ? anim.fromPlayer === PLAYER_BLACK ? 'piece-black' : 'piece-white'
                  : anim.toPlayer === PLAYER_BLACK ? 'flip-white-to-black' : 'flip-black-to-white'
                : cell === PLAYER_BLACK ? 'piece-black' : cell === PLAYER_WHITE ? 'piece-white' : '';

              return (
                <div
                  key={`${r}-${c}`}
                  className={`relative aspect-square border border-gray-700 ${(r + c) % 2 === 0 ? 'bg-green-600' : 'bg-green-700'} ${isLastMove ? 'ring-4 ring-yellow-400' : ''}`}
                  onClick={() => handleSquareClick(r, c)}
                  onMouseEnter={() => setHoverPos([r, c])}
                  onMouseLeave={() => setHoverPos(null)}
                >
                  {cell !== EMPTY && !isAnimated && (
                    <div className={`absolute inset-2 rounded-full ${pieceClass}`} />
                  )}
                  {isAnimated && (
                    <div className={`absolute inset-2 rounded-full ${pieceClass}`} />
                  )}
                  {isValidMove && hoverPos && hoverPos[0] === r && hoverPos[1] === c && (
                    <div className={`absolute inset-2 rounded-full opacity-40 ${currentPlayer === PLAYER_BLACK ? 'bg-black' : 'bg-white'}`} />
                  )}
                  {isValidMove && (
                    <div className={`absolute inset-3 rounded-full pulse ${currentPlayer === PLAYER_BLACK ? 'bg-cyan-400' : 'bg-orange-400'}`} />
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  };

  const HUD = () => {
    const [blackScore, whiteScore] = getScore();
    return (
      <div className="flex justify-between items-center bg-gray-800 p-4 rounded-xl shadow-md mb-4" style={{ width: 'min(90vw, 560px)' }}>
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full piece-black mr-2"></div>
          <span className="text-white text-xl">{blackScore}</span>
        </div>
        <div className="text-white text-xl font-semibold bg-blue-600 px-4 py-2 rounded-lg">
          {gameOver ? 'Game Over' : aiThinking ? 'AI Thinking...' : currentPlayer === PLAYER_BLACK ? "Black's Turn" : "White's Turn"}
        </div>
        <div className="flex items-center">
          <span className="text-white text-xl mr-2">{whiteScore}</span>
          <div className="w-8 h-8 rounded-full piece-white"></div>
        </div>
      </div>
    );
  };

  const AIDebugPanel = () => {
    if (gameMode === 'PvP') return null;
    const maxScore = aiDecisionLog.length > 0 ? Math.max(...aiDecisionLog.map(([score]) => Math.abs(score))) : 1;

    return (
      <div className="bg-gray-800 p-4 rounded-xl shadow-md ml-4" style={{ width: 'min(90vw, 450px)', height: 'min(90vw, 560px)' }}>
        <h2 className="text-white text-xl mb-2">AI Analysis</h2>
        <p className="text-cyan-400 mb-4">Difficulty: {difficulty} (Depth: {DIFFICULTIES[difficulty]})</p>
        {aiDecisionLog.length === 0 ? (
          <p className={`text-${aiThinking ? 'orange' : 'gray'}-400`}>{aiThinking ? 'Analyzing moves...' : 'Waiting for AI move...'}</p>
        ) : (
          <div>
            <div className="flex text-white font-semibold mb-2">
              <span className="w-1/3">Move</span>
              <span className="w-1/3">Score</span>
              <span className="w-1/3">Score Bar</span>
            </div>
            {aiDecisionLog.slice(0, 12).map(([score, [r, c]], i) => (
              <div key={i} className={`flex items-center p-2 rounded ${i === 0 ? 'bg-yellow-900' : 'bg-gray-700'} mb-2`}>
                <span className="w-1/3 text-white">{`${i + 1}. ${String.fromCharCode(65 + c)}${r + 1}`}</span>
                <span className="w-1/3 text-white">{score.toFixed(1)}</span>
                <div className="w-1/3 h-3 bg-gray-900 rounded">
                  <div
                    className={`h-full rounded ${score > 0 ? 'bg-green-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.abs(score) / maxScore * 50}%`, marginLeft: score > 0 ? '50%' : `${50 - Math.abs(score) / maxScore * 50}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const Menu = () => {
    const [menuState, setMenuState] = React.useState('main');

    return (
      <div className="flex flex-col items-center bg-gray-900 bg-opacity-80 p-8 rounded-xl shadow-lg">
        <h1 className="text-5xl font-bold text-yellow-400 mb-8 drop-shadow-md">Othello AI</h1>
        {menuState === 'main' ? (
          <>
            <h2 className="text-white text-2xl mb-4">Choose your game mode</h2>
            <button
              className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400 transition"
              onClick={() => startGame('PvP', null)}
            >
              Player vs Player
            </button>
            <button
              className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400 transition"
              onClick={() => setMenuState('choose_color')}
            >
              Player vs Bot
            </button>
            <button
              className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400 transition"
              onClick={() => startGame('BvB', null)}
            >
              Bot vs Bot
            </button>
            <button
              className="bg-red-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-red-400 transition"
              onClick={() => window.close()}
            >
              Quit
            </button>
          </>
        ) : (
          <>
            <h2 className="text-white text-2xl mb-4">Choose your color</h2>
            <button
              className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400 transition"
              onClick={() => startGame('PvB', PLAYER_BLACK)}
            >
              Play as Black
            </button>
            <button
              className="bg-blue-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-blue-400 transition"
              onClick={() => startGame('PvB', PLAYER_WHITE)}
            >
              Play as White
            </button>
            <button
              className="bg-gray-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-gray-400 transition"
              onClick={() => setMenuState('main')}
            >
              Back
            </button>
          </>
        )}
        <div className="mt-4">
          <h3 className="text-white text-xl mb-2">AI Difficulty:</h3>
          <div className="flex space-x-2">
            {Object.keys(DIFFICULTIES).map(d => (
              <button
                key={d}
                className={`px-4 py-2 rounded-lg ${difficulty === d ? 'bg-orange-500 text-white' : 'bg-gray-600 text-white hover:bg-gray-400'}`}
                onClick={() => setDifficulty(d)}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const GameOverScreen = () => {
    const [blackScore, whiteScore] = getScore();
    let winnerText, winnerColor;
    if (winner === PLAYER_BLACK) {
      winnerText = "Black Wins!";
      winnerColor = 'text-yellow-400';
    } else if (winner === PLAYER_WHITE) {
      winnerText = "White Wins!";
      winnerColor = 'text-gray-300';
    } else {
      winnerText = "It's a Tie!";
      winnerColor = 'text-purple-400';
    }

    return (
      <div className="absolute inset-0 bg-black bg-opacity-80 flex flex-col items-center justify-center">
        <h1 className={`text-5xl font-bold ${winnerColor} mb-8 drop-shadow-md`}>{winnerText}</h1>
        <p className="text-white text-2xl mb-8">Final Score: Black {blackScore} - White {whiteScore}</p>
        <button
          className="bg-green-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-green-400 transition"
          onClick={resetGame}
        >
          Play Again
        </button>
        <button
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-400 transition"
          onClick={() => setGameState('MENU')}
        >
          Main Menu
        </button>
      </div>
    );
  };

  const PauseScreen = () => (
    <div className="absolute inset-0 bg-black bg-opacity-80 flex flex-col items-center justify-center">
      <h1 className="text-5xl font-bold text-yellow-400 mb-8 drop-shadow-md">Game Paused</h1>
      <button
        className="bg-green-600 text-white px-6 py-3 rounded-lg mb-4 hover:bg-green-400 transition"
        onClick={() => setGameState('PLAYING')}
      >
        Resume
      </button>
      <button
        className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-400 transition"
        onClick={() => setGameState('MENU')}
      >
        Main Menu
      </button>
    </div>
  );

  return (
    <div className="flex flex-col md:flex-row items-center justify-center p-4">
      {gameState === 'MENU' ? (
        <Menu />
      ) : gameState === 'PLAYING' ? (
        <>
          <div className="flex flex-col items-center">
            <HUD />
            <GameBoard />
          </div>
          <AIDebugPanel />
          {gameOver && <GameOverScreen />}
        </>
      ) : gameState === 'PAUSED' ? (
        <PauseScreen />
      ) : null}
    </div>
  );
}

export default App;