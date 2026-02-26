# Track token and TTS usage
from config import settings
import time

class UsageTracker:
    def __init__(self):
        self.total_gemini_input_tokens = 0
        self.total_gemini_output_tokens = 0
        self.total_tts_characters = 0
        self.daily_reset_time = time.time()
    
    def add_gemini_usage(self, input_tokens: int, output_tokens: int):
        self.total_gemini_input_tokens += input_tokens
        self.total_gemini_output_tokens += output_tokens
    
    def add_tts_usage(self, characters: int):
        self.total_tts_characters += characters
    
    def calculate_cost(self):
        gemini_cost = (self.total_gemini_input_tokens / 1000) * settings.GEMINI_COST_PER_1K_INPUT_TOKENS
        gemini_cost += (self.total_gemini_output_tokens / 1000) * settings.GEMINI_COST_PER_1K_OUTPUT_TOKENS
        tts_cost = (self.total_tts_characters / 1_000_000) * settings.TTS_COST_PER_1M_CHARACTERS
        return gemini_cost + tts_cost
    
    def budget_warning(self):
        cost = self.calculate_cost()
        return cost >= settings.MAX_COST_INR * settings.WARNING_THRESHOLD
    
    def budget_exceeded(self):
        return self.calculate_cost() >= settings.MAX_COST_INR
    
    def get_stats(self):
        return {
            "input_tokens": self.total_gemini_input_tokens,
            "output_tokens": self.total_gemini_output_tokens,
            "tts_chars": self.total_tts_characters,
            "estimated_cost": self.calculate_cost()
        }