import logging
import queue
from utils.logging_setup import logger
from utils.config import LANGUAGES


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
        self.volume_queue = queue.Queue()
        self.audio_processor.volume_queue = self.volume_queue

        # Initialize main_window panels:
        self.main_window.initialize_panels(self)

        self.events.on("update_status", self.on_update_status)
        self.events.on("error", self.on_error)
        self.events.on("update_transcription", self.on_update_transcription)
        self.events.on("simulation_ended", self.on_simulation_ended)
        self.events.on("update_performance_metrics", self.on_update_performance_metrics)

        # Connect UI events to controller methods
        # self._connect_signals()
        self.logger.info("AppController initialized")

    @property
    def state_manager(self):
        return self.audio_processor.state_manager

    def toggle_recording(self):
        """Start or stop recording based on current state"""
        if not self.state_manager.is_recording():
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start the recording process"""
        self.logger.info("Starting recording")
        self.main_window.update_status("Recording started...")

        # Start recording audio
        self.audio_processor.start_recording(self.audio_queue)

        # Update UI
        self.main_window.update_for_state(self.audio_processor.get_state())

        # Start volume monitoring
        self.main_window.recording_panel.start_volume_monitoring()

        # Start transcribing audio
        # TODO: end implementation
        self.transcription_service.start_transcription(self.audio_processor)

        # self.process_thread = threading.Thread(target=self.process_audio)
        # self.process_thread.daemon = True
        # self.process_thread.start()

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
        if self.state_manager.is_paused():
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
                self.main_window.show_success_message(f"Recording saved to {file_path}")
            else:
                self.events.emit("error", "Failed to save recording")
        except Exception as e:
            error_message = str(e)
            self.events.emit(
                "error",
                f"Error saving recording: {error_message}",
                f"Error saving recording (save_recording_controller_function): {error_message}",
            )

        # def process_audio(self):
        """Process audio chunks from the queue and update transcription"""
        while self.state_manager.is_recording():
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
        if not self.state_manager.is_simulating():
            # Get file path from UI
            file_path = self.main_window.show_open_dialog()

            if file_path:
                self.main_window.update_status(
                    f"Simulating recording with file: {file_path}"
                )

                self.with_playback = True

                if not self.with_playback:
                    self.audio_processor.start_simulation(
                        file_path, self.transcription_service
                    )
                else:
                    self.audio_processor.start_simulation_with_playback(
                        file_path, self.transcription_service
                    )
                    # Update UI
                self.main_window.recording_panel.update_for_state(
                    self.audio_processor.get_state()
                )

        else:
            # Stop simulation
            self.audio_processor.stop_simulation()
            self.main_window.recording_panel.update_for_state(
                self.audio_processor.get_state()
            )

    def set_playback_while_simulating(self):
        """Set playback while simulating"""
        self.with_playback = (
            self.main_window.recording_panel.with_playback_checkbox.get()
        )
        logger.debug(f"Playback while simulating was set to {self.with_playback}")

    # TODO: Refine it and move what is needed to the audio_processor
    def toggle_play_audio(self):
        """Play audio from a file"""
        if not self.state_manager.is_playing():
            # Get file path from UI
            file_path = self.main_window.show_open_dialog()

            if not file_path:
                return

            self.audio_processor.activate_playback()  # Set state to playing
            self.stopped = False

            # Update UI
            self.main_window.update_for_state(self.audio_processor.get_state())

            self.events.emit("update_status", f"Playing audio from {file_path}")

            self.audio_processor.play_audio_file(
                file_path, on_complete=lambda: self.on_playback_complete(file_path)
            )

        else:
            # Stop playback
            self.stopped = self.audio_processor.stop_playback()
            self.main_window.update_for_state(self.audio_processor.get_state())

    def on_playback_complete(self, file_path):
        """Callback to handle when playback finishes"""

        def update_ui():
            if self.stopped:
                self.events.emit("update_status", "Playback stopped")
            else:
                self.events.emit(
                    "update_status", f"Finished playing audio from {file_path}"
                )
                # self.main_window.update_status(f"Finished playing audio from {file_path}")

            self.main_window.update_for_state(self.audio_processor.get_state())

        # Use a thread-safe way to update the UI (depends on framework: tkinter, Qt, etc.)
        self.main_window.run_on_ui_thread(update_ui)

    def change_language(self, language_name, language_codes=LANGUAGES):
        """Change the transcription language"""
        try:
            language_code = language_codes[language_name]
            if not language_code:
                logger.error(f"Language code for {language_name} not found")
            self.transcription_service.set_language(language_code)
            self.events.emit(
                "update_status",
                f"Language changed to {language_name} ({language_code})",
            )
            self.logger.info(f"Language changed to {language_name} ({language_code})")

        except Exception as e:
            error_message = str(e)
            self.main_window.update_status(f"Error changing language: {error_message}")
            self.logger.error(f"Error changing language: {error_message}")

    def on_update_status(self, message, log_message=None):
        """Update the status display."""
        self.main_window.update_status(message)
        if not log_message:
            self.logger.info("Status update:" + message)
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

    def on_simulation_ended(self):
        self.main_window.recording_panel.update_for_state(
            self.audio_processor.get_state()
        )

    # TODO: Check if everything is good here
    def cleanup(self):
        """Clean up all resources and threads"""
        self.logger.info("Cleaning up resources")

        # Stop any ongoing processes
        if self.state_manager.is_recording():
            self.stop_recording()

        if self.state_manager.is_playing():
            self.audio_processor.stop_playback()

        if self.state_manager.is_simulating():
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
        return self.state_manager.get_state()

    def get_volume(self):
        vol_level = self.audio_processor.get_volume_level()
        if vol_level is None:
            return None
        return self.audio_processor.get_volume_level()

    def get_performance_metrics(self):
        """Get performance metrics from the audio processor."""
        return self.transcription_service.get_performance_metrics()

    def on_update_performance_metrics(self, metrics):
        """Update the performance metrics display."""
        self.main_window.update_performance_metrics(metrics)
