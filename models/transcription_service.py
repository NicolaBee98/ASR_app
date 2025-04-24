"""Transcription service for ASR processing."""

import threading
import time
import numpy as np
import queue
from whisper_streaming.whisper_online import asr_factory
from utils.logging_setup import logger
from utils.config import ASR_CONFIG, ASRArgs, LOG_FILE_PATH
from .api.api_backend_factory import api_backend_factory


class TranscriptionService:
    """Manages transcription using ASR services."""

    def __init__(self, events=None, status_callback=None):
        """
        Initialize the transcription service.

        Args:
            performance_monitor: Performance monitoring instance
            events: Callback for transcript updates
        """
        self.events = events
        self.status_callback = status_callback or (lambda *args, **kwargs: None)
        self.processing_thread = None
        self.processing = False

        # Initialize performance monitor
        self.performance_metrics = {
            "NO METRICS INITIALIZED": 0,
        }

        # Initialize ASR API
        self.api = api_backend_factory()
        self.args = self._create_asr_args()
        # self.asr, self.online = self._initialize_asr()

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

    # def _initialize_asr(self):
    #     """
    #     Initialize the ASR engine with whisper_online package

    #     Returns:
    #         Tuple of (asr, online) objects
    #     """
    #     try:
    #         # Create a logfile for ASR
    #         logfile = open(LOG_FILE_PATH["whisper_streaming"], "a", buffering=1)

    #         # Initialize ASR
    #         asr, online = asr_factory(self.args, logfile=logfile)
    #         logger.info(f"ASR engine initialized with backend: {self.args.backend}")
    #         return asr, online

    #     except Exception as e:
    #         logger.error(f"Error initializing ASR engine: {str(e)}")
    #         raise e

    def set_language(self, language_code):
        """
        Change the ASR language.

        Args:
            language_code: Language code (e.g., 'en', 'es')

        Returns:
            bool: Whether the language was changed successfully
        """
        self.api.set_language(language_code)
        # try:
        #     # Update language in args
        #     self.args.lan = language_code

        #     # Reinitialize ASR
        #     self.asr, self.online = self._initialize_asr()

        #     logger.info(f"ASR language changed to: {language_code}")
        #     return True

        # except Exception as e:
        #     logger.error(f"Error changing ASR language: {str(e)}")
        #     return False

    def start_transcription(self, audio_processor):
        if not audio_processor.state_manager.is_recording():
            return False

        # Start recording thread
        self.transcription_thread = threading.Thread(
            target=self._transcription_thread, args=(audio_processor,)
        )
        self.transcription_thread.daemon = True
        self.transcription_thread.start()

    def get_performance_metrics(self):
        return self.performance_metrics

    def update_performance_metrics(self, metric_name, value, update_ui=False):
        """
        Update a single performance metric.
        Args:
            metric_name: Name of the metric to update
            value: Value to update or add
            update_ui: Whether to emit the metrics update to UI
        """
        try:
            if metric_name.endswith("_times"):
                if metric_name not in self.performance_metrics:
                    self.performance_metrics[metric_name] = []
                self.performance_metrics[metric_name].append(value)

                # Also calculate and store average
                avg_metric_name = f"avg_{metric_name[:-1]}"  # _times -> _time
                self.performance_metrics[avg_metric_name] = sum(
                    self.performance_metrics[metric_name]
                ) / len(self.performance_metrics[metric_name])

            elif metric_name.endswith("_time"):
                # For time metrics, store current value
                self.performance_metrics[metric_name] = value
            elif metric_name.startswith("total_") or metric_name.endswith("_count"):
                # For counters, add to existing value
                if metric_name not in self.performance_metrics:
                    self.performance_metrics[metric_name] = 0
                self.performance_metrics[metric_name] += value
            else:
                # For other metrics, just update
                self.performance_metrics[metric_name] = value

            # For list-based metrics
            self.performance_metrics.pop("NO METRICS INITIALIZED", None)

            if update_ui:
                self.events.emit("update_performance_metrics", self.performance_metrics)
        except Exception as e:
            logger.error(
                f"Error in performance_metrics while computing {metric_name}: {str(e)}"
            )
            logger.error(f"Performance metrics: {self.performance_metrics.items()}")

    def track_processing_time(self, operation_name, func, *args, **kwargs):
        """
        Track processing time for an operation.
        Args:
            operation_name: Name of the operation being tracked
            func: Function to call
            *args, **kwargs: Arguments to pass to the function
        Returns:
            Result of the function call
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        processing_time = time.time() - start_time

        metric_name = f"{operation_name}_time"
        self.update_performance_metrics(metric_name, processing_time)

        # Also track total time for this operation
        total_metric_name = f"total_{operation_name}_time"
        self.update_performance_metrics(total_metric_name, processing_time)

        # Track call count
        call_metric_name = f"{operation_name}_calls"
        self.update_performance_metrics(call_metric_name, 1)

        return result, processing_time

    def process_audio_chunk(self, data):
        """
        Process a single audio chunk.
        Args:
            data: Raw audio data bytes
        Returns:
            Tuple of (is_final, stability, text) or None if no result
        """
        try:
            # Track chunk size
            chunk_size = len(data)
            self.update_performance_metrics("chunk_size", chunk_size)
            self.update_performance_metrics("total_processed_bytes", chunk_size)

            # Convert bytes to numpy array
            def convert_to_array():
                return np.frombuffer(data, dtype=np.int16)

            audio_array, _ = self.track_processing_time(
                "array_conversion", convert_to_array
            )

            # Insert audio chunk
            def insert_audio_chunk():
                self.api.insert_audio_chunk(audio_array)

            _, api_time = self.track_processing_time("api_call", insert_audio_chunk)

            result, process_time = self.track_processing_time(
                "processing", self.api.process_audio
            )

            if result[0] is not None:
                self.update_performance_metrics("frames_processed", 1)
                self.update_performance_metrics("ui_updates", 1)

                # Track time between UI updates
                now = time.time()
                if "last_update_time" in self.performance_metrics:
                    time_since_last_update = (
                        now - self.performance_metrics["last_update_time"]
                    )
                    self.update_performance_metrics(
                        "time_between_updates", time_since_last_update
                    )
                self.update_performance_metrics("last_update_time", now)

                # Track transcript length
                if result[2]:
                    self.update_performance_metrics("transcript_length", len(result[2]))

            # Total time for this chunk (full processing pipeline)
            total_chunk_time = api_time + process_time
            self.update_performance_metrics("total_chunk_time", total_chunk_time)

            return result
        except Exception as e:
            self.update_performance_metrics("errors", 1)
            self.events.emit(
                "error", f"Processing error in process_audio_chunk: {str(e)}"
            )
            return None

    def _transcription_thread(self, audio_processor):
        thread_start_time = time.time()
        self.update_performance_metrics("thread_start_time", thread_start_time)

        while audio_processor.state_manager.is_recording():
            try:
                queue_start_wait = time.time()
                data = audio_processor.audio_queue.get(timeout=0.5)
                queue_wait_time = time.time() - queue_start_wait
                # Track queue wait times
                self.update_performance_metrics("queue_wait_times", queue_wait_time)
                self.update_performance_metrics("last_queue_wait", queue_wait_time)

                # Process audio with transcription service
                chunk_start = time.time()
                result = self.process_audio_chunk(data)
                chunk_process_time = time.time() - chunk_start
                self.update_performance_metrics(
                    "last_chunk_process_time", chunk_process_time, update_ui=True
                )

                if result and result[0] is not None:
                    transcript = result[2]
                    self.events.emit("update_transcription", transcript)

                logger.debug(f"Chunk processed in {chunk_process_time:.4f}s")

            except queue.Empty:
                self.update_performance_metrics("queue_empty_count", 1)
                pass
            except Exception as e:
                error_message = str(e)
                self.update_performance_metrics("errors", 1)
                self.events.emit(
                    "error",
                    f"Processing error in _transcription_thread: {error_message}",
                )

        # Thread ending metrics
        thread_running_time = time.time() - thread_start_time
        self.update_performance_metrics(
            "thread_running_time", thread_running_time, update_ui=True
        )
