from RealtimeSTT import AudioToTextRecorder
from utils.config import ASRArgs  # LOG_FILE_PATH
from utils.logging_setup import setup_logging, logger
from .api import BaseAPI
import numpy as np
import threading
# mport logging


class RealtimeSTT(BaseAPI):
    def __init__(self, args):
        try:
            # Create a logfile for ASR
            setup_logging(logger_name="realtimestt")

            # Initialize ASR
            self.args = ASRArgs(args)
            self.recorder = AudioToTextRecorder(
                use_microphone=False,
                spinner=False,
            )
            self.requires_separate_processing = True
            logger.info("ASR engine initialized using RealtimeSTT backend.")

            # create stop event for the thread
            self.stop_event = threading.Event()

        except Exception as e:
            logger.error(f"Error initializing ASR engine: {str(e)}")
            raise e

    def insert_audio_chunk(self, chunk: np.ndarray):
        self.recorder.feed_audio(chunk)

    def process_audio(self):
        return self.recorder.text()

    def set_language(self, language_code):
        """Set the language for the ASR engine."""
        try:
            # self.args.lan = language_code
            self.recorder.language = language_code
            logger.info(f"ASR language changed to: {language_code}")
            return True
        except Exception as e:
            logger.error(f"Unsupported language code: {language_code}")
            raise ValueError(
                f"Unsupported language code: {language_code}, error: {str(e)}"
            )

    def start(self):
        """Start the ASR process."""
        try:
            self.recorder = AudioToTextRecorder(
                use_microphone=False,
                spinner=False,
            )
            logger.info("ASR process reset and started.")
        except Exception as e:
            logger.error(f"Error starting ASR process: {str(e)}")
            raise e

    def stop(self):
        """Abort the ASR process."""
        try:
            self.recorder.shutdown()
            self.stop_event.set()  # Set the stop event to signal the thread to stop
            # self.recorder.abort()
            logger.info("ASR process stopped.")
        except Exception as e:
            logger.error(f"Error aborting ASR process: {str(e)}")
            raise e
