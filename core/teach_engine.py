# Structured teaching logic
from typing import List, Dict
import re

class TeachEngine:
    def __init__(self, chat_engine, vector_store):
        self.chat = chat_engine
        self.vector_store = vector_store
        self.sections = []
        self.current_section_index = 0
    
    def generate_sections(self, chapter_text: str):
        """Use Gemini to split chapter into logical sections."""
        # Simple approach: ask Gemini to outline the chapter
        prompt = f"""You are a teacher. Break this chapter into 3-5 logical teaching sections. 
Each section should have a title and brief description. Output as a numbered list.
Chapter: {chapter_text[:2000]}..."""  # truncate to avoid token limits
        response, _, _ = self.chat.send_message(prompt)
        
        # Parse response into sections
        sections = []
        lines = response.strip().split('\n')
        for line in lines:
            if re.match(r'^\d+\.', line):
                # Extract title (remove number and period)
                title = re.sub(r'^\d+\.\s*', '', line).strip()
                sections.append({"title": title, "explained": False})
        if not sections:
            # Fallback: create generic sections
            sections = [{"title": "Introduction", "explained": False},
                        {"title": "Main Concepts", "explained": False},
                        {"title": "Summary", "explained": False}]
        self.sections = sections
        return sections
    
    def get_current_section(self):
        if self.current_section_index < len(self.sections):
            return self.sections[self.current_section_index]
        return None
    
    def teach_section(self, section_title: str) -> str:
        """Generate teaching content for a section using context from PDF."""
        # Retrieve relevant chunks for this section title
        context = self.vector_store.retrieve_context(section_title, n_results=2)
        prompt = f"Teach the section '{section_title}' in a simple, engaging way suitable for Class {self.chat.class_level}. Use examples."
        response, _, _ = self.chat.send_message(prompt, context_chunks=context)
        # Mark section as explained
        for s in self.sections:
            if s['title'] == section_title:
                s['explained'] = True
                break
        return response
    
    def next_section(self):
        self.current_section_index += 1
        return self.get_current_section()
    
    def generate_recap(self) -> str:
        """Summarize all explained sections."""
        explained_titles = [s['title'] for s in self.sections if s['explained']]
        if not explained_titles:
            return "We haven't covered any section yet."
        prompt = f"Give a quick recap of these sections: {', '.join(explained_titles)}. Keep it brief and encouraging."
        response, _, _ = self.chat.send_message(prompt)
        return response