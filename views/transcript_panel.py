import customtkinter as ctk
import time
from utils.logging_setup import logger


class TranscriptPanel:
    def __init__(self, parent, controller):
        """Initialize the transcript and status panel.

        Args:
            parent: Parent widget
            controller: Application controller
        """
        self.controller = controller
        self.logger = logger

        # Create bottom frame for status and transcript
        bottom_frame = ctk.CTkFrame(parent, fg_color="#e0e0e0", corner_radius=0)
        bottom_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)
        bottom_frame.grid_columnconfigure((0, 1), weight=1)
        bottom_frame.grid_rowconfigure(0, weight=1)

        # Create status section
        self._create_status_section(bottom_frame)

        # Create transcript section
        self._create_transcript_section(bottom_frame)

        # Create performance monitor
        self._create_performance_monitor(bottom_frame)

        # Create volume meter
        self._create_volume_meter(bottom_frame)

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
        """Create the performance monitor section."""
        perf_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=4)
        perf_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        perf_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            perf_frame,
            text="Performance Monitor",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
        ).grid(row=0, column=0, padx=5, pady=5)

        self.perf_text = ctk.CTkTextbox(
            perf_frame,
            height=50,
            font=ctk.CTkFont(family="Courier", size=10),
            fg_color="#FFFFFF",
        )
        self.perf_text.grid(
            row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew"
        )

    def _create_volume_meter(self, parent):
        """Create the volume meter section."""
        volume_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=4)
        volume_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        volume_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            volume_frame,
            text="Volume",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
        ).grid(row=0, column=0, padx=5, pady=5)

        # Volume level label
        self.volume_level_label = ctk.CTkLabel(
            volume_frame,
            text="0.0 dB",
            font=ctk.CTkFont(family="Courier", size=10),
            width=60,
        )
        self.volume_level_label.grid(row=1, column=0, padx=(10, 5), pady=5)

        # Volume progress bar
        self.volume_progress = ctk.CTkProgressBar(
            volume_frame,
            orientation="horizontal",
            width=300,
            height=20,
            fg_color="#E0E0E0",
            progress_color="#4CAF50",  # Green color indicating volume level
        )
        self.volume_progress.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.volume_progress.set(0)  # Initial value at 0

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

        # # Only update if text changed substantially
        # if (
        #     len(text) - len(current_text) > 10
        #     or abs(len(text) - len(current_text)) > 20
        # ):
        #     self.transcript_text.delete("0.0", "end")
        #     self.transcript_text.insert("0.0", text)
        #     # self.logger.debug(f"Transcript window updated: {text}")

    def append_transcript(self, text):
        """Append new transcribed text.

        Args:
            text (str): Text to append to transcript
        """
        self.transcript_text.insert("end", text + " ")  # Append with space
        self.transcript_text.see("end")  # Auto-scroll
        self.logger.debug(f"Transcript appended: {text}")

    def update_performance_metrics(self, metrics):
        """Update the performance monitor display.

        Args:
            metrics (dict): Dictionary containing performance metrics
        """
        # Format metrics for display
        api_rate = metrics.get("api_rate", 0)
        avg_api_time = metrics.get("avg_api_time", 0)
        frame_rate = metrics.get("frame_rate", 0)

        perf_info = f"API calls/sec: {api_rate:.1f} | Avg API time: {avg_api_time:.1f}ms | Frames/sec: {frame_rate:.1f}"

        # Update display
        self.perf_text.delete("0.0", "end")
        self.perf_text.insert("0.0", perf_info)

    def update_volume_meter(self, volume_level):
        """Update the volume meter display.

        Args:
            volume_level (float): Current volume level in decibels
        """
        # Normalize volume level for progress bar (assuming typical range of -60 to 0 dB)
        normalized_volume = max(0, min(1, (volume_level + 60) / 60))

        # Update progress bar
        self.volume_progress.set(normalized_volume)

        # Update volume level label
        self.volume_level_label.configure(text=f"{volume_level:.1f} dB")

    def update_ui(self):
        """Fetch and update the volume bar."""
        logger.debug("Updating UI")
        volume = self.controller.get_volume()
        if volume is not None:
            normalized_volume = min(
                max((volume + 60) / 60, 0), 1
            )  # Normalize dBFS (-60 dB to 0 dB) to [0,1]
            self.volume_progress.set(normalized_volume)
        self.after(100, self.update_ui)  # Repeat every 100ms
