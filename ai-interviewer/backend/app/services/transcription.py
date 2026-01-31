import numpy as np
import logging
from faster_whisper import WhisperModel
import io

logger = logging.getLogger(__name__)

def log_debug(msg):
    with open("debug.log", "a") as f:
        f.write(f"[TRANSCRIPTION] {msg}\n")

class TranscriptionService:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        logger.info(f"Loading Whisper model: {model_size} on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Whisper model loaded.")

    def transcribe_audio(self, audio_data: bytes) -> str:
        """
        Transcribes raw audio bytes.
        Expects audio_data to be typical WAV or raw PCM compatible with Whisper.
        For raw PCM, we might need to wrap in WAV container or use np.frombuffer.
        Assuming incoming is a valid audio file buffer for now (webm/wav).
        """
        try:
            # print(f"DEBUG: Transcribing {len(audio_data)} bytes...", flush=True) 
            # (Commented out size to avoid spam, but enabled if needed)
            
            # Create a file-like object
            audio_file = io.BytesIO(audio_data)
            
            segments, info = self.model.transcribe(
                audio_file, 
                beam_size=5, 
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            text = " ".join([segment.text for segment in segments])
            if text:
                log_debug(f"Result: '{text}'")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            log_debug(f"Exception: {e}")
            return ""

# Global instance
# Using 'tiny' or 'base' for CPU performance during dev
transcriber = TranscriptionService(model_size="base") 
