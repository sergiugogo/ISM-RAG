from PyPDF2 import PdfReader
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extrage text din PDF. Dacă nu există text nativ, folosește OCR (docTR).
    """
    reader = PdfReader(file_path)
    text = ""

    # 1️⃣ Extragere text clasic
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"

    # 2️⃣ OCR fallback doar dacă e necesar
    if not text.strip():
        print("⚠️ Niciun text detectat. Se folosește OCR cu docTR...")
        model = ocr_predictor(pretrained=True)
        doc = DocumentFile.from_pdf(file_path)
        result = model(doc)
        text = result.render()
        print("✅ OCR complet!")

    return text.strip()
