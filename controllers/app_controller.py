import logging
import threading
import queue
import time
from utils.logging_setup import logger


class AppController:
    def __init__(self, main_window, audio_processor, transcription_service, events):
        """
        Initialize the application controller.

        Args:
            main_window: The main application window view
            audio_processor: The audio recording/processing model
            transcription_service: The transcription service model
        """
        self.logger = logger
        self.main_window = main_window
        self.audio_processor = audio_processor
        self.transcription_service = transcription_service
        self.events = events

        # Communication queue
        self.audio_queue = queue.Queue()

        # Initialize main_window panels:
        self.main_window.initialize_panels(self)

        self.events.on("update_status", self.on_update_status)
        self.events.on("error", self.on_error)
        self.events.on("update_transcription", self.on_update_transcription)

        # Connect UI events to controller methods
        # self._connect_signals()
        self.logger.info("AppController initialized")

    def toggle_recording(self):
        """Start or stop recording based on current state"""
        if not self.audio_processor.state_manager.is_recording():
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start the recording process"""
        self.logger.info("Starting recording")
        self.main_window.update_status("Recording started...")

        # Setup audio processor
        self.audio_processor.start_recording(self.audio_queue)

        # Update UI
        self.main_window.recording_panel.update_for_state(
            self.audio_processor.get_state()
        )

        # Start processing thread - TODO FIX The function before the threading

        self.process_thread = threading.Thread(target=self.process_audio)
        self.process_thread.daemon = True
        self.process_thread.start()

    def stop_recording(self):
        """Stop the recording process"""
        self.logger.info("Stopping recording")
        self.audio_processor.stop_recording()

        # Update UI
        self.main_window.update_status("Recording stopped.")
        self.main_window.recording_panel.update_for_state(
            self.audio_processor.get_state()
        )

        # Wait for threads to complete
        if hasattr(self, "process_thread") and self.process_thread.is_alive():
            self.process_thread.join(timeout=1.0)

    def toggle_pause(self):
        """Pause or resume recording"""
        self.audio_processor.toggle_pause()

        # Update UI
        if self.audio_processor.state_manager.is_paused():
            self.main_window.update_status("Recording paused.")
        else:
            self.main_window.update_status("Recording resumed.")

        self.main_window.recording_panel.update_for_state(
            self.audio_processor.get_state()
        )

    def save_recording(self):
        """Save the recorded audio to a file"""
        file_path = self.main_window.show_save_dialog()
        logging.debug(f"Save file path: {file_path}")
        if not file_path:
            return  # User cancelled

        try:
            success = self.audio_processor.save_recording(file_path)
            if success:
                self.events.emit("update_status", f"Recording saved to: {file_path}")
            else:
                self.events.emit("error", "Failed to save recording")
        except Exception as e:
            error_message = str(e)
            self.events.emit(
                "error",
                f"Error saving recording: {error_message}",
                f"Error saving recording (save_recording_controller_function): {error_message}",
            )

    def process_audio(self):
        """Process audio chunks from the queue and update transcription"""
        while self.audio_processor.state_manager.is_recording():
            try:
                data = self.audio_queue.get(timeout=0.5)

                # Process audio with transcription service
                result = self.transcription_service.process_audio_chunk(data)

                if result and result[0] is not None:
                    transcript = result[2]
                    self.main_window.update_transcription(transcript)

            except queue.Empty:
                pass
            except Exception as e:
                error_message = str(e)
                self.main_window.update_status(f"Processing error: {error_message}")
                self.logger.error(f"Error in processing audio: {error_message}")

    def toggle_simulation(self):
        """Simulate recording from a file"""
        if not self.audio_processor.state_manager.is_simulating():
            # Get file path from UI
            file_path = self.main_window.show_open_dialog(
                title="Select Audio File",
                filetypes=[
                    ("Audio Files", ("*.wav", "*.mp3", "*.m4a")),
                    ("All files", "*.*"),
                ],
            )

            if file_path:
                self.main_window.update_status(
                    f"Simulating recording with file: {file_path}"
                )

                self.audio_processor.activate_simulation()
                # Update UI
                self.main_window.recording_panel.update_for_state(
                    self.audio_processor.get_state()
                )

                # Start simulation in a thread
                self.simulate_thread = threading.Thread(
                    target=self.run_simulation, args=(file_path,), daemon=True
                )

                # self.simulate_thread.daemon = True
                self.simulate_thread.start()

        else:
            # Stop simulation
            self.audio_processor.stop_simulation()
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )

            # Wait for simulation thread to finish
            if hasattr(self, "simulate_thread") and self.simulate_thread.is_alive():
                self.simulate_thread.join(timeout=0.5)

    def toggle_play_audio(self):
        """Play audio from a file"""
        if not self.audio_processor.state_manager.is_playing():
            # Get file path from UI
            file_path = self.main_window.show_open_dialog(
                title="Select Audio File",
                filetypes=[
                    ("Audio Files", ("*.wav", "*.mp3", "*.m4a")),
                    ("All files", "*.*"),
                ],
            )

            if not file_path:
                return

            self.audio_processor.activate_playback()
            self.stopped = False

            # Update UI
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )

            # Start playback in a thread
            self.play_thread = threading.Thread(
                target=self.run_playback, args=(file_path,)
            )
            self.play_thread.daemon = True
            self.play_thread.start()
        else:
            # Stop playback
            self.stopped = self.audio_processor.stop_playback()
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )

    def run_simulation(self, file_path):
        """Run the simulation process"""
        try:
            self.audio_processor.simulate_audio_stream(
                file_path, self.transcription_service
            )

        except Exception as e:
            error_message = str(e)
            self.main_window.update_status(f"Error in simulation: {error_message}")
            self.logger.error(f"Error in simulation: {error_message}")

        finally:
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )
            # Reset UI if not already reset
            if self.audio_processor.state_manager.is_simulating():
                self.audio_processor.stop_simulation()

    def run_playback(self, file_path):
        """Run the audio playback process"""
        try:
            self.main_window.update_status(f"Playing audio from {file_path}")

            success = self.audio_processor.play_audio_file(file_path)

            if not success:
                self.main_window.update_status("Could not start playback")
                self.main_window.recording_panel.update_for_state(
                    self.audio_processor.get_state()
                )
                return

            # Wait for playback to complete or be stopped
            while self.audio_processor.state_manager.is_playing():
                time.sleep(0.1)

            # Update status when complete
            if self.stopped:
                logger.debug(f"CALLED STOPPED {self.stopped}")
                self.main_window.update_status("Playback stopped")
            else:
                self.main_window.update_status(
                    f"Finished playing audio from {file_path}"
                )
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )

        except Exception as e:
            error_message = str(e)
            self.main_window.update_status(f"Error playing audio: {error_message}")
            self.logger.error(f"Error playing audio: {error_message}")
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )

    def change_language(self, language_code, language_name):
        """Change the transcription language"""
        try:
            self.transcription_service.set_language(language_code)
            self.main_window.update_status(
                f"Language changed to {language_name} ({language_code})"
            )
            self.logger.info(f"Language changed to {language_name} ({language_code})")
        except Exception as e:
            error_message = str(e)
            self.main_window.update_status(f"Error changing language: {error_message}")
            self.logger.error(f"Error changing language: {error_message}")

    def play_audio(self, file_path):
        """Play audio from the given file path"""
        self.logger.info(f"Playing audio from {file_path}")

        # Start playback in a thread
        self.play_thread = threading.Thread(
            target=self._run_playback, args=(file_path,)
        )
        self.play_thread.daemon = True
        self.play_thread.start()

        # Update status
        self.main_window.update_status(f"Playing audio from {file_path}")

    def on_update_status(self, message, log_message=None):
        """Update the status display."""
        self.main_window.update_status(message)
        if not log_message:
            self.logger.info("Staus update:" + message)
        else:
            self.logger.info(log_message)

    def on_update_transcription(self, message, log_message=None):
        """Update the status display."""
        self.main_window.update_transcription(message)
        if not log_message:
            self.logger.info("Transcription: " + message)
        else:
            self.logger.info(log_message)

    def on_error(self, message, log_message=None):
        """Handle an error message."""
        self.main_window.update_status(message)
        if not log_message:
            self.logger.error(message)
        else:
            self.logger.error(log_message)

    def cleanup(self):
        """Clean up all resources and threads"""
        self.logger.info("Cleaning up resources")

        # Stop any ongoing processes
        if self.audio_processor.state_manager.is_recording():
            self.stop_recording()

        if self.audio_processor.state_manager.is_playing():
            self.audio_processor.stop_playback()

        if self.audio_processor.state_manager.is_simulating():
            self.audio_processor.stop_simulation()

        # Wait for threads to finish
        threads_to_join = []

        if hasattr(self, "process_thread") and self.process_thread.is_alive():
            threads_to_join.append(self.process_thread)

        if hasattr(self, "simulate_thread") and self.simulate_thread.is_alive():
            threads_to_join.append(self.simulate_thread)

        if hasattr(self, "play_thread") and self.play_thread.is_alive():
            threads_to_join.append(self.play_thread)

        # Join all threads with timeout
        for thread in threads_to_join:
            thread.join(timeout=0.5)

        # Clean up resources
        self.audio_processor.cleanup()

        # Stop transcription service
        self.transcription_service.stop_processing()

        self.logger.info("Cleanup complete")

    def _get_state(self):
        return self.audio_processor.state_manager.get_state()
