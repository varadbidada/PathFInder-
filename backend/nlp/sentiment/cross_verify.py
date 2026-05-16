"""
nlp/sentiment/cross_verify.py — Cross-Verification Engine for Social Media Content

Analyzes sentiment across multiple posts/comments to detect:
- Consensus sentiment (positive/mixed/negative)
- Confidence level (high/medium/low)
- Outlier posts that should be removed
"""
from __future__ import annotations

import logging
import statistics
from typing import Literal

logger = logging.getLogger(__name__)


class CrossVerificationEngine:
    """
    Cross-verifies sentiment across multiple social media posts/comments.
    
    Removes outliers and computes consensus sentiment with confidence level.
    """
    
    def __init__(self):
        self.outlier_threshold = 1.5  # Standard deviations from mean
        self.high_confidence_threshold = 0.3  # std < 0.3 = high confidence
        self.low_confidence_threshold = 0.5   # std > 0.5 = low confidence
    
    def verify(
        self,
        sentiment_scores: list[float],
        texts: list[str] = None
    ) -> dict:
        """
        Cross-verify sentiment scores from multiple sources.
        
        Args:
            sentiment_scores: List of compound sentiment scores (-1 to 1)
            texts: Optional list of corresponding text snippets
        
        Returns:
            {
                "consensus_sentiment": "positive" | "mixed" | "negative",
                "confidence": "high" | "medium" | "low",
                "mean_sentiment": float,
                "std_deviation": float,
                "outliers_removed": int,
                "outlier_indices": list[int],
                "cleaned_scores": list[float],
                "note": str (optional warning message)
            }
        """
        if not sentiment_scores:
            return {
                "consensus_sentiment": "neutral",
                "confidence": "low",
                "mean_sentiment": 0.0,
                "std_deviation": 0.0,
                "outliers_removed": 0,
                "outlier_indices": [],
                "cleaned_scores": [],
                "note": "No sentiment data available"
            }
        
        if len(sentiment_scores) == 1:
            return {
                "consensus_sentiment": self._classify_sentiment(sentiment_scores[0]),
                "confidence": "low",
                "mean_sentiment": sentiment_scores[0],
                "std_deviation": 0.0,
                "outliers_removed": 0,
                "outlier_indices": [],
                "cleaned_scores": sentiment_scores,
                "note": "Only one data point — low confidence"
            }
        
        # Calculate initial statistics
        mean_sentiment = statistics.mean(sentiment_scores)
        std_deviation = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
        
        # Detect outliers
        outlier_indices = []
        cleaned_scores = []
        
        for i, score in enumerate(sentiment_scores):
            deviation = abs(score - mean_sentiment)
            if deviation > self.outlier_threshold * std_deviation:
                outlier_indices.append(i)
                logger.info(f"Detected outlier sentiment: {score:.2f} (mean: {mean_sentiment:.2f}, std: {std_deviation:.2f})")
            else:
                cleaned_scores.append(score)
        
        # Recalculate statistics after removing outliers
        if cleaned_scores:
            mean_sentiment = statistics.mean(cleaned_scores)
            std_deviation = statistics.stdev(cleaned_scores) if len(cleaned_scores) > 1 else 0.0
        else:
            # All were outliers — keep original
            cleaned_scores = sentiment_scores
            outlier_indices = []
        
        # Classify consensus sentiment
        consensus = self._classify_sentiment(mean_sentiment)
        
        # Determine confidence level
        confidence = self._determine_confidence(std_deviation, len(cleaned_scores))
        
        # Generate note if needed
        note = None
        if std_deviation > self.low_confidence_threshold:
            note = "Highly mixed opinions found — sentiment varies significantly across sources"
        elif len(outlier_indices) > 0:
            note = f"Removed {len(outlier_indices)} outlier post(s) with extreme sentiment"
        
        result = {
            "consensus_sentiment": consensus,
            "confidence": confidence,
            "mean_sentiment": round(mean_sentiment, 4),
            "std_deviation": round(std_deviation, 4),
            "outliers_removed": len(outlier_indices),
            "outlier_indices": outlier_indices,
            "cleaned_scores": [round(s, 4) for s in cleaned_scores]
        }
        
        if note:
            result["note"] = note
        
        return result
    
    def _classify_sentiment(self, score: float) -> Literal["positive", "mixed", "negative"]:
        """Classify a sentiment score into positive/mixed/negative."""
        if score > 0.2:
            return "positive"
        elif score < -0.2:
            return "negative"
        else:
            return "mixed"
    
    def _determine_confidence(
        self,
        std_deviation: float,
        sample_size: int
    ) -> Literal["high", "medium", "low"]:
        """
        Determine confidence level based on std deviation and sample size.
        
        Rules:
        - High: std < 0.3 AND sample_size >= 3
        - Low: std > 0.5 OR sample_size < 2
        - Medium: everything else
        """
        if sample_size < 2:
            return "low"
        
        if std_deviation < self.high_confidence_threshold and sample_size >= 3:
            return "high"
        elif std_deviation > self.low_confidence_threshold:
            return "low"
        else:
            return "medium"
    
    def filter_outliers(
        self,
        sentiment_scores: list[float],
        texts: list[str]
    ) -> tuple[list[float], list[str]]:
        """
        Filter out outlier posts and return cleaned lists.
        
        Returns:
            (cleaned_scores, cleaned_texts)
        """
        if len(sentiment_scores) != len(texts):
            logger.warning("Sentiment scores and texts length mismatch")
            return sentiment_scores, texts
        
        result = self.verify(sentiment_scores, texts)
        outlier_indices = set(result["outlier_indices"])
        
        cleaned_scores = [
            score for i, score in enumerate(sentiment_scores)
            if i not in outlier_indices
        ]
        cleaned_texts = [
            text for i, text in enumerate(texts)
            if i not in outlier_indices
        ]
        
        return cleaned_scores, cleaned_texts


# ── Singleton instance ────────────────────────────────────────────────────────
_engine_instance: Optional[CrossVerificationEngine] = None


def get_cross_verification_engine() -> CrossVerificationEngine:
    """Get or create singleton cross-verification engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = CrossVerificationEngine()
    return _engine_instance
