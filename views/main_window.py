import customtkinter as ctk
from tkinter import messagebox
from views.recording_panel import RecordingPanel
from views.transcript_panel import TranscriptPanel
from utils.config import UI_CONFIG
from utils.logging_setup import logger

# from controllers.app_controller import AppController


class MainWindow:
    def __init__(self, root, state_manager):  # audio_processor, transcription_service)
        """Initialize the main application window.

        Args:
            controller: The application controller that handles business logic
        """
        # self.controller = AppController(self, audio_processor, transcription_service)
        self.root = root
        self.root.title("Automatic Speech Recognition App")
        self.root.geometry("800x1000")
        self.root.resizable(True, True)

        # Configure UI appearance
        ctk.set_appearance_mode(UI_CONFIG["appearance_mode"])
        ctk.set_default_color_theme(UI_CONFIG["color_theme"])
        ctk.deactivate_automatic_dpi_awareness()
        ctk.set_widget_scaling(UI_CONFIG["widget_scaling"])

        # Configure main grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Set app_state
        self.state_manager = state_manager

        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="#e0e0e0", corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Adjust row weights to give more space to performance monitor
        self.main_frame.grid_rowconfigure(0, weight=0)  # Title - no expansion
        self.main_frame.grid_rowconfigure(1, weight=2)  # Recording panel
        self.main_frame.grid_rowconfigure(2, weight=1)  # Secondary controls
        self.main_frame.grid_rowconfigure(4, weight=3)  # Status/transcript area

        # Create title
        self._create_title()

        # Initialize UI components
        # Create panels (will be initialized with controller later)
        self.recording_panel = None
        self.transcript_panel = None

        # Set up closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("Main window initialized")

    def _create_title(self):
        """Create the application title label."""
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Audio Recorder",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#000000",
        )
        title_label.grid(row=0, column=0, pady=(20, 20))

    def initialize_panels(self, controller):
        """Initialize UI panels with controller reference."""
        self.recording_panel = RecordingPanel(self.main_frame, controller)
        self.transcript_panel = TranscriptPanel(self.main_frame, controller)

    def start(self):
        """Start the main application loop."""
        logger.info("Starting main application loop")
        self.root.mainloop()

    def _on_closing(self):
        """Handle application closing."""
        logger.info("Application closing")
        self.controller.shutdown()
        self.root.destroy()

    def update_status(self, message):
        """Update the status display.

        Args:
            message (str): Status message to display
        """
        self.transcript_panel.update_status(message)

    def update_transcription(self, text):
        """Update the transcript display.

        Args:
            text (str): Transcript text to display
        """
        self.transcript_panel.update_transcription(text)

    def update_timer(self, time_str):
        """Update the recording timer display.

        Args:
            time_str (str): Time string to display (format: MM:SS)
        """
        self.recording_panel.update_timer(time_str)

    def update_ui_for_state(self, state):
        """Update UI components based on application state.

        Args:
            state: Current application state
        """
        self.recording_panel.update_for_state(state)

    def show_open_dialog(
        self,
        title="Select Audio File",
        filetypes=[
            ("Audio Files", ("*.wav", "*.mp3", "*.m4a")),
            ("All files", "*.*"),
        ],
    ):
        """Show a file open dialog and return the selected path"""
        return ctk.filedialog.askopenfilename(title=title, filetypes=filetypes)

    def show_save_dialog(self):
        """Show a save file dialog and return the selected path"""
        logger.debug("Showing save dialog")
        return ctk.filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("Audio files", "*.wav"), ("All files", "*.*")],
        )

    def show_success_message(self, message):
        """Show a success message"""
        logger.debug("Showing success message")
        messagebox.showinfo("Success", message)

    def run_on_ui_thread(self, func, *args, **kwargs):
        """Run a function on the UI thread"""
        self.root.after(0, func, *args, **kwargs)

    def update_for_state(self, state):
        """Update UI components based on application state."""
        self.recording_panel.update_for_state(state)
        self.transcript_panel.update_for_state(state)

    def update_performance_metrics(self, metrics):
        """Update performance metrics display."""
        self.transcript_panel.update_performance_metrics_ui(metrics)

    def update_volume_meter(self, volume_level):
        """Update the volume meter in the recording panel."""
        self.recording_panel.update_volume_meter(volume_level)
