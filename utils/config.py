"""Configuration settings for the audio recorder application."""

# import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="./.env")

# UI Configuration
UI_CONFIG = {
    "appearance_mode": "light",  # Force light mode for better WSLg rendering
    "color_theme": "blue",
    "widget_scaling": 1.2,  # Slightly larger widgets for better visibility
    "window_size": "800x800",
    "window_title": "Audio Recorder",
}

# Audio Configuration
AUDIO_CONFIG = {
    "chunk_size": 1024,
    "format": 16,  # Corresponds to pyaudio.paInt16
    "channels": 1,
    "rate": 16000,
}

# File Paths
DEFAULT_RECORDING_PATH = "recording.wav"
LOG_FILE_PATH = "test.log"

# ASR Configuration that has to be passed to whisper_online.asr_factory
ASR_CONFIG = {
    "start_at": 0,
    "offline": False,
    "comp_unaware": False,
    "min_chunk_size": 5.0,
    "model": "large-v2",
    "model_cache_dir": None,
    "model_dir": None,
    "lan": "auto",  # Default language
    "task": "transcribe",
    "backend": "openai-api",
    "vac": False,
    "vac_chunk_size": 0.04,
    "vad": False,
    "buffer_trimming": "segment",
    "buffer_trimming_sec": 30,
    "log_level": "DEBUG",
}


class ASRArgs:
    """Class to hold arguments for ASR"""

    def __init__(self, args_dict):
        for key, value in args_dict.items():
            setattr(self, key, value)


# Available languages for the dropdown
LANGUAGES = {
    "Auto": "auto",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Russian": "ru",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Arabic": "ar",
    "Hindi": "hi",
}

# UI Colors
COLORS = {
    "background": "#e0e0e0",
    "panel_background": "#d9d9d9",
    "border": "#999999",
    "record_button": {
        "fg_color": "#4682B4",  # Steel Blue
        "hover_color": "#36648B",
        "border_color": "#36648B",
    },
    "stop_button": {
        "fg_color": "#B22222",  # Firebrick
        "hover_color": "#8B0000",
        "border_color": "#8B0000",
    },
    "pause_button": {
        "fg_color": "#CD853F",  # Peru
        "hover_color": "#8B5A2B",
        "border_color": "#8B5A2B",
    },
    "save_button": {
        "fg_color": "#2E8B57",  # Sea Green
        "hover_color": "#1D5B38",
        "border_color": "#1D5B38",
    },
    "simulate_button": {
        "fg_color": "#8A2BE2",  # Blue Violet
        "hover_color": "#5A189A",
        "border_color": "#5A189A",
    },
    "play_button": {
        "fg_color": "#FF6347",  # Tomato
        "hover_color": "#FF4500",
        "border_color": "#FF4500",
    },
    "timer_text": "#0000CD",  # Medium Blue
}
