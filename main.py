#!/usr/bin/env python3
"""Entry point for the Audio Transcription API server."""

import sys
from src.logger import logger


def main() -> int:
    """Main entry point for the application."""
    logger.info("=" * 50)
    logger.info("Audio Transcription API Starting")
    logger.info("=" * 50)

    try:
        from src.server.main import run_server

        run_server(host="127.0.0.1", port=8000, reload=True)

        logger.info("Server stopped")
        return 0

    except ImportError as e:
        logger.exception("Failed to import required modules")
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        logger.exception("Unhandled exception in main")
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
