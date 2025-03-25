"""Utilities for audio file operations."""

import wave
import pyaudio
import tempfile
from pydub import AudioSegment
from .logging_setup import logger
from .config import AUDIO_CONFIG


def convert_to_wav(file_path):
    """
    Convert any audio file to WAV format with standard parameters.

    Args:
        file_path: Path to the source audio file

    Returns:
        Path to the converted temporary WAV file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()

        # Convert the file
        logger.info(f"Converting {file_path} to WAV format")
        audio = AudioSegment.from_file(file_path)

        # Normalize audio parameters
        audio = (
            audio.set_frame_rate(AUDIO_CONFIG["rate"])
            .set_channels(AUDIO_CONFIG["channels"])
            .set_sample_width(2)  # 16-bit PCM
        )

        # Export to the temporary file
        audio.export(temp_path, format="wav")
        logger.info(f"Converted audio saved to {temp_path}")

        return temp_path

    except Exception as e:
        logger.error(f"Error converting audio file: {str(e)}")
        raise


def save_recording(frames, file_path):
    """
    Save recorded audio frames to a WAV file.

    Args:
        frames: List of audio data frames
        file_path: Path where to save the WAV file
    """
    try:
        logger.info(f"Saving recording to {file_path}")
        p = pyaudio.PyAudio()

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(AUDIO_CONFIG["channels"])
            wf.setsampwidth(p.get_sample_size(AUDIO_CONFIG["format"]))
            wf.setframerate(AUDIO_CONFIG["rate"])
            wf.writeframes(b"".join(frames))

        p.terminate()
        logger.info(f"Recording saved successfully to {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving recording: {str(e)}")
        return False
