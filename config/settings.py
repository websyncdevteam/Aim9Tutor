# Global configuration settings
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini settings – Use exact model name required by new SDK
GEMINI_MODEL = "gemini-2.0-flash-001"   # or try "gemini-1.5-pro-001" if you need pro
# Alternative model names (uncomment if needed):
# GEMINI_MODEL = "gemini-1.5-flash"
# GEMINI_MODEL = "gemini-1.5-pro"
# GEMINI_MODEL = "gemini-1.5-pro-001"

# Google TTS settings
TTS_LANGUAGE_CODE = "hi-IN"  # default, will be overridden
TTS_VOICE_MALE = "hi-IN-Standard-A"
TTS_VOICE_FEMALE = "hi-IN-Standard-B"

# Budget limits (in INR, approximate)
MAX_COST_INR = 2800
WARNING_THRESHOLD = 0.8  # 80% of max cost

# Token pricing (approximate)
GEMINI_COST_PER_1K_INPUT_TOKENS = 0.00025   # example, adjust based on actual pricing
GEMINI_COST_PER_1K_OUTPUT_TOKENS = 0.0005
TTS_COST_PER_1M_CHARACTERS = 16.00          # Google TTS standard pricing

# PDF upload limit
MAX_PDF_SIZE_MB = 10

# Allowed classes
ALLOWED_CLASSES = list(range(1, 10))  # 1 to 9

# Language options
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Hinglish": "hi-en",
    "Bhojpuri": "bho"
}

# Chunking parameters
CHUNK_SIZE = 700       # tokens
CHUNK_OVERLAP = 100    # tokens

# Vector store settings
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "cbse_knowledge_base"