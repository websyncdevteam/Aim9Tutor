# Manage session progress and flow
class ProgressManager:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.current_mode = None
        self.current_section_index = 0
        self.quiz_score = 0
        self.quiz_questions_answered = 0
        self.chapter_loaded = False
        self.pdf_name = None
    
    def set_mode(self, mode):
        self.current_mode = mode
    
    def next_section(self):
        self.current_section_index += 1
    
    def record_quiz_result(self, correct: bool):
        self.quiz_questions_answered += 1
        if correct:
            self.quiz_score += 1
    
    def get_quiz_progress(self):
        return self.quiz_questions_answered, self.quiz_score
    
    def load_chapter(self, pdf_name):
        self.pdf_name = pdf_name
        self.chapter_loaded = True
        self.reset()  # fresh start for new chapter