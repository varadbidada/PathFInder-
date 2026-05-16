"""
services/feedback_service.py — User Feedback Collection & Learning

Collects user feedback on branch recommendations and uses it to improve
future predictions. Stores anonymized data for model improvement.
"""
from __future__ import annotations
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "user_feedback.db"


@dataclass
class FeedbackEntry:
    """User feedback on a branch recommendation"""
    session_id: str
    predicted_branch: str
    user_accepted: bool  # True if user agreed, False if they chose different
    user_preferred_branch: Optional[str]  # If they disagreed, what did they want?
    signals: Dict[str, float]  # The signals that led to the prediction
    confidence: float
    timestamp: datetime


class FeedbackService:
    """Manages user feedback collection and learning"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize the feedback database"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                predicted_branch TEXT NOT NULL,
                user_accepted INTEGER NOT NULL,
                user_preferred_branch TEXT,
                signals_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predicted_branch 
            ON feedback(predicted_branch)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_accepted 
            ON feedback(user_accepted)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Feedback database initialized at {DB_PATH}")
    
    def record_feedback(
        self,
        session_id: str,
        predicted_branch: str,
        user_accepted: bool,
        user_preferred_branch: Optional[str],
        signals: Dict[str, float],
        confidence: float,
    ) -> None:
        """Record user feedback on a branch recommendation"""
        import json
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback (
                session_id, predicted_branch, user_accepted, 
                user_preferred_branch, signals_json, confidence, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            predicted_branch,
            1 if user_accepted else 0,
            user_preferred_branch,
            json.dumps(signals),
            confidence,
            datetime.utcnow().isoformat(),
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(
            f"Feedback recorded: {predicted_branch} "
            f"{'accepted' if user_accepted else f'rejected for {user_preferred_branch}'}"
        )
    
    def get_acceptance_rate(self, branch: str) -> float:
        """Get the acceptance rate for a specific branch prediction"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(user_accepted) as accepted
            FROM feedback
            WHERE predicted_branch = ?
        """, (branch,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or row[0] == 0:
            return 0.5  # Default 50% if no data
        
        total, accepted = row
        return accepted / total
    
    def get_confusion_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Get confusion matrix: predicted branch → actual user choice.
        Returns: {predicted: {actual: count}}
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                predicted_branch,
                COALESCE(user_preferred_branch, predicted_branch) as actual_branch,
                COUNT(*) as count
            FROM feedback
            GROUP BY predicted_branch, actual_branch
        """)
        
        matrix: Dict[str, Dict[str, int]] = {}
        for predicted, actual, count in cursor.fetchall():
            if predicted not in matrix:
                matrix[predicted] = {}
            matrix[predicted][actual] = count
        
        conn.close()
        return matrix
    
    def get_signal_patterns(self, branch: str, accepted_only: bool = True) -> List[Dict[str, float]]:
        """
        Get signal patterns for users who chose a specific branch.
        Useful for understanding what signals correlate with each branch.
        
        Args:
            branch: Branch to analyze
            accepted_only: If True, only include cases where user accepted the prediction
        
        Returns:
            List of signal dictionaries
        """
        import json
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if accepted_only:
            cursor.execute("""
                SELECT signals_json
                FROM feedback
                WHERE predicted_branch = ? AND user_accepted = 1
            """, (branch,))
        else:
            cursor.execute("""
                SELECT signals_json
                FROM feedback
                WHERE user_preferred_branch = ? OR (predicted_branch = ? AND user_accepted = 1)
            """, (branch, branch))
        
        patterns = []
        for (signals_json,) in cursor.fetchall():
            patterns.append(json.loads(signals_json))
        
        conn.close()
        return patterns
    
    def get_average_signals_for_branch(self, branch: str) -> Optional[Dict[str, float]]:
        """
        Get average signal values for users who actually chose a branch.
        This can be used to calibrate the rule engine.
        """
        patterns = self.get_signal_patterns(branch, accepted_only=False)
        
        if not patterns:
            return None
        
        # Compute averages
        avg_signals: Dict[str, float] = {}
        signal_keys = patterns[0].keys()
        
        for key in signal_keys:
            values = [p[key] for p in patterns if key in p]
            if values:
                avg_signals[key] = sum(values) / len(values)
        
        return avg_signals
    
    def get_stats(self) -> Dict[str, any]:
        """Get overall feedback statistics"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE user_accepted = 1")
        accepted = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT predicted_branch, COUNT(*) as count
            FROM feedback
            GROUP BY predicted_branch
            ORDER BY count DESC
        """)
        by_branch = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_feedback": total,
            "acceptance_rate": accepted / total if total > 0 else 0,
            "by_branch": by_branch,
        }


# Global instance
feedback_service = FeedbackService()
