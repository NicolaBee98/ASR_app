import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# import logging
import customtkinter as ctk
from utils.logging_setup import setup_logging
from utils.config import (
    UI_CONFIG,
    AUDIO_CONFIG,
    DEFAULT_RECORDING_PATH,
    LOG_FILE_PATH,
    ASR_CONFIG,
    LANGUAGES,
    COLORS,
)
from models.app_state import StateManager
from models.audio_processor import AudioProcessor
from models.transcription_service import TranscriptionService
from views.main_window import MainWindow
from controllers.app_controller import AppController
from utils.performance_monitor import PerformanceMonitor
from utils.event_emitter import EventEmitter


def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Audio Recorder application")

    # Load configuration
    root = ctk.CTk()

    # Create models
    events = EventEmitter()
    state_manager = StateManager()
    audio_processor = AudioProcessor(state_manager, events=events)
    transcription_service = TranscriptionService()

    # Create UI
    main_window = MainWindow(root)  # audio_processor, transcription_service)

    # Create performance monitor
    # perf_monitor = PerformanceMonitor(main_window.performance_frame)

    # Create controller
    controller = AppController(
        main_window, audio_processor, transcription_service, events
    )
    # main_window.initialize_panels(controller)

    # Setup clean exit
    def on_closing():
        logger.info("Application closing")
        if audio_processor.state_manager.is_recording():
            audio_processor.stop_recording()
        if audio_processor.state_manager.is_playing():
            audio_processor.stop_playback()
        if audio_processor.state_manager.is_simulating():
            audio_processor.stop_simulation()
        audio_processor.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start application
    logger.info("Starting main loop")
    root.mainloop()


if __name__ == "__main__":
    main()
