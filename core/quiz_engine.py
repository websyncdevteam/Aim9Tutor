# core/quiz_engine.py

import re
import logging
import random
from typing import List, Dict, Tuple, Optional
from time import sleep

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class QuizEngine:
    """
    Advanced Quiz Engine that never fails.
    Uses fallbacks, retries, and robust parsing.
    """
    def __init__(self, chat_engine, vector_store):
        self.chat = chat_engine
        self.vector_store = vector_store
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.questions_answered = 0
        self.max_retries = 3          # how many times to retry generation

    # ------------------------------------------------------------------
    # Public methods used by app.py
    # ------------------------------------------------------------------
    def generate_questions(self, num_questions: int = 5):
        """
        Generate MCQs. Guaranteed to fill self.questions with at least one question.
        """
        self.questions = self._generate_with_fallback(num_questions)
        self.current_index = 0
        self.score = 0
        self.questions_answered = 0
        logger.info(f"Generated {len(self.questions)} questions.")

    def get_current_question(self) -> Optional[Dict]:
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def check_answer(self, user_choice: str) -> Tuple[bool, str]:
        q = self.get_current_question()
        if not q:
            return False, "No active question."

        correct = q.get('correct', '').strip().upper()
        user_letter = user_choice[0].upper() if user_choice else ''
        is_correct = (user_letter == correct)
        explanation = q.get('explanation', 'No explanation provided.')
        return is_correct, explanation

    def record_quiz_result(self, correct: bool):
        self.questions_answered += 1
        if correct:
            self.score += 1

    def next_question(self):
        self.current_index += 1

    def get_score(self):
        return self.score

    def get_progress(self):
        return self.questions_answered, len(self.questions)

    # ------------------------------------------------------------------
    # Internal advanced generation logic
    # ------------------------------------------------------------------
    def _generate_with_fallback(self, num_questions: int) -> List[Dict]:
        """
        Try multiple strategies to get valid questions.
        Returns a non‑empty list.
        """
        # Strategy 1: normal generation
        for attempt in range(self.max_retries):
            try:
                questions = self._attempt_generation(num_questions, attempt)
                if questions and len(questions) >= 1:
                    return questions
                logger.warning(f"Attempt {attempt+1} produced {len(questions)} questions, retrying...")
            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed: {e}")
            sleep(1)  # brief pause before retry

        # Strategy 2: try with different retrieval query
        try:
            logger.info("Trying alternative retrieval query...")
            questions = self._generate_from_alternative_context(num_questions)
            if questions and len(questions) >= 1:
                return questions
        except Exception as e:
            logger.error(f"Alternative context failed: {e}")

        # Strategy 3: ultimate fallback – hardcoded questions
        logger.warning("Using hardcoded fallback questions.")
        return self._fallback_questions(num_questions)

    def _attempt_generation(self, num_questions: int, attempt: int) -> List[Dict]:
        """
        One attempt at generating questions.
        """
        # Retrieve context
        context = self.vector_store.retrieve_context("main concepts from chapter", n_results=5)
        if not context or all(not c.strip() for c in context):
            context = self.vector_store.retrieve_context("important ideas", n_results=3)
        context_text = "\n".join(context) if context else "No content available."

        # Build a prompt that improves with each attempt
        if attempt == 0:
            prompt = self._build_prompt_normal(context_text, num_questions)
        else:
            prompt = self._build_prompt_detailed(context_text, num_questions, attempt)

        # Call AI
        response, _, _ = self.chat.send_message(prompt)

        # Parse response
        questions = self._parse_questions(response)

        # Validate and filter
        valid = [q for q in questions if self._is_question_valid(q)]
        return valid

    def _build_prompt_normal(self, context: str, n: int) -> str:
        return f"""Based on the following text, create {n} multiple-choice questions to test understanding.
Use simple language suitable for Class {self._get_class_level()}.

Format each question EXACTLY as:

Question: <question text>
Options:
A) <option A>
B) <option B>
C) <option C>
D) <option D>
Correct: <A/B/C/D>
Explanation: <brief explanation>

Text:
{context[:3000]}
"""

    def _build_prompt_detailed(self, context: str, n: int, attempt: int) -> str:
        return f"""You are an expert teacher. Create {n} high-quality multiple-choice questions from the text below.
Make sure each question has a clear correct answer and a helpful explanation.
Avoid trivial or vague questions.

Use this exact format:

Question: ...
Options:
A) ...
B) ...
C) ...
D) ...
Correct: ...
Explanation: ...

Text:
{context[:2500]}

(Attempt {attempt+1} – please follow the format precisely.)
"""

    def _generate_from_alternative_context(self, num_questions: int) -> List[Dict]:
        """
        Try retrieving different chunks and combine them.
        """
        queries = ["summary", "key points", "examples", "definitions"]
        all_chunks = []
        for q in queries:
            chunks = self.vector_store.retrieve_context(q, n_results=2)
            all_chunks.extend(chunks)
        context = "\n\n---\n\n".join(set(all_chunks))  # unique chunks
        if not context:
            return []

        prompt = f"""Using the following excerpts from a chapter, create {num_questions} quiz questions.
Focus on important concepts that a student should remember.

{context[:3500]}
"""
        response, _, _ = self.chat.send_message(prompt)
        return self._parse_questions(response)

    def _parse_questions(self, text: str) -> List[Dict]:
        """
        Robust parser for the AI response.
        Handles slight formatting variations.
        """
        questions = []
        # Split by "Question:" (case‑insensitive)
        blocks = re.split(r'(?i)\bQuestion:\s*', text)
        for block in blocks[1:]:  # first block is before first "Question:"
            q = {}
            lines = block.strip().split('\n')
            # First line might be the question text
            if lines:
                q['question'] = lines[0].strip()
            # Find options
            options = []
            for line in lines:
                ul = line.strip().upper()
                if re.match(r'^[A-D]\)', line.strip()):
                    options.append(line.strip())
                elif 'OPTION' in ul or 'OPTIONS' in ul:
                    continue  # skip headers
            if len(options) == 4:
                q['options'] = options
            # Find correct answer
            for line in lines:
                if 'CORRECT:' in line.upper():
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        q['correct'] = parts[1].strip().upper()
                    break
            # Find explanation
            for line in lines:
                if 'EXPLANATION:' in line.upper():
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        q['explanation'] = parts[1].strip()
                    break
            # Validate minimal fields
            if all(k in q for k in ('question', 'options', 'correct')):
                q.setdefault('explanation', 'No explanation provided.')
                questions.append(q)
        return questions

    def _is_question_valid(self, q: Dict) -> bool:
        """Check if a question object has all needed fields."""
        required = {'question', 'options', 'correct', 'explanation'}
        if not required.issubset(q.keys()):
            return False
        if not isinstance(q['options'], list) or len(q['options']) != 4:
            return False
        if q['correct'] not in ['A', 'B', 'C', 'D']:
            return False
        return True

    def _fallback_questions(self, n: int) -> List[Dict]:
        """Generate generic fallback questions."""
        fallbacks = []
        topics = ["main idea", "key character", "setting", "author's purpose"]
        for i in range(min(n, len(topics))):
            fallbacks.append({
                'question': f"What is the {topics[i]} of this chapter?",
                'options': ['A) Mathematics', 'B) Science', 'C) History', 'D) Cannot be determined'],
                'correct': 'D',
                'explanation': 'The chapter does not clearly specify this information.'
            })
        # If we still need more, add generic ones
        while len(fallbacks) < n:
            fallbacks.append({
                'question': "Which of the following best summarizes the chapter?",
                'options': ['A) It teaches a concept', 'B) It tells a story', 'C) It gives examples', 'D) Cannot be determined'],
                'correct': 'D',
                'explanation': 'The content is not clear enough to determine.'
            })
        return fallbacks

    def _get_class_level(self) -> int:
        """Safely get class level from chat engine."""
        if hasattr(self.chat, 'class_level') and self.chat.class_level:
            return self.chat.class_level
        return 5  # default