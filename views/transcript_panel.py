import customtkinter as ctk
import time
from utils.logging_setup import logger
from models.app_state import AppState


class TranscriptPanel:
    def __init__(self, parent, controller):
        """Initialize the transcript and status panel.

        Args:
            parent: Parent widget
            controller: Application controller
        """
        self.controller = controller
        self.logger = logger

        # Define parent window
        self.state_manager = self.controller.state_manager

        # Create bottom frame for status and transcript
        bottom_frame = ctk.CTkFrame(parent, fg_color="#e0e0e0", corner_radius=0)
        bottom_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Create status section
        self._create_status_section(bottom_frame)

        # Create transcript section
        self._create_transcript_section(bottom_frame)

        # Create performance monitor - taller now
        self._create_performance_monitor(bottom_frame)

        self.logger.debug("Transcript panel initialized")

    def _create_status_section(self, parent):
        """Create the status display section."""
        status_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=4)
        status_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            status_frame,
            text="Status",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            text_color="#000000",
        ).grid(row=0, column=0, padx=10, pady=(10, 5))

        self.status_text = ctk.CTkTextbox(
            status_frame,
            height=100,
            font=ctk.CTkFont(family="Courier", size=12),
            wrap="word",
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#999999",
            text_color="#000000",
        )
        self.status_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _create_transcript_section(self, parent):
        """Create the transcript display section."""
        transcript_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=4)
        transcript_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        transcript_frame.grid_columnconfigure(0, weight=1)
        transcript_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            transcript_frame,
            text="Transcript",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            text_color="#000000",
        ).grid(row=0, column=0, padx=10, pady=(10, 5))

        self.transcript_text = ctk.CTkTextbox(
            transcript_frame,
            height=100,
            font=ctk.CTkFont(family="Courier", size=12),
            wrap="word",
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#999999",
            text_color="#000000",
        )
        self.transcript_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _create_performance_monitor(self, parent):
        """Create the performance monitor section with increased height."""
        perf_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=4)
        perf_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        perf_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            perf_frame,
            text="Performance Monitor",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
        ).grid(row=0, column=0, padx=5, pady=5)

        # Increased height from 50 to 120
        self.perf_text = ctk.CTkTextbox(
            perf_frame,
            height=120,
            font=ctk.CTkFont(family="Courier", size=10),
            fg_color="#FFFFFF",
        )
        self.perf_text.grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew"
        )

    def update_status(self, message):
        """Update the status display.

        Args:
            message (str): Status message to display
        """
        # Add timestamp to status messages
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        status_message = f"[{timestamp}] {message}\n"

        # Update status text widget
        self.status_text.insert("end", status_message)
        self.status_text.see("end")

    def update_transcription(self, text):
        """Update the transcript display.

        Args:
            text (str): Transcript text to display
        """
        # current_text = self.transcript_text.get("0.0", "end").strip()
        self.transcript_text.insert("end", " " + text)
        self.transcript_text.see("end")

    def append_transcript(self, text):
        """Append new transcribed text.

        Args:
            text (str): Text to append to transcript
        """
        self.transcript_text.insert("end", text + " ")  # Append with space
        self.transcript_text.see("end")  # Auto-scroll
        self.logger.debug(f"Transcript appended: {text}")

    def update_for_state(self, state):
        """Update UI components based on application state."""
        if state == AppState.RECORDING:
            self.start_perf_monitor()
        else:
            self.stop_perf_monitor()

    def start_perf_monitor(self):
        self.is_monitoring_perf = True
        self.perf_update_interval = 1000  # Update every seconds
        self.update_performance_metrics_ui(self.controller.get_performance_metrics())

    def update_perf_monitor(self):
        if self.is_monitoring_perf:
            # Update performance stats
            self.perf_stats = self.controller.get_performance_metrics()

            # Calculate rates
            # TODO: fix this
            api_rate = (
                self.perf_stats["api_call_time"]
                if self.state_manager.is_recording()
                else 0
            )
            frame_rate = (
                self.perf_stats["frames_processed"]
                if self.state_manager.is_recording()
                else 0
            )
            avg_api_time = (
                (self.perf_stats["api_total_time"] / self.perf_stats["ui_updates"])
                * 1000
                if self.perf_stats["ui_updates"] > 0  # TODO: fix this
                else 0
            )

            # Update display
            perf_info = f"API calls/sec: {api_rate:.1f} | Avg API time: {avg_api_time:.1f}ms | Frames/sec: {frame_rate:.1f}"
            self.perf_text.delete("0.0", "end")
            self.perf_text.insert("0.0", perf_info)

        # Schedule next update
        self.root.after(self.perf_update_interval, self.update_perf_monitor)

    def stop_perf_monitor(self):
        """Stop volume level updates"""
        self.is_monitoring_perf = False

    def update_performance_metrics_ui(self, metrics):
        """Update performance metrics display.

        Args:
            metrics (dict): Dictionary containing performance metrics
        """
        if self.is_monitoring_perf:
            lines = []
            selected_items = []  # list(metrics.items())

            # Preprocess values
            for i, (key, value) in enumerate(metrics.items()):
                if isinstance(value, float):
                    value = round(value, 2)
                elif isinstance(value, list):
                    continue

                if key.endswith("time"):
                    value = f"{value} s"

                selected_items.append(
                    (key, str(value))
                )  # Ensure all values are strings

            # Format in pairs of 2 per line
            for i in range(0, len(selected_items), 2):
                left = f"{selected_items[i][0]:<20}: {selected_items[i][1]:<20}"
                right = ""
                if i + 1 < len(selected_items):
                    right = f"{selected_items[i + 1][0]:<20}: {selected_items[i + 1][1]:<20}"
                lines.append(left + "   " + right)

            # Join and display
            perf_info = "\n".join(lines)
            self.perf_text.delete("0.0", "end")
            self.perf_text.insert("0.0", perf_info)
