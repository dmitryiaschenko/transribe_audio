# Audio Transcription App

A modern GUI application for transcribing audio files using Google's Gemini AI. Supports multiple languages and provides specialized analysis for interviews and business meetings.

## Features

- **Drag-and-drop** file selection (with click-to-browse fallback)
- **Multiple languages**: English, Russian, Polish
- **Conversation types**:
  - *Interview*: Includes assessment, strengths, weaknesses, recommendations
  - *Business Meeting*: Includes summary, action items, next steps
- **Dark theme** modern UI built with CustomTkinter
- **Token usage and cost tracking**
- **Copy to clipboard** functionality
- **Comprehensive logging** for debugging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd transcription_app
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API key:
```bash
# Create a .env file in the project root
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

## Usage

### GUI Application
```bash
python main.py
```

### CLI Version
```bash
python transcribe.py
```

## Project Structure

```
transcription_app/
├── main.py                 # GUI entry point
├── transcribe.py           # CLI version
├── requirements.txt
├── .env                    # API key (create this)
├── logs/                   # Application logs
├── src/
│   ├── config.py           # Configuration and constants
│   ├── logger.py           # Logging setup
│   ├── api/
│   │   └── transcription_service.py
│   └── gui/
│       ├── app.py          # Main window
│       └── components.py   # UI components
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

Application logs are stored in the `logs/` directory with daily rotation:
- File: `logs/app_YYYYMMDD.log`
- Console: INFO level and above
- File: DEBUG level (detailed)

## Requirements

- Python 3.10+
- Google Gemini API key

## License

MIT
