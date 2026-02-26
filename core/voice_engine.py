# core/voice_engine.py

from google.cloud import texttospeech
import uuid
from pathlib import Path
from config import settings

class VoiceEngine:
    """
    Text-to-Speech engine using API key authentication.
    """
    def __init__(self, api_key: str = None):
        """
        Initialize the TTS client with API key.
        If no key provided, tries to get from settings.
        """
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google API key is required for TTS. Set GOOGLE_API_KEY in .env")

        # Initialize client with API key
        self.client = texttospeech.TextToSpeechClient(
            client_options={"api_key": self.api_key}
        )
        self.audio_dir = Path("assets/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, text: str, language: str, gender: str = "female", class_level: int = 5) -> tuple[Path, int]:
        """Generate speech and return (file_path, character_count)."""
        # Map language to Google TTS language code
        lang_map = {
            "en": "en-IN",
            "hi": "hi-IN",
            "hi-en": "hi-IN",   # Hinglish uses Hindi voice
            "bho": "hi-IN"       # Bhojpuri use Hindi voice
        }
        language_code = lang_map.get(language, "en-IN")

        # Select voice based on gender
        if gender.lower() == "male":
            voice_name = "hi-IN-Standard-A" if language_code == "hi-IN" else "en-IN-Standard-A"
        else:
            voice_name = "hi-IN-Standard-B" if language_code == "hi-IN" else "en-IN-Standard-B"

        # Adjust speaking rate for lower classes
        speaking_rate = 0.9 if class_level <= 5 else 1.0

        # Build request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE if gender.lower() == "female" else texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )

        # Make API call
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Save to file
        filename = f"tts_{uuid.uuid4()}.mp3"
        filepath = self.audio_dir / filename
        with open(filepath, 'wb') as out:
            out.write(response.audio_content)

        return filepath, len(text)