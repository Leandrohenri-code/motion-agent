"""
Audio recording, transcription, and TTS integration.
"""
import os
import wave
import tempfile
from utils.json_streamer import log


class AudioProcessor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def transcribe(self, audio_path: str, provider: str = "openai") -> str:
        """Transcribe audio file to text."""
        log(f"Transcrevendo áudio: {os.path.basename(audio_path)}")
        if provider == "openai":
            return self._transcribe_whisper(audio_path)
        return ""

    def _transcribe_whisper(self, audio_path: str) -> str:
        import httpx
        with open(audio_path, "rb") as f:
            resp = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"model": "whisper-1", "language": "pt"},
                files={"file": (os.path.basename(audio_path), f)},
                timeout=120,
            )
        resp.raise_for_status()
        return resp.json().get("text", "")

    def tts(self, text: str, provider: str = "openai", voice: str = "alloy",
            speed: float = 1.0, api_key: str = None) -> str:
        """Generate TTS audio file. Returns path to generated file."""
        key = api_key or self.api_key
        out_path = tempfile.mktemp(suffix=".mp3")

        if provider == "openai":
            return self._tts_openai(text, voice, speed, key, out_path)
        elif provider == "elevenlabs":
            return self._tts_elevenlabs(text, voice, key, out_path)
        return out_path

    def _tts_openai(self, text: str, voice: str, speed: float, api_key: str, out_path: str) -> str:
        import httpx
        resp = httpx.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "tts-1", "input": text, "voice": voice, "speed": speed},
            timeout=120,
        )
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)
        log(f"Áudio TTS gerado: {out_path}", level="success")
        return out_path

    def _tts_elevenlabs(self, text: str, voice_id: str, api_key: str, out_path: str) -> str:
        import httpx
        vid = voice_id or "21m00Tcm4TlvDq8ikWAM"
        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
            headers={"xi-api-key": api_key},
            json={"text": text, "model_id": "eleven_multilingual_v2"},
            timeout=120,
        )
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return out_path

    def get_audio_duration(self, audio_path: str) -> float:
        """Return audio duration in seconds."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except Exception:
            return 0.0
