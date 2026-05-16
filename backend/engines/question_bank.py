"""
engines/question_bank.py — Centralized Question Bank

All questions are predefined with metadata for deterministic selection.
Questions are randomized per session to provide variety across users.
"""
from __future__ import annotations
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from engines.conversation_fsm import ConversationStage


@dataclass
class Question:
    """Question with metadata"""
    id: str
    text: str
    stage: ConversationStage
    mapped_branches: List[str]  # Which branches this question helps identify
    difficulty: int  # 1-5
    tie_breaker_priority: int  # Higher = more useful for tie-breaking
    category: str  # interest, skill, workstyle, etc.
    
    def __hash__(self):
        return hash(self.id)


# Centralized question bank
QUESTION_BANK: List[Question] = [
    # ── INTRODUCTION ──────────────────────────────────────────────────────
    Question(
        id="intro_001",
        text="Hi! I'm Pathfinder, your AI career counsellor. I'll help you find the best engineering branch and colleges based on your interests and abilities. Ready to start?",
        stage=ConversationStage.INTRODUCTION,
        mapped_branches=[],
        difficulty=1,
        tie_breaker_priority=0,
        category="greeting",
    ),
    
    # ── INTEREST ASSESSMENT ───────────────────────────────────────────────
    Question(
        id="interest_001",
        text="Imagine it's a Saturday and you have the whole day free. Which of these would you most enjoy doing?\n🖥️ Building a website or app\n🔧 Taking apart a gadget to see how it works\n🏗️ Visiting a construction site or sketching a building design\n🔬 Watching a biology documentary or doing a science experiment\n⚡ Tinkering with circuits or electronics\n\nJust pick what feels most natural to you, or describe in your own words!",
        stage=ConversationStage.INTEREST_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=5,
        category="interest",
    ),
    
    Question(
        id="interest_002",
        text="When you hear about a new technology (like AI, electric cars, or space exploration), what's your first reaction?\n💡 I want to understand how it works\n🛠️ I want to build something similar\n📊 I want to know its real-world impact\n🎨 I want to improve its design\n\nTell me what excites you most!",
        stage=ConversationStage.INTEREST_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Electronics", "Civil"],
        difficulty=2,
        tie_breaker_priority=4,
        category="interest",
    ),
    
    Question(
        id="interest_003",
        text="If you could spend a year learning anything (money and time no issue), what would it be?\n💻 Programming and software development\n🔩 Mechanical systems and robotics\n🏛️ Architecture and structural design\n🧬 Biology and medical science\n⚡ Electronics and circuit design\n\nWhat calls to you?",
        stage=ConversationStage.INTEREST_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=6,
        category="interest",
    ),
    
    Question(
        id="interest_004",
        text="When you read tech news or watch videos, which topics make you stop scrolling?\n🤖 AI, machine learning, new apps\n🚗 Electric vehicles, drones, robotics\n🌆 Smart cities, sustainable buildings\n💊 Medical breakthroughs, biotech\n📱 New gadgets, chip technology",
        stage=ConversationStage.INTEREST_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=5,
        category="interest",
    ),
    
    Question(
        id="interest_005",
        text="If you had to pick a superpower for your career, which would it be?\n🧠 Instantly understand any code or algorithm\n🔧 Build anything you imagine with your hands\n🏗️ Design structures that last centuries\n🧬 Cure diseases and understand the human body\n⚡ Control and understand all electronic devices",
        stage=ConversationStage.INTEREST_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=4,
        category="interest",
    ),
    
    # ── SKILL ASSESSMENT ──────────────────────────────────────────────────
    Question(
        id="skill_001",
        text="Think about your strengths. Which of these describes you best?\n🧮 I'm great at math and logical problem-solving\n🔧 I'm good with my hands and building things\n🎨 I'm creative and good at visualizing designs\n📚 I'm strong in biology and chemistry\n⚡ I understand how electronic devices work\n\nBe honest about what comes naturally to you!",
        stage=ConversationStage.SKILL_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=3,
        tie_breaker_priority=7,
        category="skill",
    ),
    
    Question(
        id="skill_002",
        text="Imagine you're on a project: one team writes the software brain, the other team builds the physical hardware. Which team excites you more?\n💻 Software team (coding, algorithms, logic)\n🔧 Hardware team (physical components, assembly)\n🤝 Both equally (I like the intersection)\n\nWhich feels like your zone?",
        stage=ConversationStage.SKILL_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Electronics"],
        difficulty=3,
        tie_breaker_priority=8,
        category="skill",
    ),
    
    Question(
        id="skill_003",
        text="When solving a problem, what's your natural approach?\n🧩 Break it into logical steps and code a solution\n🔨 Build a physical prototype or model\n📐 Draw diagrams and visualize the solution\n🔬 Research and experiment systematically\n⚡ Test different circuits or configurations\n\nHow do you tackle challenges?",
        stage=ConversationStage.SKILL_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=3,
        tie_breaker_priority=6,
        category="skill",
    ),
    
    Question(
        id="skill_004",
        text="Which school subjects did you genuinely enjoy (not just score well in)?\n💻 Computer Science, Math\n🔧 Physics, Workshop/Lab work\n📐 Math, Drawing, Design\n🧪 Biology, Chemistry\n⚡ Physics, Electronics practicals",
        stage=ConversationStage.SKILL_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=3,
        tie_breaker_priority=5,
        category="skill",
    ),
    
    Question(
        id="skill_005",
        text="If you had to teach a 10-year-old something, what would you pick?\n💻 How to make a simple game or website\n🔧 How machines work (gears, engines)\n🏗️ How bridges stay up\n🧬 How the human body works\n⚡ How smartphones and circuits work",
        stage=ConversationStage.SKILL_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=3,
        tie_breaker_priority=4,
        category="skill",
    ),
    
    # ── WORKSTYLE ASSESSMENT ──────────────────────────────────────────────
    Question(
        id="workstyle_001",
        text="Think about your ideal work environment. Which sounds most appealing?\n💻 Working at a desk with a computer, solving complex problems\n🏭 Working in a lab or workshop with tools and equipment\n🏗️ Working on-site at construction or project locations\n🏥 Working in a hospital or research lab\n🔬 Working in a tech lab with electronic equipment\n\nWhere do you see yourself thriving?",
        stage=ConversationStage.WORKSTYLE_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=5,
        category="workstyle",
    ),
    
    Question(
        id="workstyle_002",
        text="How do you prefer to work?\n👤 Independently, focusing deeply on my own tasks\n👥 In a team, collaborating and sharing ideas\n🔄 Mix of both, depending on the project\n\nWhat's your natural style?",
        stage=ConversationStage.WORKSTYLE_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Electronics"],
        difficulty=2,
        tie_breaker_priority=3,
        category="workstyle",
    ),
    
    Question(
        id="workstyle_003",
        text="What kind of impact do you want your work to have?\n🌐 Create software that millions use daily\n🚗 Build machines and systems that improve lives\n🏙️ Design infrastructure that shapes cities\n💊 Contribute to healthcare and save lives\n📱 Develop cutting-edge electronic devices\n\nWhat drives you?",
        stage=ConversationStage.WORKSTYLE_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=4,
        category="workstyle",
    ),
    
    Question(
        id="workstyle_004",
        text="10 years from now, which headline would make you proudest?\n💻 'AI breakthrough by [Your Name] changes tech forever'\n🚗 'Revolutionary vehicle design wins engineering award'\n🏗️ 'Iconic building designed by [Your Name] opens'\n💊 'Medical innovation saves thousands of lives'\n⚡ 'Next-gen chip technology unveiled'",
        stage=ConversationStage.WORKSTYLE_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=3,
        category="workstyle",
    ),
    
    Question(
        id="workstyle_005",
        text="Which work environment sounds most appealing?\n💻 Tech campus with gaming zones and hackathons\n🏭 Factory floor with heavy machinery and prototypes\n🏗️ Construction sites and architectural studios\n🏥 Hospital labs and research facilities\n🔬 Clean rooms and electronics labs",
        stage=ConversationStage.WORKSTYLE_ASSESSMENT,
        mapped_branches=["CS", "Mechanical", "Civil", "Medical", "Electronics"],
        difficulty=2,
        tie_breaker_priority=2,
        category="workstyle",
    ),
    
    # ── TIE BREAKER ───────────────────────────────────────────────────────
    Question(
        id="tiebreaker_001",
        text="I see you have strong aptitude for multiple branches! Let me ask: would you rather spend your day writing code or working with physical components?",
        stage=ConversationStage.TIE_BREAKER,
        mapped_branches=["CS", "Mechanical", "Electronics"],
        difficulty=4,
        tie_breaker_priority=10,
        category="tiebreaker",
    ),
    
    Question(
        id="tiebreaker_002",
        text="Here's a key question: do you prefer work where you can see and touch the results (like a machine or building), or work that's more abstract (like software or algorithms)?",
        stage=ConversationStage.TIE_BREAKER,
        mapped_branches=["CS", "Mechanical", "Civil", "Electronics"],
        difficulty=4,
        tie_breaker_priority=9,
        category="tiebreaker",
    ),
    
    Question(
        id="tiebreaker_003",
        text="Final clarifying question: imagine you're stuck on a problem. Would you rather debug code line by line, or troubleshoot a physical system with tools?",
        stage=ConversationStage.TIE_BREAKER,
        mapped_branches=["CS", "Mechanical", "Electronics"],
        difficulty=4,
        tie_breaker_priority=8,
        category="tiebreaker",
    ),
    
    # ── BRANCH PREDICTION (Confirmation) ──────────────────────────────────
    Question(
        id="branch_confirm_001",
        text="Based on our conversation, I believe {branch} Engineering is your best fit. Does this feel right to you, or would you prefer a different branch?",
        stage=ConversationStage.BRANCH_PREDICTION,
        mapped_branches=["CS", "Electronics", "Mechanical", "Civil", "Medical"],
        difficulty=1,
        tie_breaker_priority=0,
        category="confirmation",
    ),
]


class QuestionBank:
    """Question bank manager"""
    
    def __init__(self):
        self.questions = {q.id: q for q in QUESTION_BANK}
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a question by ID"""
        return self.questions.get(question_id)
    
    def get_questions_for_stage(self, stage: ConversationStage) -> List[Question]:
        """Get all questions for a specific stage"""
        return [q for q in QUESTION_BANK if q.stage == stage]
    
    def get_next_question(
        self,
        stage: ConversationStage,
        asked_ids: List[str],
        branch_scores: Optional[Dict[str, float]] = None,
        session_id: Optional[str] = None,
    ) -> Optional[Question]:
        """
        Get the next question for a stage with randomization.
        
        Args:
            stage: Current conversation stage
            asked_ids: List of already asked question IDs
            branch_scores: Current branch scores (for tie-breaker selection)
            session_id: Session ID for seeding randomization (ensures consistency within session)
        
        Returns:
            Next question or None if no questions available
        """
        candidates = self.get_questions_for_stage(stage)
        
        # Filter out already asked questions
        unasked = [q for q in candidates if q.id not in asked_ids]
        
        if not unasked:
            return None
        
        # For tie-breaker, select based on priority and relevant branches
        if stage == ConversationStage.TIE_BREAKER and branch_scores:
            # Get top 2 branches
            top_branches = sorted(branch_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            top_branch_names = [b[0] for b in top_branches]
            
            # Filter questions relevant to top branches
            relevant = [
                q for q in unasked
                if any(branch in q.mapped_branches for branch in top_branch_names)
            ]
            
            if relevant:
                # Sort by tie-breaker priority
                relevant.sort(key=lambda q: q.tie_breaker_priority, reverse=True)
                return relevant[0]
        
        # For branch confirmation, format the question with the predicted branch
        if stage == ConversationStage.BRANCH_PREDICTION and branch_scores:
            top_branch = max(branch_scores, key=branch_scores.get)
            question = unasked[0]
            # Replace {branch} placeholder with actual branch
            formatted_text = question.text.replace("{branch}", top_branch)
            # Create a new question with formatted text
            return Question(
                id=question.id,
                text=formatted_text,
                stage=question.stage,
                mapped_branches=question.mapped_branches,
                difficulty=question.difficulty,
                tie_breaker_priority=question.tie_breaker_priority,
                category=question.category,
            )
        
        # For other stages, randomize selection to provide variety
        # Use session_id as seed for consistency within a session
        if session_id:
            # Create a deterministic but session-specific random order
            random.seed(hash(session_id + stage.value))
            shuffled = list(unasked)
            random.shuffle(shuffled)
            random.seed()  # Reset seed
            return shuffled[0]
        
        # Fallback: return first unasked question
        return unasked[0]
    
    def get_question_count(self, stage: ConversationStage) -> int:
        """Get total number of questions for a stage"""
        return len(self.get_questions_for_stage(stage))


# Global question bank instance
question_bank = QuestionBank()
