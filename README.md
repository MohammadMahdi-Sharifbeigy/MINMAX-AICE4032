# Othello Webapp

A web-based Othello game with PvP, PvB, and BvB modes, powered by Flask and React.

## Prerequisites
- Python 3.8+
- Node.js 14+
- npm

## Setup Instructions

1. **Backend Setup**
   - Navigate to `backend/`
   - Create a virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # On Windows: venv\Scripts\activate
     ```
   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Start the Flask server:
     ```bash
     python app.py
     ```

2. **Frontend Setup**
   - Navigate to `frontend/`
   - Install dependencies:
     ```bash
     npm install
     ```
   - Start the development server:
     ```bash
     npm start
     ```
   - Open `http://localhost:3000` in your browser.

3. **Audio Files**
   - Place `menu_music.mp3`, `game_music.mp3`, `place_sound.wav`, and `flip_sound.mp3` in `frontend/src/assets/`.
   - These are optional; the game will run without them but won't play sounds.

## Notes
- The game runs locally at `http://localhost:3000`.
- The backend uses Flask-SocketIO for real-time communication.
- The frontend uses React with Tailwind CSS for styling.
- Ensure the backend is running before starting the frontend.
