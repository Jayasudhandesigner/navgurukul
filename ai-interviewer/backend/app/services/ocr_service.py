import easyocr
import logging
import numpy as np
import cv2
import imagehash
from PIL import Image
import io

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self, languages=['en'], gpu=False):
        logger.info(f"Loading EasyOCR model (GPU={gpu})...")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        self.last_frame_hash = None
        self.hash_threshold = 5  # Difference threshold for pHash
        logger.info("EasyOCR model loaded.")

    def _compute_hash(self, image: Image.Image):
        return imagehash.phash(image)

    def is_duplicate(self, image_bytes: bytes) -> bool:
        """
        Checks if the current frame is significantly different from the last processed one.
        Returns True if it's a duplicate (or similar enough to skip).
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            current_hash = self._compute_hash(image)
            
            if self.last_frame_hash is None:
                self.last_frame_hash = current_hash
                return False # First frame is never duplicate
            
            diff = current_hash - self.last_frame_hash
            if diff < self.hash_threshold:
                return True # Duplicate
            
            self.last_frame_hash = current_hash
            return False
            
        except Exception as e:
            logger.error(f"Error in duplicate check: {e}")
            return False # Process if unsure

    def extract_text(self, image_bytes: bytes) -> str:
        """
        Extracts text from image bytes.
        Returns a single string of combined text.
        """
        try:
            if self.is_duplicate(image_bytes):
                logger.info("Skipping duplicate frame for OCR.")
                return ""

            # Convert bytes to numpy for OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Optimization: Resize if too large (e.g. > 1000px width)
            height, width = img.shape[:2]
            if width > 1000:
                scale = 1000 / width
                img = cv2.resize(img, (1000, int(height * scale)))

            # Optimization: Grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # EasyOCR expects bytes or numpy array
            # detail=0 returns just the list of strings
            result = self.reader.readtext(gray, detail=0, paragraph=True)
            
            # Result is just a list of strings now
            full_text = "\n".join(result)
            
            if full_text.strip():
                logger.info(f"OCR Extracted: {full_text[:50]}...")
            
            return full_text
            if full_text.strip():
                logger.info(f"OCR Extracted: {full_text[:50]}...")
            
            return full_text
            
        except Exception as e:
            logger.error(f"OCR Extraction error: {e}")
            return ""

# Global instance
# Set gpu=True if CUDA is available, else False
ocr_engine = OCRService(gpu=False)
