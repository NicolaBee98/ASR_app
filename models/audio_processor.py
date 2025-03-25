"""Audio recording and processing functionality."""

import threading
import time
import wave
import pyaudio
from pydub import AudioSegment
import tempfile
import numpy as np
import queue
from utils.logging_setup import logger
from utils.config import AUDIO_CONFIG
from models.app_state import AppState


class AudioProcessor:
    """Handles audio recording, playback and processing."""

    def __init__(self, state_manager, events=None, performance_monitor=None):
        """
        Initialize the audio processor.

        Args:
            state_manager: The application state manager
            audio_callback: Callback for processed audio chunks
            performance_monitor: Performance monitoring instance
        """
        self.state_manager = state_manager
        self.events = events or (
            lambda *args, **kwargs: None
        )  # Function called for update GUI
        self.performance_monitor = performance_monitor

        # Audio parameters from config
        self.format = AUDIO_CONFIG["format"]
        self.channels = AUDIO_CONFIG["channels"]
        self.rate = AUDIO_CONFIG["rate"]
        self.recording_chunk = int(AUDIO_CONFIG["recording_chunk_size"] * self.rate)

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None

        # Recording data
        self.frames = []
        self.start_time = 0

        # Thread management
        self.record_thread = None
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()

        logger.debug("AudioProcessor initialized")

    def start_recording(self, input_queue):
        """Start audio recording."""
        if not self.state_manager.set_state(AppState.RECORDING):
            return False

        # Clear previous recording data
        self.frames = []
        self.audio_queue = input_queue
        self.start_time = time.time()

        # Start recording thread
        self.record_thread = threading.Thread(target=self._record_audio_thread)
        self.record_thread.daemon = True
        self.record_thread.start()

        logger.info("Recording started")
        return True

    def stop_recording(self):
        """Stop audio recording and clean up resources."""
        if self.state_manager.is_recording():
            self.state_manager.set_state(AppState.IDLE)

            # Signal thread to stop
            self.stop_event.set()

            # Wait for recording thread to finish (with timeout)
            if self.record_thread and self.record_thread.is_alive():
                self.record_thread.join(timeout=1.0)
                if self.record_thread.is_alive():
                    logger.warning("Recording thread did not terminate properly")

            # Ensure cleanup in case of errors
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            logger.info("Recording stopped")
            return True

        logger.warning("Cannot stop, recording is not active")
        return False

    def toggle_pause(self):
        """Toggle recording pause state."""

        current_state = self.state_manager.current_state

        if current_state == AppState.RECORDING:
            self.state_manager.set_state(AppState.RECORDING_PAUSED)
            logger.debug("(Audio Processor) Recording paused")
            return True
        elif current_state == AppState.RECORDING_PAUSED:
            self.state_manager.set_state(AppState.RECORDING)
            logger.debug("(Audio Processor) Recording resumed")
            return True
        else:
            logger.warning("Cannot toggle pause: not in a recording state")
            return False

    def get_recording_time(self):
        """
        Get the current recording time in seconds.

        Returns:
            float: Recording time in seconds
        """
        if not self.state_manager.is_recording():
            return 0

        return time.time() - self.start_time

    def _record_audio_thread(self):
        """Background thread function for audio recording."""
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.recording_chunk,
            )

            # Record until stopped
            while not self.stop_event.is_set() and self.state_manager.is_recording():
                if self.state_manager.current_state == AppState.RECORDING:
                    self._record_frame()
                else:
                    # Reduce CPU usage while paused
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in recording thread: {str(e)}")

        finally:
            # Clean up
            if hasattr(self, "stream") and self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

    def _record_frame(self):
        """Helper function to record a frame and update queue/performance monitor."""
        # Only record when not paused
        data = self.stream.read(self.recording_chunk, exception_on_overflow=False)
        self.frames.append(data)

        try:
            self.audio_queue.put_nowait(data)
        except queue.Full:
            logger.warning("Audio queue is full. Dropping frame.")

        # Update performance monitor
        if self.performance_monitor:
            self.performance_monitor.record_frame_processed()

    def get_next_audio_chunk(self, timeout=0.5):
        """
        Get the next audio chunk from the queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Audio data or None if queue is empty
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_recorded_frames(self):
        """
        Get the recorded audio frames.

        Returns:
            List of audio data frames
        """
        return self.frames

    def clear_recorded_frames(self):
        """Clear the recorded audio frames."""
        self.frames = []

    def play_audio_file(self, file_path, on_complete=None):
        """
        Play an audio file.

        Args:
            file_path: Path to the audio file
            on_complete: Callback to call when playback completes
        """
        assert self.state_manager.current_state == AppState.PLAYING

        # Start playback thread
        play_thread = threading.Thread(
            target=self._play_audio_thread, args=(file_path, on_complete)
        )
        play_thread.daemon = True
        play_thread.start()

        logger.info(f"Playing audio file: {file_path}")
        return True

    def stop_playback(self):
        """Stop audio playback."""
        if self.state_manager.current_state == AppState.PLAYING:
            self.state_manager.set_state(AppState.IDLE)
            return True
        return False

    def _play_audio_thread(self, file_path, on_complete=None):
        """
        Background thread function for audio playback.

        Args:
            file_path: Path to the audio file
            on_complete: Callback to call when playback completes
        """
        try:
            # Open the WAV file
            wf = wave.open(file_path, "rb")

            # Initialize playback stream
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            # Read and play chunks
            data = wf.readframes(self.recording_chunk)

            while data and self.state_manager.is_playing():
                stream.write(data)
                data = wf.readframes(self.recording_chunk)

            # Clean up
            stream.stop_stream()
            stream.close()
            wf.close()

            # If we got here naturally (not stopped), transition to IDLE
            if self.state_manager.current_state == AppState.PLAYING:
                self.state_manager.set_state(AppState.IDLE)

            # Call completion callback if provided
            if on_complete:
                on_complete()

            logger.debug("Audio playback completed or stopped")

        except Exception as e:
            logger.error(f"Error in playback thread: {str(e)}")
            self.state_manager.set_state(AppState.IDLE)

    def cleanup(self):
        """Clean up resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.audio.terminate()
        logger.info("AudioProcessor resources cleaned up")

    def _convert_to_wav(self, file_path):
        """Convert MP3 or M4A to WAV and return the new file path."""
        try:
            self.events.emit("update_status", f"Converting {file_path} to WAV...")

            # Load the audio file
            audio = AudioSegment.from_file(file_path)

            # Save the converted file to a temporary WAV file
            tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            audio.export(tmpfile.name, format="wav")

            return tmpfile.name  # Return path to the new WAV file
        except Exception as e:
            self.events.emit("update_status", f"Error in audio conversion: {str(e)}")
            raise e

    def _audio_consistency_check(self, file_path):
        """Ensure the audio is in the correct format. Convert if needed and return the path."""
        try:
            # Convert to WAV if needed
            if file_path.endswith((".mp3", ".m4a")):
                file_path = self._convert_to_wav(file_path)

            # Load the (now WAV) audio file
            audio = AudioSegment.from_file(file_path)

            # Apply consistency transformations
            modified = False

            if audio.channels != self.channels:
                # logger.info("Converting audio to mono...")
                self.events.emit("update_status", "Converting audio to mono...")
                audio = audio.set_channels(self.channels)
                modified = True

            if audio.frame_rate != self.rate:
                # logger.info(f"Resampling audio to {self.rate // 1000} kHz...")
                self.events.emit(
                    "update_status", f"Resampling audio to {self.rate // 1000} kHz..."
                )
                audio = audio.set_frame_rate(self.rate)
                modified = True

            # TODO - use global parameters
            if audio.sample_width != 2:  # Ensure 16-bit PCM
                # logger.info("Converting audio to 16-bit PCM...")
                self.events.emit("update_status", "Converting audio to 16-bit PCM...")
                audio = audio.set_sample_width(2)
                modified = True

            # If modifications were made, save to a new temp file
            if modified:
                tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                audio.export(tmpfile.name, format="wav")
                return tmpfile.name  # Return modified WAV file path

            return file_path  # Return original WAV if no changes were needed

        except Exception as e:
            self.events.emit("error", f"Error in audio processing: {str(e)}")
            raise e

    def simulate_audio_stream(self, file_path, transcription_service):
        """
        Simulate real-time audio streaming from a file.

        Args:
            file_path: Path to the audio file
            transcription_service: TranscriptionService instance to process audio
        """
        wf = None
        try:
            # Load and preprocess audio file
            file_path = self._audio_consistency_check(file_path)

            # Set simulation state
            if not self.state_manager.is_simulating():
                self.state_manager.prepare_simulation()

            # Open the WAV file for streaming
            wf = wave.open(file_path, "rb")
            chunk_size = int(
                self.rate * transcription_service.min_chunk
            )  # ASR processing chunk size

            self.events.emit("update_status", "Streaming simulated audio...")

            # Simulation loop
            while self.state_manager.is_simulating():
                data = wf.readframes(chunk_size)
                if not data:
                    break  # Stop when no more data

                # Convert bytes to NumPy array (int16)
                audio_array = np.frombuffer(data, dtype=np.int16)

                # Process audio with ASR
                transcription_service.online.insert_audio_chunk(audio_array)
                result = transcription_service.online.process_iter()

                # If we have a transcript, send it to callback
                if (
                    result[0] is not None
                ):  # and transcription_service.transcript_callback:
                    transcript = result[2]
                    self.events.emit("update_transcription", transcript)
                    # transcription_service.transcript_callback(transcript)

                    if self.performance_monitor:
                        self.performance_monitor.record_ui_update()

                    logger.debug(f"ASR Output: {transcript}")

                # Simulate real-time delay
                time.sleep(transcription_service.min_chunk)

            if self.state_manager.is_simulating():
                self.events.emit("update_status", "Simulation completed.")

        except Exception as e:
            error_message = str(e)
            self.events.emit("error", f"Error in simulation: {error_message}")

        finally:
            # Reset simulation state
            if self.state_manager.is_simulating():
                self.state_manager.set_state(AppState.IDLE)
            if wf:
                wf.close()

    def activate_simulation(self):
        """Prepare for audio simulation. Set state to simulating for updating UI"""
        logger.debug("Preparing audio simulation (function called)")
        if not self.state_manager.is_simulating():
            self.state_manager.set_state(AppState.SIMULATING)
            return True

    def stop_simulation(self):
        """Stop audio simulation."""
        # logger.debug("Stopping audio simulation (function called)")
        if self.state_manager.is_simulating():
            self.state_manager.set_state(AppState.IDLE)
            self.events.emit("update_status", "Simulation stopped.")
            return True
        return False

    def save_recording(self, file_path):
        """Save the recorded audio to a WAV file."""
        if not self.frames:
            self.events.emit("error", "No audio to save.")
            return False

        try:
            # Save the audio to a WAV file
            with wave.open(file_path, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(self.frames))

            self.events.emit("update_status", f"Recording saved to {file_path}")
            return True

        except Exception as e:
            error_message = str(e)
            self.events.emit(
                "error",
                f"Error saving recording: {error_message}",
                f"Error saving recording (save_recording_audio_processor): {error_message}",
            )
            return False

    def get_audio_queue_size(self):
        """Get the current size of the audio queue in a thread-safe manner."""
        try:
            return self.audio_queue.qsize()
        except Exception:
            # Some implementations of queue don't support qsize
            return -1

    def get_state(self):
        """Get the current state of the audio processor."""
        return self.state_manager.current_state

    def activate_playback(self):
        if not self.state_manager.is_playing():
            self.state_manager.set_state(AppState.PLAYING)
            return True
        return False
