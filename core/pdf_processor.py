# Extract text and split into chunks
import re
import PyPDF2
from pathlib import Path
from typing import List, Dict
from config import settings

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from PDF."""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def clean_text(text: str) -> str:
    """Remove headers, footers, extra whitespace."""
    # Remove page numbers like "- 1 -" or "Page 1"
    text = re.sub(r'[-]*\s*\d+\s*[-]*', '', text)
    # Remove common footer patterns (customize as needed)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if re.match(r'^\s*$', line):  # skip empty lines?
            # keep empty lines? better to collapse multiple empties later
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(line.strip())
    text = '\n'.join(cleaned_lines)
    # Collapse multiple newlines to two max
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def chunk_text(text: str, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> List[Dict]:
    """Split text into overlapping chunks (approximate token count)."""
    # Simple word-based splitting; for production use a tokenizer like tiktoken
    words = text.split()
    chunks = []
    start = 0
    # Estimate tokens: roughly 1.3 tokens per word? We'll use word count for simplicity.
    # Better to use a proper tokenizer but for now we approximate.
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        chunks.append({
            "text": chunk_text,
            "start_word": start,
            "end_word": end
        })
        start += chunk_size - overlap
    return chunks

def process_pdf(file_path: Path) -> List[Dict]:
    """Full pipeline: extract, clean, chunk."""
    raw_text = extract_text_from_pdf(file_path)
    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned)
    return chunks