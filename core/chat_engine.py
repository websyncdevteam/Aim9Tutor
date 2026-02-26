# core/chat_engine.py

import logging
from typing import List, Tuple, Optional
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatEngine:
    """
    Gemini AI chat engine with model fallback (no recursion).
    """

    # Updated models based on your available list
    FALLBACK_MODELS = [
        settings.GEMINI_MODEL,
        "gemini-2.0-flash-001",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash-lite",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env")

        self.client = genai.Client(api_key=self.api_key)
        self.current_model = None
        self.system_prompt = ""
        self.chat = None
        self.class_level = None  # will be set in set_system_prompt
        logger.info("ChatEngine initialized")

    def set_system_prompt(self, class_level: int, language: str, competitive_mode: bool = False):
        """Create a system prompt and store class level."""
        self.class_level = class_level  # ✅ FIX: store class level
        base = f"""You are a friendly Indian school teacher teaching Class {class_level}.
Explain concepts clearly. Use small sentences for lower classes. Encourage the student.
Never go outside the uploaded content unless competitive mode is enabled.
If language is Hinglish or Bhojpuri, adapt your style naturally. Do not hallucinate.
Always respond in the language specified: {language}."""
        if competitive_mode:
            base += " You may occasionally include additional examples or comparisons to similar topics outside the text to enhance understanding."
        else:
            base += " Strictly use only the information from the uploaded PDF."
        self.system_prompt = base

    def start_chat(self, model: str) -> bool:
        """Try to start chat with given model. Returns True if success."""
        try:
            self.chat = self.client.chats.create(
                model=model,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            self.current_model = model
            logger.info(f"Chat started with model: {model}")
            return True
        except (ClientError, ServerError) as e:
            logger.warning(f"Model {model} failed: {e}")
            return False

    def send_message(self, message: str, context_chunks: Optional[List[str]] = None) -> Tuple[str, int, int]:
        """
        Send message, trying each model in order until one works.
        Returns (response_text, approx_input_tokens, approx_output_tokens).
        """
        # Build full message with context
        full_message = message
        if context_chunks:
            context_text = "\n\n---\n\n".join(context_chunks)
            full_message = f"Context from chapter:\n{context_text}\n\nQuestion: {message}"

        # Try models one by one
        last_error = None
        for model in self.FALLBACK_MODELS:
            # If chat already exists and uses a different model, we need to restart
            if self.chat is None or self.current_model != model:
                if not self.start_chat(model):
                    continue  # try next model

            # Now try to send message with this model
            try:
                response = self.chat.send_message(full_message)
                answer = response.text if hasattr(response, 'text') else str(response)
                input_tokens = int(len(full_message.split()) * 1.3)
                output_tokens = int(len(answer.split()) * 1.3)
                return answer, input_tokens, output_tokens
            except (ClientError, ServerError) as e:
                logger.warning(f"Message sending failed with model {model}: {e}")
                last_error = e
                # Mark chat as dead, will try next model
                self.chat = None
                continue

        # If all models fail
        logger.error("All models failed. Last error: %s", last_error)
        raise RuntimeError("Unable to process message with any available model.") from last_error

    def get_history(self):
        if self.chat:
            try:
                return self.chat.get_history()
            except Exception:
                return []
        return []