"""
services/peer_comparison.py — Peer Comparison Feature

Anonymously stores student choices and provides peer statistics.
Helps students feel confident: "You're not alone in this choice."
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "peer_stats.db"


def _init_database() -> None:
    """Initialize the peer statistics database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peer_choices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            branch_predicted TEXT NOT NULL,
            rank_range_bucket TEXT NOT NULL,
            city_tier TEXT NOT NULL,
            college_chosen TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_branch_rank 
        ON peer_choices(branch_predicted, rank_range_bucket)
    """)
    
    conn.commit()
    conn.close()
    
    logger.info(f"Peer statistics database initialized at {DB_PATH}")


def _get_rank_bucket(rank: int) -> str:
    """
    Bucket ranks for anonymization.
    
    Args:
        rank: Student's rank
    
    Returns:
        Rank bucket string (e.g., "1000-2000")
    """
    if rank < 1000:
        return "0-1000"
    elif rank < 2000:
        return "1000-2000"
    elif rank < 5000:
        return "2000-5000"
    elif rank < 10000:
        return "5000-10000"
    elif rank < 20000:
        return "10000-20000"
    elif rank < 50000:
        return "20000-50000"
    elif rank < 100000:
        return "50000-100000"
    else:
        return "100000+"


def _get_city_tier(location: Optional[str]) -> str:
    """
    Classify city into tiers.
    
    Args:
        location: City/state name
    
    Returns:
        City tier (Tier-1, Tier-2, Tier-3, Any)
    """
    if not location:
        return "Any"
    
    location_lower = location.lower()
    
    # Tier-1 cities
    tier_1 = ["mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "pune", "kolkata"]
    if any(city in location_lower for city in tier_1):
        return "Tier-1"
    
    # Tier-2 cities (education hubs)
    tier_2 = ["kota", "trichy", "vellore", "manipal", "pilani", "roorkee", "kharagpur", 
              "ahmedabad", "jaipur", "lucknow", "bhopal", "patna"]
    if any(city in location_lower for city in tier_2):
        return "Tier-2"
    
    # Everything else is Tier-3
    return "Tier-3"


def store_peer_choice(
    branch_predicted: str,
    rank: int,
    location: Optional[str] = None,
    college_chosen: Optional[str] = None,
) -> None:
    """
    Anonymously store a student's choice.
    
    Args:
        branch_predicted: Predicted branch
        rank: Student's rank
        location: Preferred location
        college_chosen: College they chose (optional)
    """
    try:
        _init_database()
        
        rank_bucket = _get_rank_bucket(rank)
        city_tier = _get_city_tier(location)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO peer_choices (branch_predicted, rank_range_bucket, city_tier, college_chosen)
            VALUES (?, ?, ?, ?)
        """, (branch_predicted, rank_bucket, city_tier, college_chosen))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored peer choice: {branch_predicted}, rank bucket {rank_bucket}")
        
    except Exception as e:
        logger.error(f"Failed to store peer choice: {e}")


def get_peer_stats(
    branch: str,
    rank: int,
    location: Optional[str] = None,
) -> dict:
    """
    Get peer statistics for similar students.
    
    Args:
        branch: Branch to query
        rank: Student's rank
        location: Preferred location (optional)
    
    Returns:
        {
            "total_peers": int,
            "branch_match_percentage": float,
            "rank_bucket": str,
            "top_colleges": list[tuple[str, int]],
            "message": str
        }
    """
    try:
        _init_database()
        
        rank_bucket = _get_rank_bucket(rank)
        city_tier = _get_city_tier(location)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get total peers in same rank bucket
        cursor.execute("""
            SELECT COUNT(*) FROM peer_choices
            WHERE rank_range_bucket = ?
        """, (rank_bucket,))
        
        total_peers = cursor.fetchone()[0]
        
        # Get peers who chose the same branch
        cursor.execute("""
            SELECT COUNT(*) FROM peer_choices
            WHERE rank_range_bucket = ? AND branch_predicted = ?
        """, (rank_bucket, branch))
        
        branch_matches = cursor.fetchone()[0]
        
        # Get top colleges chosen by peers
        cursor.execute("""
            SELECT college_chosen, COUNT(*) as count
            FROM peer_choices
            WHERE rank_range_bucket = ? 
              AND branch_predicted = ?
              AND college_chosen IS NOT NULL
            GROUP BY college_chosen
            ORDER BY count DESC
            LIMIT 5
        """, (rank_bucket, branch))
        
        top_colleges = cursor.fetchall()
        
        conn.close()
        
        # Calculate percentage
        branch_percentage = (branch_matches / total_peers * 100) if total_peers > 0 else 0
        
        # Generate message
        if total_peers == 0:
            message = f"You're among the first students in the {rank_bucket} rank range to use Pathfinder!"
        elif branch_matches == 0:
            message = f"Among {total_peers} students with your rank ({rank_bucket}), none have chosen {branch} yet. You could be a pioneer!"
        else:
            message = f"Among {total_peers} students with your rank ({rank_bucket}), {branch_percentage:.0f}% chose {branch}. You're not alone in this choice!"
        
        return {
            "total_peers": total_peers,
            "branch_match_percentage": round(branch_percentage, 1),
            "rank_bucket": rank_bucket,
            "top_colleges": [(college, count) for college, count in top_colleges],
            "message": message,
        }
        
    except Exception as e:
        logger.error(f"Failed to get peer stats: {e}")
        return {
            "total_peers": 0,
            "branch_match_percentage": 0,
            "rank_bucket": _get_rank_bucket(rank),
            "top_colleges": [],
            "message": "Peer statistics unavailable",
        }
