import customtkinter as ctk
from utils.logging_setup import logger
from models.app_state import AppState
from utils.config import LANGUAGES


class RecordingPanel:
    def __init__(self, parent, controller):
        """Initialize the recording control panel.

        Args:
            parent: Parent widget
            controller: Application controller
        """

        self.controller = controller

        # Button styling
        self.button_height = 36
        self.button_font = ctk.CTkFont(family="Arial", size=16, weight="bold")

        # Create top frame for recording controls
        self._create_first_panel(parent)

        # Create secondary controls
        self._create_secondary_panel(parent)

        logger.info("Recording panel initialized")

    def _create_first_panel(self, parent):
        """Create the top control panel."""
        # Create recording controls panel
        self.first_panel = ctk.CTkFrame(
            parent,
            fg_color="#d9d9d9",
            corner_radius=8,
            border_width=2,
        )
        self.first_panel.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.first_panel.grid_columnconfigure((0, 1, 2), weight=1)
        self.first_panel.grid_rowconfigure((0, 1, 2), weight=1)

        # Create recording controls
        self._create_record_button()
        self._create_pause_button()
        self._create_save_button()
        self._create_timer()
        self._create_volume_meter(self.first_panel)

    def _create_record_button(self):
        """Create the record/stop button."""
        self.record_button = ctk.CTkButton(
            self.first_panel,
            text="Record",
            command=self.controller.toggle_recording,
            fg_color="#4682B4",  # Steel Blue
            hover_color="#36648B",
            border_width=2,
            border_color="#36648B",
            corner_radius=6,
            height=self.button_height,
            font=self.button_font,
            text_color="#FFFFFF",
        )
        self.record_button.grid(row=0, column=0, padx=10, pady=15, sticky="ew")

    def _create_pause_button(self):
        """Create the pause/resume button."""
        self.pause_button = ctk.CTkButton(
            self.first_panel,
            text="Pause",
            command=self.controller.toggle_pause,
            state="disabled",
            fg_color="#CD853F",  # Peru
            hover_color="#8B5A2B",
            border_width=2,
            border_color="#8B5A2B",
            corner_radius=6,
            height=self.button_height,
            font=self.button_font,
            text_color="#FFFFFF",
        )
        self.pause_button.grid(row=0, column=1, padx=10, pady=15, sticky="ew")

    def _create_save_button(self):
        """Create the save button."""
        self.save_button = ctk.CTkButton(
            self.first_panel,
            text="Save",
            command=self.controller.save_recording,
            state="disabled",
            fg_color="#2E8B57",  # Sea Green
            hover_color="#1D5B38",
            border_width=2,
            border_color="#1D5B38",
            corner_radius=6,
            height=self.button_height,
            font=self.button_font,
            text_color="#FFFFFF",
        )
        self.save_button.grid(row=0, column=2, padx=10, pady=15, sticky="ew")

    def _create_timer(self):
        """Create the recording timer display."""
        self.timer_label = ctk.CTkLabel(
            self.first_panel,
            text="00:00",
            font=ctk.CTkFont(family="Courier", size=36, weight="bold"),
            text_color="#0000CD",  # Medium Blue
        )
        self.timer_label.grid(row=1, column=0, columnspan=3, pady=10)

        self.is_paused = False

    def _create_volume_meter(self, parent):
        """Create the volume meter section."""
        volume_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=4)
        volume_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        volume_frame.grid_columnconfigure(1, weight=1)

        # ctk.CTkLabel(
        #     volume_frame,
        #     text="Volume",
        #     font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
        # ).grid(row=0, column=0, padx=5, pady=5)

        # Volume level label
        self.volume_level_label = ctk.CTkLabel(
            volume_frame,
            text="Volume: 0.0 dB",
            font=ctk.CTkFont(family="Courier", size=10),
            width=60,
        )
        self.volume_level_label.grid(row=0, column=0, padx=(10, 5), pady=5)

        # Volume progress bar
        self.volume_progress = ctk.CTkProgressBar(
            volume_frame,
            orientation="horizontal",
            width=300,
            height=20,
            fg_color="#E0E0E0",
            progress_color="#4CAF50",  # Green color indicating volume level
        )
        self.volume_progress.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.volume_progress.set(0)  # Initial value at 0

    def _create_secondary_panel(self, parent):
        """Create the secondary control panel (simulate and play buttons with language selector)."""

        secondary_panel = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=8)
        secondary_panel.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        secondary_panel.grid_columnconfigure(
            (0, 1, 2), weight=1
        )  # Added column for language selector
        secondary_panel.grid_rowconfigure((0, 1), weight=1)

        # Simulate button
        self.simulate_button = ctk.CTkButton(
            secondary_panel,
            text="Simulate",
            command=self.controller.toggle_simulation,
            fg_color="#8A2BE2",  # Blue Violet
            hover_color="#5A189A",
            border_width=2,
            border_color="#5A189A",
            corner_radius=6,
            height=self.button_height,
            font=self.button_font,
            text_color="#FFFFFF",
        )
        self.simulate_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Play button
        self.play_button = ctk.CTkButton(
            secondary_panel,
            text="Play",
            command=self.controller.toggle_play_audio,
            fg_color="#FF6347",  # Tomato
            hover_color="#FF4500",
            border_width=2,
            border_color="#FF4500",
            corner_radius=6,
            height=self.button_height,
            font=self.button_font,
            text_color="#FFFFFF",
        )
        self.play_button.grid(row=0, column=1, padx=10, pady=10)

        self.with_playback_checkbox = ctk.CTkCheckBox(
            secondary_panel,
            text="Play while simulating",
            onvalue=True,
            offvalue=False,
            command=self.controller.set_playback_while_simulating,
            text_color="#000000",
            corner_radius=1,
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            state="normal",
        )
        self.with_playback_checkbox.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.with_playback_checkbox.select()

        # Language dropdown next to play button
        self._create_language_selector(secondary_panel)

    def _create_language_selector(self, parent):
        """Create the language selection widget."""
        # Language frame
        language_frame = ctk.CTkFrame(parent, fg_color="#d9d9d9", corner_radius=0)
        language_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        language_frame.grid_columnconfigure(0, weight=1)
        language_frame.grid_rowconfigure((0, 1), weight=1)

        # Language label
        language_label = ctk.CTkLabel(
            language_frame,
            text="Language",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color="#000000",
        )
        language_label.grid(row=0, column=0, padx=5, pady=(0, 0))

        # Language dropdown
        self.language_var = ctk.StringVar(value="Auto")
        self.language_dropdown = ctk.CTkOptionMenu(
            language_frame,
            values=list(LANGUAGES.keys()),
            variable=self.language_var,
            command=self.controller.change_language,
            width=120,
            height=self.button_height,
            font=ctk.CTkFont(family="Arial", size=14),
            fg_color="#FFFFFF",
            button_color="#555555",
            button_hover_color="#333333",
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#EEEEEE",
            dropdown_text_color="#000000",
            text_color="#000000",
        )
        self.language_dropdown.grid(row=1, column=0, padx=5, pady=(0, 0))

    def update_timer(self, time_str):
        """Update the timer display.

        Args:
            time_str (str): Time string to display (format: MM:SS)
        """
        self.timer_label.configure(text=time_str)

    def update_for_state(self, state):
        """Update UI components based on application state.

        Args:
            state: Current application state
        """
        if state == AppState.IDLE:
            self.record_button.configure(
                text="Record",
                fg_color="#4682B4",
                hover_color="#36648B",
                border_color="#36648B",
            )
            self.pause_button.configure(state="disabled", text="Pause")
            self.save_button.configure(state="normal")
            self.simulate_button.configure(
                text="Simulate",
                fg_color="#8A2BE2",
                hover_color="#5A189A",
                border_color="#5A189A",
            )
            self.play_button.configure(
                text="Play",
                fg_color="#FF6347",
                hover_color="#FF4500",
                border_color="#FF4500",
            )

            self._stop_timer()

        elif state == AppState.RECORDING:
            self.record_button.configure(
                text="Stop",
                fg_color="#B22222",
                hover_color="#8B0000",
                border_color="#8B0000",
            )
            self.pause_button.configure(state="normal", text="Pause")
            self.save_button.configure(state="disabled")

            if not self.is_paused:
                self._start_timer()
            else:
                self._resume_timer()

        elif state == AppState.RECORDING_PAUSED:
            self.pause_button.configure(text="Resume")
            self._pause_timer()

        elif state == AppState.PLAYING:
            self.play_button.configure(
                text="Stop",
                fg_color="#B22222",
                hover_color="#8B0000",
                border_color="#8B0000",
            )

        elif state == AppState.SIMULATING:
            self.simulate_button.configure(
                text="Stop",
                fg_color="#B22222",
                hover_color="#8B0000",
                border_color="#8B0000",
            )

    # Volume related methods
    def start_volume_monitoring(self):
        """Start periodic volume level updates"""
        self.is_monitoring_volume = True
        self.update_volume_display()

    def stop_volume_monitoring(self):
        """Stop volume level updates"""
        self.is_monitoring_volume = False

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
        self.volume_level_label.configure(text=f"Volume: {volume_level:.1f} dB")

    def update_volume_display(self):
        """Update volume display and schedule next update"""
        # Only proceed if monitoring is active
        if not getattr(self, "is_monitoring_volume", True):
            return

        volume = self.controller.get_volume()
        if volume is not None:
            normalized_volume = min(max((volume + 60) / 60, 0), 1)
            self.volume_progress.set(normalized_volume)
            self.volume_level_label.configure(text=f"{volume:.1f} dB")

        # Schedule next update
        self.root = self.volume_progress.winfo_toplevel()
        self.root.after(100, self.update_volume_display)

    # Timer functions
    def _start_timer(self):
        """Start the recording timer"""
        self.timer_seconds = 0
        self.timer_running = True
        self._update_timer_display()
        self._schedule_timer_update()
        self.is_paused = False

    def _stop_timer(self):
        """Stop the recording timer"""
        self.timer_running = False
        self.is_paused = False

    def _pause_timer(self):
        """Stop the recording timer"""
        self.timer_running = False
        self.is_paused = True

    def _resume_timer(self):
        """Resume the recording timer"""
        self.timer_running = True
        self._update_timer_display()
        self._schedule_timer_update()
        self.is_paused = False

    def _update_timer_display(self):
        """Update the timer display"""
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.update_timer(time_str)

    def _schedule_timer_update(self):
        """Schedule the next timer update"""
        if self.timer_running:
            self.timer_seconds += 1
            self._update_timer_display()
            self.first_panel.after(1000, self._schedule_timer_update)
