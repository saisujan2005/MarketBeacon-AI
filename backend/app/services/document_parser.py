import io
import re
import logging
import zipfile
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes. Attempts to use `pypdf`,
    falling back to a pure-Python regex stream extractor if unsuccessful.
    """
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        # If reader fails to get text, trigger fallback
        if not text.strip():
            raise Exception("pypdf extracted empty text; attempting fallback parser")
        return text
    except Exception as e:
        logger.warning(f"Standard PDF parser failed, using stream fallback: {e}")
        # Robust PDF Stream Fallback (extracts characters enclosed in parenthesis inside TJ/Tj text operators)
        text_parts = []
        # Match PDF text operators like (text) Tj or [ (text1) 10 (text2) ] TJ
        matches = re.findall(b'\(([^)]+)\)\s*(?:Tj|TJ)', file_bytes)
        if matches:
            for m in matches:
                try:
                    text_parts.append(m.decode('utf-8', errors='ignore'))
                except Exception:
                    pass
        
        result_text = " ".join(text_parts)
        if not result_text.strip():
            # Last resort: extract printable ASCII characters
            result_text = "".join([chr(b) if (32 <= b < 127 or b in (10, 13)) else " " for b in file_bytes])
        
        return result_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from DOCX bytes. Attempts to use `docx` (python-docx),
    falling back to zipfile reading of `word/document.xml`.
    """
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logger.warning(f"python-docx failed, using XML zipfile fallback: {e}")
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as doc_zip:
                xml_content = doc_zip.read('word/document.xml')
                root = ET.fromstring(xml_content)
                
                texts = []
                for elem in root.iter():
                    if elem.tag.endswith('t'):
                        if elem.text:
                            texts.append(elem.text)
                return "\n".join(texts)
        except Exception as ex:
            logger.error(f"XML docx parser fallback failed: {ex}")
            # Failsafe character cleaning
            return "".join([chr(b) if (32 <= b < 127 or b in (10, 13)) else " " for b in file_bytes])


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Decodes direct text file bytes using UTF-8 or Latin-1 encodings.
    """
    try:
        return file_bytes.decode('utf-8')
    except Exception:
        try:
            return file_bytes.decode('latin-1')
        except Exception:
            return "".join([chr(b) if (32 <= b < 127 or b in (10, 13)) else " " for b in file_bytes])


def chunk_text(text: str, chunk_size_tokens: int = 900, overlap_tokens: int = 120) -> list:
    """
    Splits text into chunks of 800-1000 tokens (word-based approximation: 1 token = 0.75 words).
    Ensures safe word boundaries and overlaps.
    """
    # 1 token = 0.75 words.
    # 900 tokens = ~675 words
    # 120 tokens overlap = ~90 words
    words = text.split()
    if not words:
        return []

    chunk_size_words = int(chunk_size_tokens * 0.75)
    overlap_words = int(overlap_tokens * 0.75)

    if chunk_size_words <= 0:
        chunk_size_words = 600
    if overlap_words >= chunk_size_words:
        overlap_words = chunk_size_words // 5

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        
        # Advance window
        start += chunk_size_words - overlap_words

    return chunks
