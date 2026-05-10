import re
from typing import Dict, List, Any

KNOWN_COLLEGES = [
    "MIT","Harvard","Stanford","Caltech","Yale","Princeton","Columbia","UPenn","Brown",
    "Dartmouth","Cornell","Duke","Northwestern","Johns Hopkins","Vanderbilt","Rice",
    "Carnegie Mellon","CMU","UCLA","UC Berkeley","Berkeley","Michigan","Georgia Tech",
    "USC","NYU","Boston University","BU","Northeastern","Purdue","Illinois","UIUC",
    "Wisconsin","UNC","Ohio State","Penn State","UT Austin","Florida","IIT","IIM",
    "BITS","NIT","VIT","Manipal","Ashoka",
]
KNOWN_PROGRAMS = [
    "Computer Science","CS","Engineering","Mechanical Engineering","Electrical Engineering",
    "Civil Engineering","Chemical Engineering","Business","MBA","Finance","Economics",
    "Mathematics","Math","Physics","Biology","Chemistry","Pre-Med","Medicine","Law",
    "Psychology","Data Science","Artificial Intelligence","AI","Machine Learning","ML",
    "Information Technology","IT","Cybersecurity","Robotics","Aerospace","Architecture",
]
TEST_PATTERNS = [
    r"\bSAT\b",r"\bACT\b",r"\bGRE\b",r"\bGMAT\b",r"\bTOEFL\b",
    r"\bIELTS\b",r"\bGPA\b",r"\b\d+(\.\d+)?\s*(GPA|gpa)\b",
]
LOCATION_PATTERNS = [
    r"\b(USA|US|United States|UK|United Kingdom|Canada|Australia|Germany|India|Singapore)\b",
    r"\b(New York|Boston|California|Texas|Massachusetts|London|Toronto|Sydney)\b",
]
DEADLINE_PATTERNS = [
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(st|nd|rd|th)?(,?\s*\d{4})?\b",
    r"\b20\d{2}\b",
    r"\b(early action|early decision|regular decision|rolling admission)\b",
]
FINANCIAL_PATTERNS = [
    r"\$[\d,]+(\.\d{2})?",
    r"\b(scholarship|grant|loan|financial aid|fellowship|assistantship|stipend|waiver)\b",
]

def _find_matches(text, patterns):
    found = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            val = m.group(0).strip()
            if val not in found:
                found.append(val)
    return found

def _find_list_items(text, items):
    found = []
    for item in items:
        if re.search(r'\b' + re.escape(item) + r'\b', text, re.IGNORECASE):
            if item not in found:
                found.append(item)
    return found

class EntityExtractor:
    def extract(self, query: str) -> Dict[str, Any]:
        return {
            "colleges":   _find_list_items(query, KNOWN_COLLEGES),
            "programs":   _find_list_items(query, KNOWN_PROGRAMS),
            "tests":      _find_matches(query, TEST_PATTERNS),
            "locations":  _find_matches(query, LOCATION_PATTERNS),
            "deadlines":  _find_matches(query, DEADLINE_PATTERNS),
            "financials": _find_matches(query, FINANCIAL_PATTERNS),
        }
