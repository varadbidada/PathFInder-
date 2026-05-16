"""
nlp/sentiment/analyzer.py — Sentiment Analysis for Student Answers and Social Media

Provides sentiment analysis with:
- Transformer-based models (if available)
- VADER fallback
- Domain-specific lexicon with negation handling
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Try to import transformers (HuggingFace) ──────────────────────────────────
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library available for sentiment analysis")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.info("Transformers not available, will use VADER/lexicon fallback")

# ── Try to import VADER ───────────────────────────────────────────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as VaderAnalyzer
    VADER_AVAILABLE = True
    logger.info("VADER sentiment analyzer available")
except ImportError:
    VADER_AVAILABLE = False
    logger.info("VADER not available, will use lexicon-only fallback")


class SentimentAnalyzer:
    """
    Multi-strategy sentiment analyzer with domain-specific lexicon support.
    
    Strategy priority:
    1. Transformers (distilbert-base-uncased-finetuned-sst-2-english)
    2. VADER
    3. Domain lexicon with negation handling
    """
    
    def __init__(self):
        self.transformer_model: Optional[object] = None
        self.vader_analyzer: Optional[VaderAnalyzer] = None
        self.domain_lexicon: dict = {}
        
        # Load domain lexicon
        self._load_domain_lexicon()
        
        # Initialize transformer model (lazy loading)
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight sentiment model
                self.transformer_model = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1  # CPU only
                )
                logger.info("Loaded transformer sentiment model")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
                self.transformer_model = None
        
        # Initialize VADER
        if VADER_AVAILABLE:
            self.vader_analyzer = VaderAnalyzer()
            logger.info("Initialized VADER sentiment analyzer")
    
    def _load_domain_lexicon(self):
        """Load domain-specific lexicon from JSON file."""
        lexicon_path = Path(__file__).parent / "domain_lexicon.json"
        try:
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                self.domain_lexicon = json.load(f)
            logger.info(f"Loaded domain lexicon with {len(self.domain_lexicon.get('positive', []))} positive and {len(self.domain_lexicon.get('negative', []))} negative terms")
        except Exception as e:
            logger.error(f"Failed to load domain lexicon: {e}")
            # Fallback minimal lexicon
            self.domain_lexicon = {
                "positive": ["love", "enjoy", "good", "great", "excellent"],
                "negative": ["hate", "bad", "terrible", "awful", "poor"],
                "negation_words": ["not", "never", "no", "don't", "can't"]
            }
    
    def analyze(self, text: str) -> dict:
        """
        Analyze sentiment of text using best available method.
        
        Returns:
            {
                "compound": float (-1 to 1),
                "positive": float (0 to 1),
                "negative": float (0 to 1),
                "neutral": float (0 to 1),
                "method": str ("transformer" | "vader" | "lexicon")
            }
        """
        if not text or not text.strip():
            return {
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "method": "empty"
            }
        
        # Try transformer first
        if self.transformer_model:
            try:
                result = self._analyze_with_transformer(text)
                result["method"] = "transformer"
                return result
            except Exception as e:
                logger.debug(f"Transformer analysis failed: {e}")
        
        # Try VADER second
        if self.vader_analyzer:
            try:
                result = self._analyze_with_vader(text)
                result["method"] = "vader"
                return result
            except Exception as e:
                logger.debug(f"VADER analysis failed: {e}")
        
        # Fallback to lexicon
        result = self._analyze_with_lexicon(text)
        result["method"] = "lexicon"
        return result
    
    def _analyze_with_transformer(self, text: str) -> dict:
        """Analyze using HuggingFace transformer model."""
        # Truncate to 512 tokens (BERT limit)
        text_truncated = text[:2000]
        
        result = self.transformer_model(text_truncated)[0]
        label = result['label']  # POSITIVE or NEGATIVE
        score = result['score']  # confidence 0-1
        
        if label == 'POSITIVE':
            compound = score
            positive = score
            negative = 1 - score
        else:  # NEGATIVE
            compound = -score
            positive = 1 - score
            negative = score
        
        neutral = 1 - abs(compound)
        
        return {
            "compound": round(compound, 4),
            "positive": round(positive, 4),
            "negative": round(negative, 4),
            "neutral": round(neutral, 4)
        }
    
    def _analyze_with_vader(self, text: str) -> dict:
        """Analyze using VADER sentiment analyzer."""
        scores = self.vader_analyzer.polarity_scores(text)
        return {
            "compound": round(scores['compound'], 4),
            "positive": round(scores['pos'], 4),
            "negative": round(scores['neg'], 4),
            "neutral": round(scores['neu'], 4)
        }
    
    def _analyze_with_lexicon(self, text: str) -> dict:
        """
        Analyze using domain-specific lexicon with negation handling.
        
        Negation handling: if a negation word appears within 3 tokens before
        a sentiment word, flip its polarity.
        """
        text_lower = text.lower()
        tokens = re.findall(r'\b\w+\b', text_lower)
        
        positive_words = set(self.domain_lexicon.get('positive', []))
        negative_words = set(self.domain_lexicon.get('negative', []))
        negation_words = set(self.domain_lexicon.get('negation_words', []))
        intensifiers = set(self.domain_lexicon.get('intensifiers', []))
        diminishers = set(self.domain_lexicon.get('diminishers', []))
        
        positive_score = 0.0
        negative_score = 0.0
        
        for i, token in enumerate(tokens):
            # Check for multi-word phrases
            bigram = f"{tokens[i-1]} {token}" if i > 0 else ""
            trigram = f"{tokens[i-2]} {tokens[i-1]} {token}" if i > 1 else ""
            
            # Check if this token or phrase is a sentiment word
            is_positive = (token in positive_words or 
                          bigram in positive_words or 
                          trigram in positive_words)
            is_negative = (token in negative_words or 
                          bigram in negative_words or 
                          trigram in negative_words)
            
            if not (is_positive or is_negative):
                continue
            
            # Check for negation in previous 3 tokens
            negated = False
            for j in range(max(0, i-3), i):
                if tokens[j] in negation_words:
                    negated = True
                    break
            
            # Check for intensifiers/diminishers in previous 2 tokens
            intensity_multiplier = 1.0
            for j in range(max(0, i-2), i):
                if tokens[j] in intensifiers:
                    intensity_multiplier = 1.5
                    break
                elif tokens[j] in diminishers:
                    intensity_multiplier = 0.5
                    break
            
            # Apply sentiment with negation and intensity
            if is_positive:
                if negated:
                    negative_score += 1.0 * intensity_multiplier
                else:
                    positive_score += 1.0 * intensity_multiplier
            elif is_negative:
                if negated:
                    positive_score += 1.0 * intensity_multiplier
                else:
                    negative_score += 1.0 * intensity_multiplier
        
        # Normalize scores
        total = positive_score + negative_score
        if total == 0:
            return {
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0
            }
        
        positive_norm = positive_score / total
        negative_norm = negative_score / total
        compound = (positive_score - negative_score) / max(total, 1.0)
        
        # Clamp compound to [-1, 1]
        compound = max(-1.0, min(1.0, compound))
        
        return {
            "compound": round(compound, 4),
            "positive": round(positive_norm, 4),
            "negative": round(negative_norm, 4),
            "neutral": round(1.0 - positive_norm - negative_norm, 4)
        }
    
    def analyze_with_context(self, text: str, context: str = "") -> dict:
        """
        Analyze sentiment with additional context.
        Useful for understanding domain-specific sentiment.
        """
        combined_text = f"{context} {text}" if context else text
        return self.analyze(combined_text)


# ── Singleton instance ────────────────────────────────────────────────────────
_analyzer_instance: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create singleton sentiment analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer()
    return _analyzer_instance
