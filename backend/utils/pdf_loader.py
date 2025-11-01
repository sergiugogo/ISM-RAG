from PyPDF2 import PdfReader
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from typing import List, Tuple
import hashlib

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF document. Falls back to OCR (docTR) if no native text found.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content as string
    """
    reader = PdfReader(file_path)
    text = ""

    # Attempt native text extraction first
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"

    # OCR fallback for scanned documents
    if not text.strip():
        print("[INFO] No native text detected. Initiating OCR with docTR...")
        model = ocr_predictor(pretrained=True)
        doc = DocumentFile.from_pdf(file_path)
        result = model(doc)
        text = result.render()
        print("[INFO] OCR extraction completed successfully")

    return text.strip()


def extract_text_by_pages(file_path: str) -> Tuple[List[str], int]:
    """
    Extract text from PDF preserving page boundaries.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Tuple of (list of page texts, total page count)
    """
    reader = PdfReader(file_path)
    pages_text = []
    needs_ocr = False

    # Attempt native text extraction for each page
    for page in reader.pages:
        content = page.extract_text()
        if content and content.strip():
            pages_text.append(content)
        else:
            needs_ocr = True
            pages_text.append("")

    # OCR fallback if no text was extracted
    if needs_ocr and not any(pages_text):
        print("[INFO] No native text detected. Initiating OCR with docTR...")
        model = ocr_predictor(pretrained=True)
        doc = DocumentFile.from_pdf(file_path)
        result = model(doc)
        
        # Extract text from each page in OCR result
        pages_text = []
        for page in result.pages:
            page_text = " ".join([
                " ".join([word.value for word in line.words])
                for block in page.blocks
                for line in block.lines
            ])
            pages_text.append(page_text)
        
        print("[INFO] OCR extraction completed successfully")

    return pages_text, len(pages_text)


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file for change detection.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for memory efficiency
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
