import logging
import re
from app.core.keywords import TECHNICAL_KEYWORDS

logger = logging.getLogger(__name__)

class ContextEngine:
    def __init__(self):
        self.transcript_history = []  # List of strings
        self.detected_keywords = set()
        self.current_slide_text = ""
        self.detected_topics = set()
        self.raw_transcript = ""
        self.job_description = ""

    def set_job_description(self, text: str):
        self.job_description = text
        logger.info(f"Job Description set ({len(text)} chars)")

    def update_transcript(self, text: str):
        """
        Ingests new transcript segment.
        1. Appends to history.
        2. Scans for keywords.
        """
        self.transcript_history.append(text)
        self.raw_transcript += " " + text
        
        # Simple keyword matching (case-insensitive)
        lower_text = text.lower()
        for kw in TECHNICAL_KEYWORDS:
            if kw in lower_text:
                if kw not in self.detected_keywords:
                    self.detected_keywords.add(kw)
                    logger.info(f"Context Detected Keyword: {kw}")

    def update_visuals(self, text: str):
        """
        Ingests new OCR text.
        1. Updates current slide context.
        2. Heuristic extraction of 'Titles' (e.g. short first lines).
        3. Scans for keywords in visuals too.
        """
        self.current_slide_text = text
        
        # Keyword scan in slide text
        lower_text = text.lower()
        for kw in TECHNICAL_KEYWORDS:
            if kw in lower_text:
                self.detected_keywords.add(kw)
 
        # Simple Heuristic for Topic/Title:
        # Assume the first non-empty line that is short (< 50 chars) is a title candidate
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            potential_title = lines[0]
            if len(potential_title) < 50:
                 self.detected_topics.add(potential_title)
                 logger.info(f"Context Potential Topic: {potential_title}")

    def get_context(self) -> dict:
        """
        Returns structured context summary.
        """
        return {
            "transcript_summary": self.raw_transcript[-1000:], # Last 1000 chars for prompt context
            "keywords": list(self.detected_keywords),
            "current_slide": self.current_slide_text,
            "topics": list(self.detected_topics),
            "job_description": self.job_description
        }

# Global Instance
context_engine = ContextEngine()
