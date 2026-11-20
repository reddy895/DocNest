import io
import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel

logger = logging.getLogger("docnest.ocr")

HAS_TESSERACT = False
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except Exception:
    HAS_TESSERACT = False


class OCRPageResult(BaseModel):
    page_number: int
    text: str
    confidence_score: float
    is_scanned: bool
    word_count: int
    method_used: str


class OCRService:
    """
    Robust OCR detection and text extraction pipeline for scanned PDF documents.
    Detects sparse character density and processes scanned image layers with confidence metrics.
    """

    SPARSE_TEXT_THRESHOLD_CHARS = 50

    def is_page_likely_scanned(self, text: str, page_has_images: bool = False) -> bool:
        """
        Determine if an extracted PDF page is likely a scan rather than digital text.
        """
        clean_text = text.strip()
        if len(clean_text) < self.SPARSE_TEXT_THRESHOLD_CHARS:
            return True
        # Check ratio of readable alphabetical characters
        alpha_chars = sum(c.isalpha() for c in clean_text)
        if len(clean_text) > 0 and (alpha_chars / len(clean_text)) < 0.40:
            return True
        return False

    def compute_heuristic_confidence(self, text: str) -> float:
        """
        Compute heuristic OCR confidence score between 0.0 and 1.0 based on
        word length distribution, dictionary character ratio, and punctuation sanity.
        """
        if not text.strip():
            return 0.0

        words = text.split()
        if not words:
            return 0.0

        # Heuristic 1: Valid character ratio
        valid_chars = sum(1 for c in text if c.isalnum() or c in " .,;:!?'\"-()\n\t")
        char_ratio = valid_chars / max(len(text), 1)

        # Heuristic 2: Average word length sanity (2 to 12 chars is normal natural language)
        avg_word_len = sum(len(w) for w in words) / len(words)
        word_len_score = 1.0 if (2.5 <= avg_word_len <= 10.0) else 0.6

        # Heuristic 3: Vowel presence in words
        vowel_words = sum(1 for w in words if re.search(r"[aeiouyAEIOUY]", w))
        vowel_ratio = vowel_words / len(words)

        confidence = (char_ratio * 0.4) + (word_len_score * 0.3) + (vowel_ratio * 0.3)
        return round(min(max(confidence, 0.0), 1.0), 3)

    def extract_from_image_bytes(self, image_bytes: bytes, page_number: int = 1) -> OCRPageResult:
        """
        Perform OCR on raw image bytes.
        """
        if not HAS_TESSERACT:
            logger.debug("Tesseract OCR not installed on host; using simulated heuristic fallback.")
            return OCRPageResult(
                page_number=page_number,
                text="",
                confidence_score=0.0,
                is_scanned=True,
                word_count=0,
                method_used="tesseract_unavailable",
            )

        try:
            image = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image).strip()

            confidences = [int(c) for c in data.get("conf", []) if int(c) >= 0]
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else self.compute_heuristic_confidence(text)

            return OCRPageResult(
                page_number=page_number,
                text=text,
                confidence_score=round(avg_conf, 3),
                is_scanned=True,
                word_count=len(text.split()),
                method_used="tesseract_ocr",
            )
        except Exception as e:
            logger.warning(f"OCR execution failed on page {page_number}: {e}")
            return OCRPageResult(
                page_number=page_number,
                text="",
                confidence_score=0.0,
                is_scanned=True,
                word_count=0,
                method_used=f"error_{str(e)[:30]}",
            )

    def process_scanned_pdf_pages(
        self,
        pages_text: List[str],
    ) -> Tuple[bool, float, List[Dict[str, Any]]]:
        """
        Evaluate full document pages for scanned content and return aggregate confidence.
        """
        scanned_count = 0
        confidences = []
        page_details = []

        for idx, text in enumerate(pages_text):
            page_num = idx + 1
            is_scanned = self.is_page_likely_scanned(text)
            conf = self.compute_heuristic_confidence(text)
            if is_scanned:
                scanned_count += 1
            confidences.append(conf)
            page_details.append({
                "page_number": page_num,
                "is_scanned": is_scanned,
                "confidence_score": conf,
            })

        doc_is_scanned = (scanned_count / max(len(pages_text), 1)) >= 0.5
        avg_confidence = round(sum(confidences) / max(len(confidences), 1), 3) if confidences else 1.0

        return doc_is_scanned, avg_confidence, page_details


_ocr_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
