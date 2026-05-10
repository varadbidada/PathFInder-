"""
Pathfinder — Central Configuration
All thresholds, limits, and settings live here. No magic numbers in engine code.
"""
from __future__ import annotations
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"
    log_level: str = "INFO"

    # ── Groq ────────────────────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_tokens: int = 1024
    groq_temperature: float = 0.3

    # ── Reddit ───────────────────────────────────────────────────────────────
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "Pathfinder/1.0"

    # ── Serper ───────────────────────────────────────────────────────────────
    serper_api_key: str = ""

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    reddit_cache_ttl_seconds: int = 86_400  # 24 hours

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./pathfinder.db"

    # ── Rate Limiting ────────────────────────────────────────────────────────
    rate_limit_per_minute: int = 20

    # ── Rule Engine Thresholds ───────────────────────────────────────────────
    confidence_threshold: float = 0.75          # Minimum confidence to commit to a branch
    tie_threshold: float = 0.15                 # Gap ≤ this → trigger tie-breaker question
    max_tie_breaker_rounds: int = 2             # Prevent infinite tie-breaker loops

    # ── Recommendation Engine ────────────────────────────────────────────────
    dream_rank_gap: int = 10_000               # Cutoff better than rank by this much → Dream
    moderate_rank_gap: int = 5_000             # Within ±5k → Moderate

    # ── Signal Extraction ────────────────────────────────────────────────────
    signal_retry_attempts: int = 1             # Retry once on parse failure
    neutral_signal_default: float = 0.5

    # ── Question Engine ──────────────────────────────────────────────────────
    questions_file: str = "data/questions.json"
    colleges_file: str = "data/colleges.json"
    max_questions_per_category: int = 2

    # ── Branch Weights ───────────────────────────────────────────────────────
    SIGNAL_BRANCH_MAP: dict = {
        "Logical_Thinking":  {"CS": 2.5, "Electronics": 1.5},
        "Creativity":        {"CS": 1.0, "Civil": 2.0, "Mechanical": 1.5},
        "Manual_Work":       {"Mechanical": 2.5, "Civil": 2.0},
        "Spatial_Awareness": {"Civil": 2.5, "Mechanical": 1.5},
        "Biology_Interest":  {"Medical": 3.0},
        "Problem_Solving":   {"CS": 2.0, "Electronics": 2.0},
        "Communication":     {"CS": 0.5, "Civil": 1.0},
        "Math_Aptitude":     {"CS": 1.5, "Electronics": 2.0, "Mechanical": 1.5},
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
