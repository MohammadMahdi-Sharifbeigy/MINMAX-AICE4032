// Copied from App.jsx
const PLAYER_BLACK = 1;
const PLAYER_WHITE = -1;
const EMPTY = 0;
const DIRECTIONS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];

function createInitialBoard() {
  const board = Array(8).fill().map(() => Array(8).fill(EMPTY));
  board[3][3] = board[4][4] = PLAYER_WHITE;
  board[3][4] = board[4][3] = PLAYER_BLACK;
  return board;
}

const isOnBoard = (r, c) => r >= 0 && r < 8 && c >= 0 && c < 8;

const getValidMoves = (board, player) => {
  const moves = {};
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if (board[r][c] === EMPTY) {
        const piecesToFlip = getPiecesToFlip(board, r, c, player);
        if (piecesToFlip.length > 0) moves[`${r},${c}`] = piecesToFlip;
      }
    }
  }
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
  return piecesToFlip;
};

const dynamicEvaluateBoard = (board, player, totalPieces) => {
  const opponent = -player;
  const pieceWeight = totalPieces < 20 ? 1 : totalPieces < 52 ? 5 : 20;
  const mobilityWeight = totalPieces < 20 ? 15 : totalPieces < 52 ? 10 : 5;
  const cornerWeight = totalPieces < 20 ? 100 : totalPieces < 52 ? 100 : 120;
  const stabilityWeight = totalPieces < 20 ? 80 : totalPieces < 52 ? 100 : 120;

  let score = 0;
  const myPieces = board.reduce((sum, row) => sum + row.filter(cell => cell === player).length, 0);
  const oppPieces = board.reduce((sum, row) => sum + row.filter(cell => cell === opponent).length, 0);
  score += pieceWeight * (myPieces - oppPieces);

  const myMoves = Object.keys(getValidMoves(board, player)).length;
  const oppMoves = Object.keys(getValidMoves(board, opponent)).length;
  if (myMoves + oppMoves > 0) score += mobilityWeight * (myMoves - oppMoves);

  const corners = [[0,0], [0,7], [7,0], [7,7]];
  let myCorners = 0, oppCorners = 0;
  corners.forEach(([r, c]) => {
    if (board[r][c] === player) myCorners++;
    else if (board[r][c] === opponent) oppCorners++;
  });
  score += cornerWeight * (myCorners - oppCorners);

  corners.forEach(([r, c]) => {
    if (board[r][c] === EMPTY) {
      [[0,1], [1,0], [1,1]].forEach(([dr, dc]) => {
        if (isOnBoard(r+dr, c+dc) && board[r+dr][c+dc] === player) score -= 15;
        if (isOnBoard(r-dr, c+dc) && board[r-dr][c+dc] === player) score -= 15;
        if (isOnBoard(r+dr, c-dc) && board[r+dr][c-dc] === player) score -= 15;
      });
    }
  });

  const myStable = countStablePieces(board, player);
  const oppStable = countStablePieces(board, opponent);
  score += stabilityWeight * (myStable - oppStable);

  return score;
};

const countStablePieces = (board, player) => {
  let stableCount = 0;
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if (board[r][c] === player) {
        let isStable = true;
        for (const [dr, dc] of [[1,0], [1,1], [0,1], [-1,1]]) {
          let side1Secure = false;
          let currR = r + dr, currC = c + dc;
          while (isOnBoard(currR, currC)) {
            if (board[currR][currC] !== player) { side1Secure = true; break; }
            currR += dr; currC += dc;
          }
          if (!isOnBoard(currR, currC)) side1Secure = true;

          let side2Secure = false;
          currR = r - dr; currC = c - dc;
          while (isOnBoard(currR, currC)) {
            if (board[currR][currC] !== player) { side2Secure = true; break; }
            currR -= dr; currC -= dc;
          }
          if (!isOnBoard(currR, currC)) side2Secure = true;

          if (!side1Secure || !side2Secure) { isStable = false; break; }
        }
        if (isStable) stableCount++;
      }
    }
  }
  return stableCount;
};

const minimaxAlphaBeta = (board, depth, alpha, beta, maximizingPlayer, aiPlayer, totalPieces) => {
  if (depth === 0) return [dynamicEvaluateBoard(board, aiPlayer, totalPieces), null, []];
  const validMoves = getValidMoves(board, aiPlayer);
  if (Object.keys(validMoves).length === 0) {
    const newBoard = board.map(row => [...row]);
    const nextValidMoves = getValidMoves(newBoard, -aiPlayer);
    if (Object.keys(nextValidMoves).length === 0) {
      return [dynamicEvaluateBoard(newBoard, aiPlayer, totalPieces), null, []];
    }
    return minimaxAlphaBeta(newBoard, depth - 1, alpha, beta, !maximizingPlayer, aiPlayer, totalPieces);
  }

  const evaluatedMoves = [];
  let bestMove = Object.keys(validMoves)[0]?.split(',').map(Number);
  if (maximizingPlayer) {
    let maxEval = -Infinity;
    for (const moveStr in validMoves) {
      const [r, c] = moveStr.split(',').map(Number);
      const newBoard = board.map(row => [...row]);
      newBoard[r][c] = aiPlayer;
      validMoves[moveStr].forEach(([fr, fc]) => newBoard[fr][fc] = aiPlayer);
      const [evaluation] = minimaxAlphaBeta(newBoard, depth - 1, alpha, beta, false, aiPlayer, totalPieces + 1);
      evaluatedMoves.push([evaluation, [r, c]]);
      if (evaluation > maxEval) {
        maxEval = evaluation;
        bestMove = [r, c];
      }
      alpha = Math.max(alpha, evaluation);
      if (beta <= alpha) break;
    }
    evaluatedMoves.sort((a, b) => b[0] - a[0]);
    return [maxEval, bestMove, evaluatedMoves];
  } else {
    let minEval = Infinity;
    for (const moveStr in validMoves) {
      const [r, c] = moveStr.split(',').map(Number);
      const newBoard = board.map(row => [...row]);
      newBoard[r][c] = -aiPlayer;
      validMoves[moveStr].forEach(([fr, fc]) => newBoard[fr][fc] = -aiPlayer);
      const [evaluation] = minimaxAlphaBeta(newBoard, depth - 1, alpha, beta, true, aiPlayer, totalPieces + 1);
      evaluatedMoves.push([evaluation, [r, c]]);
      if (evaluation < minEval) {
        minEval = evaluation;
        bestMove = [r, c];
      }
      beta = Math.min(beta, evaluation);
      if (beta <= alpha) break;
    }
    evaluatedMoves.sort((a, b) => a[0] - b[0]);
    return [minEval, bestMove, evaluatedMoves];
  }
};

self.onmessage = (e) => {
  const { board, depth, aiPlayer, totalPieces } = e.data;
  const [score, move, log] = minimaxAlphaBeta(board, depth, -Infinity, Infinity, true, aiPlayer, totalPieces);
  self.postMessage({ score, move, log });
};