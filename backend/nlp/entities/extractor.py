"""
nlp/entities/extractor.py — India-Specific Entity Extractor for JEE/NEET Students

Extracts entities relevant to Indian engineering/medical college admissions:
- Colleges (dynamically loaded from colleges.json)
- Branches (Indian engineering branches: CSE, ECE, Mech, etc.)
- Exams (JEE, NEET, KCET, MHT-CET, BITSAT, etc.)
- Ranks (extracted as integers)
- Locations (Indian cities and states)
- Budget (in lakhs)
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Dynamic college loading ───────────────────────────────────────────────────

def _load_colleges() -> tuple[list[str], dict[str, list[str]]]:
    """
    Load college names from colleges.json and colleges_josaa.json, merging both.
    Returns: (college_names, short_forms_map)
    """
    try:
        base_path = Path(__file__).parent.parent.parent / "data"
        josaa_path = base_path / "colleges_josaa.json"
        fallback_path = base_path / "colleges.json"
        
        college_names_set = set()
        
        # Load from JoSAA file (real data)
        if josaa_path.exists():
            with open(josaa_path, 'r', encoding='utf-8') as f:
                josaa_data = json.load(f)
            college_names_set.update(c["name"] for c in josaa_data)
            logger.info(f"Loaded {len(josaa_data)} colleges from {josaa_path.name}")
        
        # Also load from fallback (has BITS, private colleges, etc.)
        if fallback_path.exists():
            with open(fallback_path, 'r', encoding='utf-8') as f:
                fallback_data = json.load(f)
            college_names_set.update(c["name"] for c in fallback_data)
            logger.info(f"Loaded {len(fallback_data)} colleges from {fallback_path.name}")
        
        # Convert to sorted list
        college_names = sorted(college_names_set)
        
        logger.info(f"Total unique colleges: {len(college_names)}")
        
        # Build short form mappings
        short_forms = {
            "IIT Bombay": ["IITB", "IIT-B", "IIT B"],
            "IIT Delhi": ["IITD", "IIT-D", "IIT D"],
            "IIT Madras": ["IITM", "IIT-M", "IIT M"],
            "IIT Kanpur": ["IITK", "IIT-K", "IIT K"],
            "IIT Kharagpur": ["IITKGP", "IIT-KGP", "IIT KGP"],
            "IIT Roorkee": ["IITR", "IIT-R", "IIT R"],
            "IIT Guwahati": ["IITG", "IIT-G", "IIT G"],
            "IIT Hyderabad": ["IITH", "IIT-H", "IIT H"],
            "NIT Trichy": ["NITT", "NIT-T", "NIT T"],
            "NIT Surathkal": ["NITK", "NIT-K", "NIT K"],
            "NIT Warangal": ["NITW", "NIT-W", "NIT W"],
            "NIT Rourkela": ["NITR", "NIT-R", "NIT R"],
            "NIT Calicut": ["NITC", "NIT-C", "NIT C"],
            "BITS Pilani": ["BITS", "BITS-P"],
            "BITS Hyderabad": ["BITS-H", "BITS Hyd"],
            "BITS Goa": ["BITS-G"],
            "IIIT Hyderabad": ["IIITH", "IIIT-H"],
            "IIIT Delhi": ["IIITD", "IIIT-D"],
            "IIIT Allahabad": ["IIITA", "IIIT-A"],
            "DTU Delhi": ["DTU"],
            "NSUT Delhi": ["NSUT", "NSIT"],
            "VIT Vellore": ["VIT"],
            "Manipal Institute of Technology": ["Manipal", "MIT Manipal"],
        }
        
        # Add common IIITs that might not be in the data
        common_iiits = [
            "IIIT Hyderabad", "IIIT Delhi", "IIIT Allahabad", "IIIT Bangalore",
            "IIIT Pune", "IIIT Kota", "IIIT Vadodara", "IIIT Nagpur"
        ]
        for iiit in common_iiits:
            if iiit not in college_names:
                college_names.append(iiit)
        
        college_names = sorted(college_names)
        
        return college_names, short_forms
        
    except Exception as e:
        logger.error(f"Failed to load colleges: {e}")
        # Fallback minimal list
        return [
            "IIT Bombay", "IIT Delhi", "IIT Madras", "IIT Kanpur", "IIT Kharagpur",
            "NIT Trichy", "NIT Surathkal", "BITS Pilani", "IIIT Hyderabad"
        ], {}


KNOWN_COLLEGES, COLLEGE_SHORT_FORMS = _load_colleges()

# ── Indian engineering branches ───────────────────────────────────────────────

KNOWN_BRANCHES = [
    # Computer Science variants
    "CSE", "CS", "Computer Science", "Computer Science and Engineering",
    "Computer Engineering", "IT", "Information Technology",
    "Artificial Intelligence", "AI", "Data Science", "Machine Learning", "ML",
    
    # Electronics variants
    "ECE", "Electronics", "Electronics and Communication Engineering",
    "Electronics and Communication", "EEE", "Electrical and Electronics Engineering",
    "Electronics and Instrumentation",
    
    # Electrical
    "Electrical", "Electrical Engineering", "EE", "Power Engineering",
    
    # Mechanical
    "Mechanical", "Mechanical Engineering", "Mech", "Production Engineering",
    "Industrial Engineering", "Manufacturing",
    
    # Civil
    "Civil", "Civil Engineering", "Civil and Infrastructure",
    
    # Chemical
    "Chemical", "Chemical Engineering", "Chemical Science",
    
    # Other branches
    "Aerospace", "Aerospace Engineering", "Aeronautical Engineering",
    "Biotechnology", "Biotech", "Biomedical Engineering",
    "Metallurgy", "Metallurgical Engineering", "Materials Science",
    "Mining", "Mining Engineering",
    "Engineering Physics", "EP",
    "Mathematics and Computing", "MnC",
    "Instrumentation", "Instrumentation Engineering",
]

# ── Indian entrance exams ─────────────────────────────────────────────────────

EXAM_PATTERNS = [
    # JEE variants
    r"\bJEE\s*(?:Main|Mains|Advanced|Adv)?\b",
    r"\bJEE[-\s]?(?:Main|Mains|Advanced|Adv)\b",
    
    # NEET
    r"\bNEET\b",
    r"\bNEET[-\s]?(?:UG|PG)?\b",
    
    # State exams
    r"\bKCET\b",
    r"\bMHT[-\s]?CET\b",
    r"\bWBJEE\b",
    r"\bTS[-\s]?EAMCET\b",
    r"\bAP[-\s]?EAMCET\b",
    r"\bKEAM\b",
    r"\bUPSEE\b",
    
    # Private exams
    r"\bBITSAT\b",
    r"\bVITEEE\b",
    r"\bSRMJEEE\b",
    r"\bKIITEE\b",
    r"\bCOMEDK\b",
    
    # General patterns
    r"\b(?:rank|percentile|score|marks)\s*[:\s]*[\d,]+\b",
]

# ── Rank extraction patterns ──────────────────────────────────────────────────

RANK_PATTERNS = [
    r"\b(\d{1,6})\s*(?:rank|AIR|All India Rank)\b",
    r"\b(?:rank|AIR)\s*[:\s]*(\d{1,6})\b",
    r"\b(?:got|scored|obtained)\s*(?:a\s*)?(?:rank\s*(?:of\s*)?)?(\d{1,6})\b",
    r"\bmy\s*rank\s*(?:is|was)?\s*(\d{1,6})\b",
]

# ── Indian cities and states ──────────────────────────────────────────────────

INDIAN_CITIES = [
    # Metro cities
    "Mumbai", "Delhi", "Bangalore", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata",
    
    # Education hubs
    "Kota", "Patna", "Lucknow", "Bhopal", "Jaipur", "Ahmedabad", "Surat",
    "Trichy", "Tiruchirappalli", "Vellore", "Manipal", "Pilani", "Roorkee", "Kharagpur",
    
    # State capitals and major cities
    "Chandigarh", "Indore", "Nagpur", "Kanpur", "Varanasi", "Allahabad", "Prayagraj",
    "Guwahati", "Bhubaneswar", "Raipur", "Ranchi", "Thiruvananthapuram", "Kochi",
    "Coimbatore", "Madurai", "Visakhapatnam", "Vijayawada", "Warangal", "Surathkal",
    "Calicut", "Kozhikode", "Mangalore", "Mysore", "Hubli", "Dharwad",
]

INDIAN_STATES = [
    "Maharashtra", "Karnataka", "Tamil Nadu", "Telangana", "Delhi", "NCR",
    "Uttar Pradesh", "UP", "Rajasthan", "Gujarat", "West Bengal", "WB",
    "Bihar", "Madhya Pradesh", "MP", "Andhra Pradesh", "AP", "Kerala",
    "Odisha", "Orissa", "Jharkhand", "Chhattisgarh", "Assam", "Punjab",
    "Haryana", "Himachal Pradesh", "HP", "Uttarakhand", "Goa",
]

# Regional patterns
REGION_PATTERNS = [
    r"\b(?:North|South|East|West|Central)\s*India\b",
    r"\b(?:Northern|Southern|Eastern|Western)\s*(?:India|states?)\b",
]

# ── Budget extraction patterns ────────────────────────────────────────────────

BUDGET_PATTERNS = [
    # Lakh formats
    r"\b(\d+(?:\.\d+)?)\s*(?:lakh|lac|L)\b",
    r"₹\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|L)\b",
    
    # Rupee formats with commas
    r"₹\s*(\d{1,2}),(\d{2}),(\d{3})\b",  # ₹2,00,000
    r"\b(\d{1,2}),(\d{2}),(\d{3})\s*(?:rupees?|INR|Rs\.?)\b",
    
    # Budget context
    r"\bbudget\s*(?:is|of|around|approximately)?\s*(?:about)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|L)\b",
    r"\bafford\s*(?:up\s*to)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|L)\b",
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _find_matches(text: str, patterns: list) -> list[str]:
    """Find all regex pattern matches in text."""
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = match.group(0).strip()
            if val and val not in found:
                found.append(val)
    return found


def _find_list_items(text: str, items: list[str]) -> list[str]:
    """Find all items from a list that appear in text."""
    found = []
    text_lower = text.lower()
    
    for item in items:
        # Use word boundaries for exact matching
        pattern = r'\b' + re.escape(item) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            if item not in found:
                found.append(item)
    
    return found


def _extract_ranks(text: str) -> list[int]:
    """Extract rank numbers from text, handling formats like '2.3k', '2300', '23 hundred'."""
    ranks = []
    
    # Direct rank patterns
    for pattern in RANK_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                rank_str = match.group(1)
                rank = int(rank_str.replace(',', ''))
                if 1 <= rank <= 999999:  # Valid rank range
                    if rank not in ranks:
                        ranks.append(rank)
            except (ValueError, IndexError):
                continue
    
    # Handle "2.3k" format
    k_pattern = r"\b(\d+(?:\.\d+)?)\s*k\b"
    for match in re.finditer(k_pattern, text, re.IGNORECASE):
        try:
            num = float(match.group(1))
            rank = int(num * 1000)
            if 1 <= rank <= 999999:
                if rank not in ranks:
                    ranks.append(rank)
        except ValueError:
            continue
    
    return sorted(ranks)


def _extract_budget(text: str) -> float | None:
    """Extract budget in lakhs from text."""
    text_lower = text.lower()
    
    # Try lakh patterns first
    for pattern in BUDGET_PATTERNS[:4]:  # First 4 are lakh-based
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            try:
                if "," in match.group(0):
                    # Handle ₹2,00,000 format
                    groups = match.groups()
                    if len(groups) >= 3:
                        amount = int(groups[0]) * 100000 + int(groups[1]) * 1000 + int(groups[2])
                        return round(amount / 100000, 1)
                else:
                    # Handle "2 lakh" or "₹2L" format
                    amount = float(match.group(1))
                    return round(amount, 1)
            except (ValueError, IndexError):
                continue
    
    return None


def _expand_college_short_forms(text: str) -> str:
    """Expand college short forms to full names for better matching."""
    expanded = text
    for full_name, short_forms in COLLEGE_SHORT_FORMS.items():
        for short in short_forms:
            # Replace short form with full name (case-insensitive)
            pattern = r'\b' + re.escape(short) + r'\b'
            expanded = re.sub(pattern, full_name, expanded, flags=re.IGNORECASE)
    return expanded


# ── Main EntityExtractor class ────────────────────────────────────────────────

class EntityExtractor:
    """
    India-specific entity extractor for JEE/NEET students.
    
    Extracts:
    - colleges: Indian engineering/medical colleges
    - branches: Engineering branches (CSE, ECE, Mech, etc.)
    - exams: JEE, NEET, state exams, private exams
    - ranks: Integer ranks extracted from text
    - locations: Indian cities, states, regions
    - budget_lakh: Budget in lakhs (float)
    """
    
    def extract(self, query: str) -> dict[str, Any]:
        """
        Extract entities from query text.
        
        Returns:
            {
                "colleges": list[str],
                "branches": list[str],
                "exams": list[str],
                "ranks": list[int],
                "locations": list[str],
                "budget_lakh": float | None
            }
        """
        # Expand short forms for better college matching
        expanded_query = _expand_college_short_forms(query)
        
        # Extract entities
        colleges = _find_list_items(expanded_query, KNOWN_COLLEGES)
        branches = _find_list_items(query, KNOWN_BRANCHES)
        exams = _find_matches(query, EXAM_PATTERNS)
        ranks = _extract_ranks(query)
        
        # Extract locations (cities + states + regions)
        cities = _find_list_items(query, INDIAN_CITIES)
        states = _find_list_items(query, INDIAN_STATES)
        regions = _find_matches(query, REGION_PATTERNS)
        locations = cities + states + regions
        
        # Extract budget
        budget_lakh = _extract_budget(query)
        
        return {
            "colleges": colleges,
            "branches": branches,
            "exams": exams,
            "ranks": ranks,
            "locations": locations,
            "budget_lakh": budget_lakh,
        }

