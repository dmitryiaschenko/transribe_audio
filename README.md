# Audio Transcription App

A web application for transcribing audio files using Google's Gemini AI. Supports multiple languages and provides specialized analysis for interviews and business meetings.

## Features

- **Drag-and-drop** file upload (with click-to-browse fallback)
- **Real-time progress** updates via WebSocket
- **Multiple languages**: English, Russian, Polish
- **Conversation types**:
  - *Interview*: Includes assessment, strengths, weaknesses, recommendations
  - *Business Meeting*: Includes summary, action items, next steps
- **Dark theme** UI built with React and Tailwind CSS
- **Token usage and cost tracking**
- **Copy to clipboard** functionality
- **Comprehensive logging** for debugging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd transcription_app
```

2. Create a virtual environment and install backend dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
cd ..
```

4. Set up your API key:
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

## Usage

### Web Application

Start the backend server:
```bash
python main.py
```

In a separate terminal, start the frontend dev server:
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

### CLI Version
```bash
python transcribe.py
```

## Project Structure

```
transcription_app/
├── main.py                 # Server entry point
├── transcribe.py           # Standalone CLI version
├── requirements.txt
├── .env.example            # Environment variables template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/client.ts
│   │   ├── components/
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   └── TranscriptionResult.tsx
│   │   └── hooks/useWebSocket.ts
│   ├── package.json
│   └── vite.config.ts
├── src/
│   ├── config.py           # Configuration and constants
│   ├── logger.py           # Logging setup
│   ├── api/
│   │   └── transcription_service.py
│   └── server/
│       ├── main.py         # FastAPI application
│       ├── routes.py       # API endpoints
│       ├── jobs.py         # Job management
│       └── websocket.py    # WebSocket handler
└── tests/
    ├── conftest.py
    ├── test_config.py
    └── test_transcription_service.py
```

## Running Tests

```bash
python -m pytest tests/ -v
```

With coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Supported Audio Formats

- `.m4a`
- `.mp3`
- `.wav`
- `.aac`

## Logs

Application logs are stored in the `logs/` directory:
- File: `logs/app_YYYYMMDD.log` (DEBUG level)
- Console: INFO level and above

## Requirements

- Python 3.10+
- Node.js 18+
- Google Gemini API key

## License

MIT
