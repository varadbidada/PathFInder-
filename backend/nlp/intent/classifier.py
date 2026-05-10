import re
from typing import Dict, Any

INTENT_PATTERNS = {
    "greeting": [r"\b(hi|hello|hey|good morning|good evening)\b"],
    "admission_requirements": [r"\b(admission|require|requirement|qualify|gpa|sat|act|test score|criteria|eligible)\b"],
    "financial_aid": [r"\b(cost|tuition|fee|scholarship|financial aid|grant|loan|afford|bursary|fund)\b"],
    "deadlines": [r"\b(deadline|due date|when|last date|apply by|cutoff|early action|early decision|regular decision)\b"],
    "college_comparison": [r"\b(compare|versus|vs|difference|better|best|rank|ranking|which college|which university)\b"],
    "program_info": [r"\b(program|course|major|minor|curriculum|degree|bachelor|master|phd|doctorate)\b"],
    "campus_life": [r"\b(campus|dorm|housing|club|sport|activity|life|culture|diversity|community)\b"],
    "application_process": [r"\b(apply|application|how to|steps|process|common app|personal statement|essay|recommendation)\b"],
    "career_outcomes": [r"\b(career|job|placement|salary|alumni|employment|internship|outcome)\b"],
    "goodbye": [r"\b(bye|goodbye|thanks|thank you|done|exit)\b"],
}
FALLBACK_INTENT = "general_inquiry"

class IntentClassifier:
    def __init__(self):
        self.patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in INTENT_PATTERNS.items()
        }

    def classify(self, query: str) -> Dict[str, Any]:
        scores: Dict[str, int] = {}
        for intent, compiled in self.patterns.items():
            hits = sum(1 for p in compiled if p.search(query))
            if hits:
                scores[intent] = hits
        if not scores:
            return {"intent": FALLBACK_INTENT, "confidence": 0.3, "matched_patterns": []}
        best = max(scores, key=scores.__getitem__)
        total = sum(scores.values())
        confidence = min(scores[best] / max(total, 1) + 0.4, 0.99)
        return {"intent": best, "confidence": round(confidence, 2), "matched_patterns": list(scores.keys())}
