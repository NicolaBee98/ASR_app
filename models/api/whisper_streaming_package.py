from whisper_streaming.whisper_online import asr_factory
from utils.config import LOG_FILE_PATH, ASRArgs
from utils.logging_setup import logger
from .api import BaseAPI
import numpy as np


class WhisperStreamingPackage(BaseAPI):
    def __init__(self, args):
        try:
            # Create a logfile for ASR
            logfile = open(LOG_FILE_PATH["whisper_streaming"], "a", buffering=1)

            # Initialize ASR
            self.args = ASRArgs(args)
            self.asr, self.online = asr_factory(self.args, logfile=logfile)
            self.requires_separate_processing = False
            logger.info(f"ASR engine initialized with backend: {self.args.backend}")

        except Exception as e:
            logger.error(f"Error initializing ASR engine: {str(e)}")
            raise e

    def insert_audio_chunk(self, chunk: np.ndarray):
        self.online.insert_audio_chunk(chunk)

    def process_audio(self):
        return self.online.process_iter()

    def set_language(self, language_code):
        """Set the language for the ASR engine."""
        try:
            self.args.lan = language_code
            self.asr, self.online = asr_factory(self.args)
            logger.info(f"ASR language changed to: {language_code}")
            return True
        except Exception as e:
            logger.error(f"Unsupported language code: {language_code}")
            raise ValueError(
                f"Unsupported language code: {language_code}, error: {str(e)}"
            )
