import io
import pytesseract
from PIL import Image
from pypdf import PdfReader
from docx import Document

# --- CONFIGURATION ---
# POINT THIS TO YOUR TESSERACT INSTALLATION FOLDER
# If you installed it in the default location, this path is correct.
# If you installed it somewhere else, change this line!
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

async def parse_file(file_content: bytes, filename: str) -> dict:
    """
    Determines file type and extracts text accordingly.
    Supports: PDF, DOCX, PNG, JPG, JPEG
    """
    ext = filename.split('.')[-1].lower()
    text = ""
    file_type = "text"

    print(f"⚙️ Parsing file type: {ext}")

    try:
        # 1. Handle PDF
        if ext == 'pdf':
            reader = PdfReader(io.BytesIO(file_content))
            for page in reader.pages:
                text += page.extract_text() or ""
            
            # Fallback: If PDF is an image scan (empty text), warn user
            if len(text.strip()) < 50:
                print("⚠️ PDF seems to be an image scan. Text extraction might be poor.")
                text += "\n[NOTE: Scanned PDF detected. Text extraction may be incomplete.]"

        # 2. Handle DOCX
        elif ext in ['docx', 'doc']:
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([para.text for para in doc.paragraphs])

        # 3. Handle IMAGES (OCR Feature)
        elif ext in ['jpg', 'jpeg', 'png', 'webp']:
            print("📸 Image detected! Running OCR (X-Ray Vision)...")
            image = Image.open(io.BytesIO(file_content))
            # This line converts image pixels to words
            text = pytesseract.image_to_string(image)
            file_type = "image_ocr"

        # 4. Handle Plain Text
        elif ext == 'txt':
            text = file_content.decode('utf-8')

        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return {
            "type": file_type, 
            "content": text.strip()
        }

    except Exception as e:
        print(f"❌ Parser Error: {e}")
        # Friendly error for Tesseract not found
        if "tesseract is not installed" in str(e).lower() or "find the file" in str(e).lower():
            raise ValueError("Server Configuration Error: Tesseract OCR is not found. Please verify the path in parser.py.")
        raise ValueError(f"Failed to read file: {str(e)}")