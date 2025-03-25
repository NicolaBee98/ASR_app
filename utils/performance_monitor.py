"""Performance monitoring for the application."""

import time
from .logging_setup import logger


class PerformanceMonitor:
    """Tracks and reports performance metrics for the application."""

    def __init__(self, update_callback=None, update_interval=2000):
        """
        Initialize the performance monitor.

        Args:
            update_callback: Function to call with performance stats updates
            update_interval: Update interval in milliseconds
        """
        self.update_callback = update_callback
        self.update_interval = update_interval
        self.reset()
        self.is_running = False
        logger.debug("Performance monitor initialized")

    def reset(self):
        """Reset all performance counters."""
        self.stats = {
            "api_calls": 0,
            "api_total_time": 0,
            "frames_processed": 0,
            "ui_updates": 0,
            "start_time": time.time(),
        }

    def start(self):
        """Start performance monitoring."""
        self.is_running = True
        self.reset()
        logger.debug("Performance monitoring started")

    def stop(self):
        """Stop performance monitoring."""
        self.is_running = False
        logger.debug("Performance monitoring stopped")

    def record_api_call(self, duration):
        """
        Record an API call and its duration.

        Args:
            duration: Duration of the API call in seconds
        """
        if not self.is_running:
            return

        self.stats["api_calls"] += 1
        self.stats["api_total_time"] += duration

    def record_frame_processed(self):
        """Record a processed audio frame."""
        if not self.is_running:
            return

        self.stats["frames_processed"] += 1

    def record_ui_update(self):
        """Record a UI update."""
        if not self.is_running:
            return

        self.stats["ui_updates"] += 1

    def get_stats(self):
        """
        Calculate and return current performance statistics.

        Returns:
            Dictionary with calculated performance metrics
        """
        if not self.is_running:
            return {}

        elapsed_time = time.time() - self.stats["start_time"]

        if elapsed_time <= 0:
            return {}

        # Calculate rates
        api_rate = self.stats["api_calls"] / elapsed_time
        frame_rate = self.stats["frames_processed"] / elapsed_time

        # Calculate average API time in milliseconds
        avg_api_time = 0
        if self.stats["api_calls"] > 0:
            avg_api_time = (
                self.stats["api_total_time"] / self.stats["api_calls"]
            ) * 1000

        return {
            "api_rate": api_rate,
            "frame_rate": frame_rate,
            "avg_api_time": avg_api_time,
            "total_api_calls": self.stats["api_calls"],
            "total_frames": self.stats["frames_processed"],
            "total_ui_updates": self.stats["ui_updates"],
            "elapsed_time": elapsed_time,
        }

    def get_stats_text(self):
        """
        Get formatted performance stats text.

        Returns:
            Formatted string with performance metrics
        """
        stats = self.get_stats()
        if not stats:
            return "Performance monitoring inactive"

        return (
            f"API calls/sec: {stats['api_rate']:.1f} | "
            f"Avg API time: {stats['avg_api_time']:.1f}ms | "
            f"Frames/sec: {stats['frame_rate']:.1f}"
        )
