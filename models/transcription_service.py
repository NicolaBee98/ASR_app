"""Transcription service for ASR processing."""

import threading
import time
import numpy as np
from whisper_streaming.whisper_online import set_logging, asr_factory
from utils.logging_setup import logger
from utils.config import ASR_CONFIG, ASRArgs, LOG_FILE_PATH


class TranscriptionService:
    """Manages transcription using ASR services."""

    def __init__(
        self, performance_monitor=None, transcript_callback=None, status_callback=None
    ):
        """
        Initialize the transcription service.

        Args:
            performance_monitor: Performance monitoring instance
            transcript_callback: Callback for transcript updates
        """
        self.performance_monitor = performance_monitor
        self.transcript_callback = transcript_callback
        self.status_callback = status_callback or (lambda *args, **kwargs: None)
        self.processing_thread = None
        self.processing = False

        # Initialize ASR
        self.args = self._create_asr_args()
        self.asr, self.online = self._initialize_asr()

        # Determine minimum chunk size
        if self.args.vac:
            self.min_chunk = self.args.vac_chunk_size
        else:
            self.min_chunk = self.args.min_chunk_size

        logger.debug("TranscriptionService initialized")

    def _create_asr_args(self):
        """
        Create ASR arguments object.

        Returns:
            WhisperArgs object with ASR configuration
        """
        args = ASRArgs(ASR_CONFIG)

        # Set up logging for ASR
        # set_logging(args, logger)

        return args

    def _initialize_asr(self):
        """
        Initialize the ASR engine.

        Returns:
            Tuple of (asr, online) objects
        """
        try:
            # Create a logfile for ASR
            logfile = open(LOG_FILE_PATH, "a", buffering=1)

            # Initialize ASR
            asr, online = asr_factory(self.args, logfile=logfile)
            logger.info(f"ASR engine initialized with backend: {self.args.backend}")
            return asr, online

        except Exception as e:
            logger.error(f"Error initializing ASR engine: {str(e)}")
            raise

    def set_language(self, language_code):
        """
        Change the ASR language.

        Args:
            language_code: Language code (e.g., 'en', 'es')

        Returns:
            bool: Whether the language was changed successfully
        """
        try:
            # Update language in args
            self.args.lan = language_code

            # Reinitialize ASR
            self.asr, self.online = self._initialize_asr()

            logger.info(f"ASR language changed to: {language_code}")
            return True

        except Exception as e:
            logger.error(f"Error changing ASR language: {str(e)}")
            return False

    def start_processing(self, audio_processor):
        """
        Start processing audio for transcription.

        Args:
            audio_processor: AudioProcessor instance to get audio chunks from

        Returns:
            bool: Whether processing was started successfully
        """
        if self.processing:
            logger.warning("Transcription processing already running")
            return False

        self.processing = True

        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_audio_thread, args=(audio_processor,)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()

        logger.info("Transcription processing started")
        return True

    def stop_processing(self):
        """Stop audio processing."""
        if not self.processing:
            return False

        self.processing = False

        # Wait for thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)

        logger.info("Transcription processing stopped")
        return True

    def _process_audio_thread(self, audio_processor):
        """
        Background thread for processing audio.

        Args:
            audio_processor: AudioProcessor instance to get audio chunks from
        """
        while self.processing:
            try:
                # Get audio chunk from processor
                data = audio_processor.get_next_audio_chunk()

                if data:
                    # Convert bytes to numpy array
                    audio_array = np.frombuffer(data, dtype=np.int16)

                    # Process with ASR
                    start_time = time.time()

                    # Insert audio chunk
                    self.online.insert_audio_chunk(audio_array)

                    # Process audio
                    result = self.online.process_iter()

                    # Calculate processing time
                    processing_time = time.time() - start_time

                    # Update performance monitor
                    if self.performance_monitor:
                        self.performance_monitor.record_api_call(processing_time)

                    # If we have a transcript, send it to callback
                    if result[0] is not None and self.transcript_callback:
                        transcript = result[2]
                        self.transcript_callback(transcript)

                        if self.performance_monitor:
                            self.performance_monitor.record_ui_update()

                        logger.debug(f"Transcript: {transcript}")

            except Exception as e:
                logger.error(f"Error in transcription processing: {str(e)}")
                time.sleep(0.1)  # Prevent tight loop on error

    def process_audio_chunk(self, data):
        """
        Process a single audio chunk.
        Args:
            data: Raw audio data bytes
        Returns:
            Tuple of (is_final, stability, text) or None if no result
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(data, dtype=np.int16)
            logger.debug(
                f"Process audio chunk - audio chunk of size {audio_array.size}"
            )

            # Insert audio chunk
            self.online.insert_audio_chunk(audio_array)

            # Process audio
            result = self.online.process_iter()

            # Update performance monitor if available
            if self.performance_monitor:
                self.performance_monitor.record_api_call(time.time())

            return result
        except Exception as e:
            logger.error(f"Error processing audio chunk: {str(e)}")
            return None

    # TODO: Implement file processing for full transcription
    def process_file(self, file_path, progress_callback=None):
        """
        Process an entire audio file for transcription.

        Args:
            file_path: Path to the audio file
            progress_callback: Callback for progress updates

        Returns:
            str: Full transcript
        """
        pass
