from .whisper_streaming_package import WhisperStreamingPackage
from .realtime_stt import RealtimeSTT
from utils.config import ASR_CONFIG, TRANSCRIPTION_PACKAGE


def api_backend_factory(args=ASR_CONFIG, backend=TRANSCRIPTION_PACKAGE):
    if backend == "whisper_streaming":
        return WhisperStreamingPackage(args)
    elif backend == "realtime_stt":
        return RealtimeSTT(args)
    else:
        raise ValueError(f"Unsupported backend: {backend}")
