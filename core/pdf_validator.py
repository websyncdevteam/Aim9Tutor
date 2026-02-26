# Validate PDF and restrict to Class 1-9
import re
import PyPDF2
from pathlib import Path
from config import settings

class PDFValidationError(Exception):
    pass

def validate_pdf(file_path: Path):
    """Validate PDF file."""
    # Check file extension
    if file_path.suffix.lower() != '.pdf':
        raise PDFValidationError("File is not a PDF.")
    
    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.MAX_PDF_SIZE_MB:
        raise PDFValidationError(f"PDF exceeds {settings.MAX_PDF_SIZE_MB}MB limit.")
    
    # Try to read first few pages to check if PDF is readable and extract class info
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) == 0:
                raise PDFValidationError("PDF has no pages.")
            
            # Extract text from first 3 pages to detect class
            preview_text = ""
            for i in range(min(3, len(reader.pages))):
                page = reader.pages[i]
                preview_text += page.extract_text() or ""
            
            # Look for class indicators
            class_pattern = r'(?:class|grade|std\.?)\s*(\d{1,2})'
            matches = re.findall(class_pattern, preview_text, re.IGNORECASE)
            if matches:
                # Convert to int and check if any is >9
                for m in matches:
                    try:
                        class_num = int(m)
                        if class_num > 9:
                            raise PDFValidationError(f"Detected Class {class_num}. Only Classes 1-9 are allowed.")
                    except ValueError:
                        pass
    except Exception as e:
        raise PDFValidationError(f"Error reading PDF: {e}")
    
    return preview_text[:1000]  # return preview