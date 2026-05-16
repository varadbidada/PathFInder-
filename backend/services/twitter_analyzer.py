"""
services/twitter_analyzer.py — NLP Analysis Pipeline for College Tweets

Pipeline stages:
  1. Sentiment analysis      (VADER + TextBlob ensemble)
  2. Emotion detection       (keyword-based lexicon)
  3. Topic extraction        (regex + keyword matching → 8 categories)
  4. Toxicity detection      (keyword heuristic)
  5. Embedding similarity clustering (TF-IDF cosine → cluster before summarising)
  6. Per-category aggregation
  7. Final report generation (sample size, confidence, dominant/minority opinion)

Design: NO single tweet drives the final verdict. Minimum cluster size enforced.
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

from services.twitter_scraper import Tweet

logger = logging.getLogger(__name__)

# ── Optional heavy deps (graceful fallback) ───────────────────────────────────
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("vaderSentiment not installed. Using TextBlob-only sentiment.")

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("textblob not installed. Using VADER-only sentiment.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. Clustering will use keyword grouping.")


# ── Topic categories & keyword maps ──────────────────────────────────────────

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "placements": [
        "placement", "placed", "package", "salary", "lpa", "ctc", "offer",
        "recruit", "hiring", "job", "internship", "intern", "campus drive",
        "on-campus", "off-campus", "ppo", "pre-placement",
    ],
    "hostel_life": [
        "hostel", "dorm", "room", "mess", "food", "canteen", "accommodation",
        "pg", "paying guest", "warden", "curfew", "roommate", "night out",
        "hostel life", "hostel room",
    ],
    "academics": [
        "exam", "cgpa", "gpa", "grade", "marks", "syllabus", "curriculum",
        "course", "lecture", "class", "assignment", "project", "semester",
        "backlog", "study", "academic", "professor", "prof",
    ],
    "coding_culture": [
        "coding", "hackathon", "competitive programming", "cp", "leetcode",
        "codeforces", "github", "open source", "dev", "developer", "tech",
        "programming", "algorithm", "data structure", "software",
    ],
    "peer_pressure": [
        "pressure", "stress", "anxiety", "mental health", "burnout",
        "comparison", "rat race", "competition", "toxic", "depression",
        "overwhelm", "peer", "jealous", "rank shaming",
    ],
    "startup_culture": [
        "startup", "entrepreneur", "founder", "venture", "incubator",
        "accelerator", "funding", "seed", "pitch", "product", "innovation",
        "e-cell", "entrepreneurship cell",
    ],
    "faculty": [
        "faculty", "professor", "prof", "teacher", "mentor", "guide",
        "phd", "research", "lab", "teaching", "lecture quality",
        "faculty support", "sir", "ma'am",
    ],
    "fest_campus_life": [
        "fest", "festival", "cultural", "techfest", "mood indigo", "shaastra",
        "rendezvous", "spring fest", "campus", "club", "society", "event",
        "sports", "nss", "ncc", "extracurricular", "college life",
    ],
}


def classify_topic(text: str) -> list[str]:
    """Return all matching topic categories for a tweet."""
    text_lower = text.lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(topic)
    return matched if matched else ["general"]


# ── Emotion lexicon ───────────────────────────────────────────────────────────

EMOTION_LEXICON: dict[str, list[str]] = {
    "joy": ["happy", "love", "amazing", "great", "excellent", "proud", "excited",
            "wonderful", "fantastic", "best", "awesome", "thrilled", "glad"],
    "anger": ["angry", "furious", "hate", "terrible", "worst", "disgusting",
              "outraged", "pathetic", "useless", "horrible", "awful"],
    "fear": ["scared", "worried", "anxious", "nervous", "afraid", "stress",
             "panic", "dread", "concern", "uncertain"],
    "sadness": ["sad", "depressed", "disappointed", "regret", "miss", "lonely",
                "hopeless", "miserable", "unhappy", "crying"],
    "surprise": ["shocked", "surprised", "unexpected", "unbelievable", "wow",
                 "omg", "incredible", "astonishing"],
    "disgust": ["disgusting", "gross", "nasty", "repulsive", "vile", "sick",
                "revolting", "appalling"],
    "trust": ["trust", "reliable", "honest", "genuine", "authentic", "credible",
              "dependable", "safe"],
    "anticipation": ["hope", "expect", "looking forward", "excited about",
                     "can't wait", "future", "upcoming"],
}


def detect_emotions(text: str) -> dict[str, float]:
    """Return emotion scores [0,1] for a tweet using lexicon matching."""
    text_lower = text.lower()
    scores: dict[str, float] = {}
    for emotion, keywords in EMOTION_LEXICON.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        scores[emotion] = min(hits / 3.0, 1.0)  # normalise: 3+ hits = 1.0
    return scores


# ── Toxicity detection ────────────────────────────────────────────────────────

TOXIC_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b(idiot|stupid|moron|dumb|loser|trash|garbage|scam|fraud)\b', re.I),
    re.compile(r'\b(f+u+c+k|sh+i+t|b+i+t+c+h|a+s+s+h+o+l+e)\b', re.I),
    re.compile(r'\b(kill yourself|kys|die)\b', re.I),
    re.compile(r'\b(racist|sexist|casteist|discrimination)\b', re.I),
]


def compute_toxicity(text: str) -> float:
    """Return toxicity score [0,1]."""
    hits = sum(1 for p in TOXIC_PATTERNS if p.search(text))
    return min(hits / 2.0, 1.0)


# ── Sentiment analysis ────────────────────────────────────────────────────────

def compute_sentiment(text: str) -> tuple[float, str]:
    """
    Returns (compound_score, label) where compound ∈ [-1, 1].
    Uses VADER + TextBlob ensemble when both are available.
    """
    scores: list[float] = []

    if VADER_AVAILABLE:
        vs = _vader.polarity_scores(text)
        scores.append(vs["compound"])

    if TEXTBLOB_AVAILABLE:
        tb_score = TextBlob(text).sentiment.polarity
        scores.append(tb_score)

    if not scores:
        # Pure keyword fallback
        pos_words = ["good", "great", "excellent", "best", "love", "amazing", "happy"]
        neg_words = ["bad", "worst", "terrible", "hate", "awful", "poor", "horrible"]
        text_lower = text.lower()
        pos = sum(1 for w in pos_words if w in text_lower)
        neg = sum(1 for w in neg_words if w in text_lower)
        compound = (pos - neg) / max(pos + neg, 1)
        scores.append(compound)

    compound = sum(scores) / len(scores)

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return round(compound, 4), label


# ── Analysed tweet ────────────────────────────────────────────────────────────

@dataclass
class AnalysedTweet:
    tweet: Tweet
    sentiment_score: float
    sentiment_label: str
    emotions: dict[str, float]
    topics: list[str]
    toxicity: float
    cluster_id: int = -1


def analyse_tweet(tweet: Tweet) -> AnalysedTweet:
    score, label = compute_sentiment(tweet.text)
    emotions = detect_emotions(tweet.text)
    topics = classify_topic(tweet.text)
    toxicity = compute_toxicity(tweet.text)
    return AnalysedTweet(
        tweet=tweet,
        sentiment_score=score,
        sentiment_label=label,
        emotions=emotions,
        topics=topics,
        toxicity=toxicity,
    )


# ── Embedding similarity clustering ──────────────────────────────────────────

MIN_CLUSTER_SIZE = 5   # A cluster must have ≥5 tweets to influence the summary
MIN_TWEETS_FOR_CLUSTERING = 20


def cluster_tweets(analysed: list[AnalysedTweet]) -> list[AnalysedTweet]:
    """
    Cluster tweets by TF-IDF cosine similarity using KMeans.
    Assigns cluster_id to each tweet. Falls back to topic-based grouping
    if scikit-learn is unavailable or corpus is too small.
    """
    if len(analysed) < MIN_TWEETS_FOR_CLUSTERING:
        # Too few tweets: assign cluster by primary topic
        for at in analysed:
            at.cluster_id = hash(at.topics[0]) % 20
        return analysed

    if not SKLEARN_AVAILABLE:
        for at in analysed:
            at.cluster_id = hash(at.topics[0]) % 20
        return analysed

    texts = [at.tweet.text for at in analysed]
    n_clusters = min(max(len(texts) // 15, 5), 20)  # 5–20 clusters

    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
        )
        X = vectorizer.fit_transform(texts)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        for at, label in zip(analysed, labels):
            at.cluster_id = int(label)
    except Exception as e:
        logger.warning(f"Clustering failed: {e}. Falling back to topic grouping.")
        for at in analysed:
            at.cluster_id = hash(at.topics[0]) % 20

    return analysed


def get_representative_tweets(
    cluster_tweets_list: list[AnalysedTweet],
    top_n: int = 3,
) -> list[AnalysedTweet]:
    """
    From a cluster, pick the most representative tweets:
    highest engagement (likes + retweets) that are not toxic.
    """
    non_toxic = [t for t in cluster_tweets_list if t.toxicity < 0.5]
    pool = non_toxic if non_toxic else cluster_tweets_list
    pool.sort(key=lambda t: t.tweet.likes + t.tweet.retweets * 2, reverse=True)
    return pool[:top_n]


# ── Per-category aggregation ──────────────────────────────────────────────────

@dataclass
class CategoryInsight:
    category: str
    tweet_count: int
    sentiment_score: float          # mean compound score
    sentiment_label: str            # dominant label
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    dominant_emotions: list[str]
    representative_tweets: list[str]
    cluster_count: int
    confidence: float


def aggregate_category(
    category: str,
    tweets: list[AnalysedTweet],
) -> CategoryInsight:
    """Aggregate all tweets for a single topic category."""
    n = len(tweets)
    if n == 0:
        return CategoryInsight(
            category=category, tweet_count=0,
            sentiment_score=0.0, sentiment_label="neutral",
            positive_ratio=0.0, negative_ratio=0.0, neutral_ratio=1.0,
            dominant_emotions=[], representative_tweets=[],
            cluster_count=0, confidence=0.0,
        )

    # Sentiment aggregation (weighted by engagement)
    total_weight = 0.0
    weighted_score = 0.0
    label_counts: Counter = Counter()

    for at in tweets:
        weight = 1 + math.log1p(at.tweet.likes + at.tweet.retweets)
        weighted_score += at.sentiment_score * weight
        total_weight += weight
        label_counts[at.sentiment_label] += 1

    mean_score = weighted_score / total_weight if total_weight > 0 else 0.0
    pos_ratio = label_counts["positive"] / n
    neg_ratio = label_counts["negative"] / n
    neu_ratio = label_counts["neutral"] / n

    dominant_label = label_counts.most_common(1)[0][0]

    # Emotion aggregation
    emotion_totals: dict[str, float] = defaultdict(float)
    for at in tweets:
        for emotion, score in at.emotions.items():
            emotion_totals[emotion] += score
    top_emotions = sorted(emotion_totals, key=lambda e: emotion_totals[e], reverse=True)[:3]

    # Cluster-based representative tweets (only from clusters with ≥ MIN_CLUSTER_SIZE)
    cluster_groups: dict[int, list[AnalysedTweet]] = defaultdict(list)
    for at in tweets:
        cluster_groups[at.cluster_id].append(at)

    valid_clusters = {
        cid: members
        for cid, members in cluster_groups.items()
        if len(members) >= MIN_CLUSTER_SIZE
    }

    rep_texts: list[str] = []
    for cid, members in list(valid_clusters.items())[:5]:
        reps = get_representative_tweets(members, top_n=1)
        rep_texts.extend(r.tweet.text for r in reps)

    # Confidence: based on sample size and cluster coverage
    cluster_coverage = len(valid_clusters) / max(len(cluster_groups), 1)
    size_factor = min(n / 50.0, 1.0)  # saturates at 50 tweets per category
    confidence = round((size_factor * 0.6 + cluster_coverage * 0.4), 3)

    return CategoryInsight(
        category=category,
        tweet_count=n,
        sentiment_score=round(mean_score, 4),
        sentiment_label=dominant_label,
        positive_ratio=round(pos_ratio, 3),
        negative_ratio=round(neg_ratio, 3),
        neutral_ratio=round(neu_ratio, 3),
        dominant_emotions=top_emotions,
        representative_tweets=rep_texts[:3],
        cluster_count=len(valid_clusters),
        confidence=confidence,
    )


# ── Final report ──────────────────────────────────────────────────────────────

@dataclass
class TwitterAnalysisReport:
    college_name: str
    sample_size: int
    overall_sentiment_score: float
    overall_sentiment_label: str
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    overall_confidence: float
    dominant_opinion: str
    minority_opinion: str
    category_insights: dict[str, CategoryInsight]
    top_emotions: list[str]
    toxicity_rate: float
    verified_tweet_ratio: float
    realistic_summary: str
    data_quality_note: str


def _build_realistic_summary(
    college_name: str,
    report_data: dict,
    category_insights: dict[str, CategoryInsight],
) -> str:
    """
    Build a realistic, hedged summary. Never asserts truth from <5 tweets.
    """
    n = report_data["sample_size"]
    conf = report_data["overall_confidence"]
    label = report_data["overall_sentiment_label"]
    pos = report_data["positive_ratio"]
    neg = report_data["negative_ratio"]

    hedge = (
        "Based on a limited sample — interpret with caution."
        if n < 50 else
        "Based on a moderate sample." if n < 100 else
        "Based on a substantial sample."
    )

    sentiment_desc = (
        f"Twitter sentiment toward {college_name} is predominantly **{label}** "
        f"({pos:.0%} positive, {neg:.0%} negative)."
    )

    # Top positive and negative categories
    pos_cats = sorted(
        [c for c in category_insights.values() if c.tweet_count >= 5],
        key=lambda c: c.sentiment_score, reverse=True
    )
    neg_cats = sorted(
        [c for c in category_insights.values() if c.tweet_count >= 5],
        key=lambda c: c.sentiment_score
    )

    pos_highlight = (
        f"Students speak most positively about **{pos_cats[0].category.replace('_', ' ')}**."
        if pos_cats else ""
    )
    neg_highlight = (
        f"The most criticism is directed at **{neg_cats[0].category.replace('_', ' ')}**."
        if neg_cats and neg_cats[0].sentiment_score < -0.05 else ""
    )

    conf_note = f"Confidence in this analysis: **{conf:.0%}** (sample size: {n} tweets)."

    parts = [hedge, sentiment_desc]
    if pos_highlight:
        parts.append(pos_highlight)
    if neg_highlight:
        parts.append(neg_highlight)
    parts.append(conf_note)

    return " ".join(parts)


def _extract_dominant_minority_opinions(
    category_insights: dict[str, CategoryInsight],
    analysed: list[AnalysedTweet],
) -> tuple[str, str]:
    """
    Dominant opinion = most common sentiment cluster representative.
    Minority opinion = least common but valid cluster representative.
    Only uses clusters with ≥ MIN_CLUSTER_SIZE tweets.
    """
    cluster_groups: dict[int, list[AnalysedTweet]] = defaultdict(list)
    for at in analysed:
        cluster_groups[at.cluster_id].append(at)

    valid = {
        cid: members
        for cid, members in cluster_groups.items()
        if len(members) >= MIN_CLUSTER_SIZE
    }

    if not valid:
        return "Insufficient data for dominant opinion.", "Insufficient data for minority opinion."

    sorted_clusters = sorted(valid.items(), key=lambda x: len(x[1]), reverse=True)

    dominant_reps = get_representative_tweets(sorted_clusters[0][1], top_n=1)
    dominant = dominant_reps[0].tweet.text if dominant_reps else "No dominant opinion found."

    minority = "No distinct minority opinion found."
    if len(sorted_clusters) > 1:
        minority_reps = get_representative_tweets(sorted_clusters[-1][1], top_n=1)
        if minority_reps:
            minority = minority_reps[0].tweet.text

    return dominant, minority


# ── Main analysis entry point ─────────────────────────────────────────────────

def analyse_college_tweets(
    college_name: str,
    tweets: list[Tweet],
) -> TwitterAnalysisReport:
    """
    Full analysis pipeline for a list of scraped tweets.

    Steps:
      1. Per-tweet NLP (sentiment, emotion, topic, toxicity)
      2. Embedding clustering
      3. Per-category aggregation
      4. Overall metrics
      5. Report generation
    """
    if not tweets:
        empty_insights = {cat: aggregate_category(cat, []) for cat in TOPIC_KEYWORDS}
        return TwitterAnalysisReport(
            college_name=college_name,
            sample_size=0,
            overall_sentiment_score=0.0,
            overall_sentiment_label="neutral",
            positive_ratio=0.0,
            negative_ratio=0.0,
            neutral_ratio=1.0,
            overall_confidence=0.0,
            dominant_opinion="No tweets found.",
            minority_opinion="No tweets found.",
            category_insights=empty_insights,
            top_emotions=[],
            toxicity_rate=0.0,
            verified_tweet_ratio=0.0,
            realistic_summary=f"No Twitter data available for {college_name}.",
            data_quality_note="Zero tweets scraped. Check API credentials or try again later.",
        )

    # Step 1: Analyse each tweet
    analysed: list[AnalysedTweet] = [analyse_tweet(t) for t in tweets]

    # Step 2: Cluster
    analysed = cluster_tweets(analysed)

    # Step 3: Group by topic
    topic_buckets: dict[str, list[AnalysedTweet]] = defaultdict(list)
    for at in analysed:
        for topic in at.topics:
            topic_buckets[topic].append(at)

    # Step 4: Per-category insights
    category_insights: dict[str, CategoryInsight] = {}
    for cat in TOPIC_KEYWORDS:
        category_insights[cat] = aggregate_category(cat, topic_buckets.get(cat, []))

    # Step 5: Overall metrics
    n = len(analysed)
    label_counts: Counter = Counter(at.sentiment_label for at in analysed)
    total_weight = 0.0
    weighted_score = 0.0
    for at in analysed:
        w = 1 + math.log1p(at.tweet.likes + at.tweet.retweets)
        weighted_score += at.sentiment_score * w
        total_weight += w

    overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
    pos_ratio = label_counts["positive"] / n
    neg_ratio = label_counts["negative"] / n
    neu_ratio = label_counts["neutral"] / n

    if overall_score >= 0.05:
        overall_label = "positive"
    elif overall_score <= -0.05:
        overall_label = "negative"
    else:
        overall_label = "neutral"

    # Emotion aggregation
    emotion_totals: dict[str, float] = defaultdict(float)
    for at in analysed:
        for emotion, score in at.emotions.items():
            emotion_totals[emotion] += score
    top_emotions = sorted(emotion_totals, key=lambda e: emotion_totals[e], reverse=True)[:3]

    # Toxicity rate
    toxic_count = sum(1 for at in analysed if at.toxicity > 0.5)
    toxicity_rate = toxic_count / n

    # Verified ratio
    verified_count = sum(1 for at in analysed if at.tweet.verified)
    verified_ratio = verified_count / n

    # Confidence: sample size + cluster quality
    cluster_groups: dict[int, list[AnalysedTweet]] = defaultdict(list)
    for at in analysed:
        cluster_groups[at.cluster_id].append(at)
    valid_clusters = sum(1 for members in cluster_groups.values() if len(members) >= MIN_CLUSTER_SIZE)
    cluster_coverage = valid_clusters / max(len(cluster_groups), 1)
    size_factor = min(n / 200.0, 1.0)
    overall_confidence = round(size_factor * 0.7 + cluster_coverage * 0.3, 3)

    # Dominant / minority opinions
    dominant, minority = _extract_dominant_minority_opinions(category_insights, analysed)

    report_data = {
        "sample_size": n,
        "overall_confidence": overall_confidence,
        "overall_sentiment_label": overall_label,
        "positive_ratio": pos_ratio,
        "negative_ratio": neg_ratio,
    }
    summary = _build_realistic_summary(college_name, report_data, category_insights)

    # Data quality note
    if n < 50:
        quality_note = (
            f"⚠️ Low sample size ({n} tweets). Results may not be representative. "
            "Consider expanding query terms or using the Academic API tier."
        )
    elif n < 100:
        quality_note = f"Moderate sample ({n} tweets). Treat category-level insights with some caution."
    else:
        quality_note = f"Good sample size ({n} tweets). Results are reasonably reliable."

    return TwitterAnalysisReport(
        college_name=college_name,
        sample_size=n,
        overall_sentiment_score=round(overall_score, 4),
        overall_sentiment_label=overall_label,
        positive_ratio=round(pos_ratio, 3),
        negative_ratio=round(neg_ratio, 3),
        neutral_ratio=round(neu_ratio, 3),
        overall_confidence=overall_confidence,
        dominant_opinion=dominant,
        minority_opinion=minority,
        category_insights=category_insights,
        top_emotions=top_emotions,
        toxicity_rate=round(toxicity_rate, 3),
        verified_tweet_ratio=round(verified_ratio, 3),
        realistic_summary=summary,
        data_quality_note=quality_note,
    )
