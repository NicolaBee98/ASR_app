"""Application state management."""

from enum import Enum, auto
from utils.logging_setup import logger


class AppState(Enum):
    """Enum representing application states."""

    IDLE = auto()
    RECORDING = auto()
    RECORDING_PAUSED = auto()
    PLAYING = auto()
    SIMULATING = auto()

    def __str__(self):
        return self.name


class StateManager:
    """Manages the application state with proper transitions."""

    def __init__(self, state_change_callback=None):
        """
        Initialize the state manager.

        Args:
            state_change_callback: Function to call when state changes
        """
        self._current_state = AppState.IDLE
        self._state_change_callback = state_change_callback
        self.logger = logger
        self.logger.info(f"Application initialized in {self._current_state} state")

    @property
    def current_state(self):
        """Get the current application state."""
        return self._current_state

    def set_state(self, new_state):
        """
        Change the application state if the transition is valid.

        Args:
            new_state: The new state to transition to

        Returns:
            bool: Whether the state transition was successful
        """
        # Define valid state transitions
        valid_transitions = {
            AppState.IDLE: [AppState.RECORDING, AppState.PLAYING, AppState.SIMULATING],
            AppState.RECORDING: [AppState.IDLE, AppState.RECORDING_PAUSED],
            AppState.RECORDING_PAUSED: [AppState.RECORDING, AppState.IDLE],
            AppState.PLAYING: [AppState.IDLE],
            AppState.SIMULATING: [AppState.IDLE],
        }

        # Check if the transition is valid
        if new_state not in valid_transitions.get(self._current_state, []):
            self.logger.warning(
                f"Invalid state transition: {self._current_state} -> {new_state}"
            )
            return False

        # Perform the transition
        old_state = self._current_state
        self._current_state = new_state
        self.logger.debug(f"State changed: {old_state} -> {new_state}")

        # Notify callback if it exists
        if self._state_change_callback:
            self._state_change_callback(old_state, new_state)

        return True

    def is_recording(self):
        """Check if the application is in any recording state."""
        return self._current_state in [AppState.RECORDING, AppState.RECORDING_PAUSED]

    def is_playing(self):
        """Check if the application is in playing state."""
        return self._current_state == AppState.PLAYING

    def is_simulating(self):
        """Check if the application is in simulating state."""
        return self._current_state == AppState.SIMULATING

    def is_active(self):
        """Check if the application is in any active state (not idle)."""
        return self._current_state != AppState.IDLE

    def is_paused(self):
        """Check if the application is in paused state."""
        return self._current_state == AppState.RECORDING_PAUSED
