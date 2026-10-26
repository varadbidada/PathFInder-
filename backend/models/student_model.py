"""
Student Model for LLM-powered career counselling.
Tracks personality traits, interests, and branch hypothesis as conversation evolves.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StudentModel:
    """
    Growing model of a Class 12 student's personality and preferences.
    Updated after each conversation turn based on LLM extraction.
    """
    
    # Trait scores (0.0 to 1.0, start at 0.5 = unknown)
    math_aptitude: float = 0.5
    logical_thinking: float = 0.5
    creativity: float = 0.5
    hands_on: float = 0.5
    spatial_reasoning: float = 0.5
    biology_interest: float = 0.5
    problem_solving: float = 0.5
    
    # Categorical traits
    risk_appetite: Optional[str] = None    # low/medium/high
    work_style: Optional[str] = None       # solo/team/either
    memory_preference: Optional[str] = None  # conceptual/rote/either
    
    # Qualitative profile (accumulated lists)
    interests: list = field(default_factory=list)
    aversions: list = field(default_factory=list)
    motivations: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)
    notable_quotes: list = field(default_factory=list)
    
    # Hypothesis
    branch_hypothesis: str = "unknown"
    hypothesis_confidence: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert model to dict for MongoDB storage and LLM context."""
        return {
            "math_aptitude": self.math_aptitude,
            "logical_thinking": self.logical_thinking,
            "creativity": self.creativity,
            "hands_on": self.hands_on,
            "spatial_reasoning": self.spatial_reasoning,
            "biology_interest": self.biology_interest,
            "problem_solving": self.problem_solving,
            "risk_appetite": self.risk_appetite,
            "work_style": self.work_style,
            "memory_preference": self.memory_preference,
            "interests": self.interests[-10:],  # cap to last 10
            "aversions": self.aversions[-10:],
            "motivations": self.motivations,
            "contradictions": self.contradictions,
            "notable_quotes": self.notable_quotes[-5:],
            "branch_hypothesis": self.branch_hypothesis,
            "hypothesis_confidence": self.hypothesis_confidence,
        }
    
    def apply_updates(self, trait_updates: dict, profile_updates: dict):
        """
        Apply LLM-extracted updates to the student model.
        Uses exponential moving average (EMA) for numeric traits.
        """
        alpha = 0.4  # weight for new evidence (0.4 = balanced)
        
        # Update numeric traits with EMA
        for trait, value in trait_updates.items():
            if value is None:
                continue
            
            if isinstance(value, float) and hasattr(self, trait):
                current = getattr(self, trait)
                if current == 0.5:  # first real observation
                    setattr(self, trait, value)
                else:
                    # EMA: new = old * (1-α) + new * α
                    setattr(self, trait, current * (1 - alpha) + value * alpha)
            
            elif isinstance(value, str) and hasattr(self, trait):
                # Categorical traits: just update
                setattr(self, trait, value)
        
        # Accumulate profile lists (deduplicate)
        for key in ["interests", "aversions", "motivations", "contradictions", "notable_quotes"]:
            new_items = profile_updates.get(key, [])
            existing = getattr(self, key)
            for item in new_items:
                if item and item not in existing:
                    existing.append(item)
    
    def calculate_branch_scores(self) -> dict[str, float]:
        """
        Calculate branch fit scores based on current trait values.
        Returns dict of branch codes to scores (0.0-1.0).
        """
        # Branch profiles (ideal trait values for each branch)
        branch_profiles = {
            "CS": {
                "logical_thinking": 0.75,
                "problem_solving": 0.80,
                "math_aptitude": 0.70,
                "creativity": 0.65,
                "hands_on": 0.30  # inverted: CS is less hands-on
            },
            "ECE": {
                "logical_thinking": 0.75,
                "math_aptitude": 0.75,
                "hands_on": 0.60,
                "spatial_reasoning": 0.65,
                "problem_solving": 0.70
            },
            "Mech": {
                "hands_on": 0.80,
                "spatial_reasoning": 0.75,
                "math_aptitude": 0.65,
                "problem_solving": 0.70,
                "creativity": 0.60
            },
            "Civil": {
                "spatial_reasoning": 0.80,
                "hands_on": 0.65,
                "math_aptitude": 0.65,
                "creativity": 0.70,
                "problem_solving": 0.65
            },
            "Chemical": {
                "biology_interest": 0.70,
                "logical_thinking": 0.70,
                "math_aptitude": 0.65,
                "problem_solving": 0.70
            }
        }
        
        scores = {}
        for branch, profile in branch_profiles.items():
            # Calculate distance between student traits and branch profile
            total_distance = 0.0
            num_traits = 0
            
            for trait, ideal_value in profile.items():
                student_value = getattr(self, trait, 0.5)
                distance = abs(student_value - ideal_value)
                total_distance += distance
                num_traits += 1
            
            # Convert distance to similarity score (0-1, higher is better)
            avg_distance = total_distance / num_traits if num_traits > 0 else 1.0
            score = 1.0 - avg_distance  # invert: lower distance = higher score
            scores[branch] = max(0.0, min(1.0, score))  # clamp to [0, 1]
        
        return scores
    
    def get_top_branches(self, n: int = 3) -> list[dict]:
        """Get top N branch recommendations with scores."""
        scores = self.calculate_branch_scores()
        sorted_branches = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"branch": branch, "score": score}
            for branch, score in sorted_branches[:n]
        ]
    
    @classmethod
    def from_dict(cls, data: dict) -> "StudentModel":
        """Create StudentModel from dict (for MongoDB deserialization)."""
        model = cls()
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        return model
