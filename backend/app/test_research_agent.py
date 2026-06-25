import unittest
from unittest.mock import patch, MagicMock
from app.services.document_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    chunk_text
)


class TestResearchAgentIngestion(unittest.TestCase):

    def test_txt_extraction(self):
        """Verify TXT decoding logic on standard text files."""
        content = "Standard market intelligence report text."
        file_bytes = content.encode("utf-8")
        extracted = extract_text_from_txt(file_bytes)
        self.assertEqual(extracted, content)

    def test_pdf_extraction_fallback(self):
        """Verify PDF regex stream parser fallback on mock PDF structures."""
        # Simple PDF structure simulation
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Length 20 >>\nstream\n(TCS Earnings Report) Tj\nendstream\nendobj"
        extracted = extract_text_from_pdf(pdf_bytes)
        self.assertIn("TCS Earnings Report", extracted)

    def test_docx_extraction_fallback(self):
        """Verify XML docx parser fallback when python-docx is mocked out."""
        # Mock DOCX format: docx is a zipfile containing word/document.xml
        import io
        import zipfile
        
        docx_buffer = io.BytesIO()
        with zipfile.ZipFile(docx_buffer, "w") as doc_zip:
            doc_zip.writestr(
                "word/document.xml",
                '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Reliance Q4 Analysis</w:t></w:r></w:p></w:body></w:document>'
            )
        
        extracted = extract_text_from_docx(docx_buffer.getvalue())
        self.assertIn("Reliance Q4 Analysis", extracted)

    def test_token_chunking_alignment(self):
        """Verify chunk sizes align with word-based token rules (1 token = 0.75 words)."""
        # Create a text with 1000 words
        words = ["word"] * 1000
        text = " ".join(words)
        
        # 900 tokens = ~675 words
        # 120 tokens overlap = ~90 words
        chunks = chunk_text(text, chunk_size_tokens=900, overlap_tokens=120)
        
        self.assertTrue(len(chunks) > 1)
        # Check first chunk size
        first_chunk_words = len(chunks[0].split())
        self.assertLessEqual(first_chunk_words, 675)
        self.assertGreater(first_chunk_words, 600)


if __name__ == "__main__":
    unittest.main()
