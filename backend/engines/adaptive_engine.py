from __future__ import annotations

import math
import re
from copy import deepcopy
from typing import Any


TRAITS = [
    "hardware_interest",
    "software_interest",
    "analytical_thinking",
    "creativity",
    "leadership",
    "teamwork",
    "biology_interest",
    "design_interest",
    "entrepreneurship",
    "research_interest",
]

BRANCHES = ["CS", "Electronics", "Mechanical", "Civil", "Medical"]

CONFIDENCE_THRESHOLD = 0.85
DEFAULT_MAX_QUESTIONS = 12
SIMILARITY_THRESHOLD = 0.72
TARGET_TRAIT_EVIDENCE = 2.5

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "do",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "this",
    "to",
    "up",
    "we",
    "when",
    "with",
    "would",
    "you",
    "your",
}

YES_WORDS = {
    "yes",
    "yeah",
    "yep",
    "yup",
    "absolutely",
    "definitely",
    "sure",
    "love",
    "enjoy",
    "like",
    "prefer",
}

NO_WORDS = {
    "no",
    "not",
    "never",
    "dont",
    "don't",
    "dislike",
    "hate",
    "avoid",
    "boring",
}

UNCERTAIN_WORDS = {
    "maybe",
    "sometimes",
    "depends",
    "unsure",
    "not sure",
    "kind of",
    "a bit",
}

TRAIT_KEYWORDS = {
    "hardware_interest": [
        "hardware",
        "gadget",
        "device",
        "machine",
        "tool",
        "circuit",
        "sensor",
        "motor",
        "robot",
        "electronics",
        "prototype",
        "solder",
        "repair",
        "mechanical",
        "hands-on",
        "hands on",
    ],
    "software_interest": [
        "software",
        "code",
        "coding",
        "programming",
        "program",
        "app",
        "website",
        "script",
        "algorithm",
        "ai",
        "backend",
        "frontend",
        "debug",
        "automation",
        "data",
    ],
    "analytical_thinking": [
        "analyze",
        "analytical",
        "logic",
        "logical",
        "pattern",
        "optimize",
        "root cause",
        "evidence",
        "systematic",
        "compare",
        "diagnose",
        "quantify",
        "model",
        "reason",
        "step by step",
    ],
    "creativity": [
        "creative",
        "creativity",
        "imagine",
        "novel",
        "original",
        "brainstorm",
        "ideas",
        "concept",
        "artistic",
        "innovative",
        "story",
        "invent",
        "visual",
    ],
    "leadership": [
        "lead",
        "leader",
        "leadership",
        "manage",
        "manager",
        "captain",
        "mentor",
        "ownership",
        "organize",
        "coordinate",
        "motivate",
        "delegate",
        "decision",
    ],
    "teamwork": [
        "team",
        "teamwork",
        "collaborate",
        "collaboration",
        "group",
        "together",
        "partner",
        "pair",
        "feedback",
        "support",
        "listen",
        "help others",
    ],
    "biology_interest": [
        "biology",
        "biotech",
        "biomedical",
        "medical",
        "medicine",
        "anatomy",
        "genetics",
        "genes",
        "human body",
        "disease",
        "health",
        "physiology",
        "diagnostics",
    ],
    "design_interest": [
        "design",
        "sketch",
        "blueprint",
        "layout",
        "ui",
        "ux",
        "cad",
        "aesthetic",
        "visual",
        "interface",
        "structure",
        "form factor",
        "ergonomic",
    ],
    "entrepreneurship": [
        "startup",
        "business",
        "market",
        "pitch",
        "founder",
        "venture",
        "customer",
        "revenue",
        "product",
        "monetize",
        "ownership",
        "sell",
        "profit",
    ],
    "research_interest": [
        "research",
        "paper",
        "papers",
        "experiment",
        "investigate",
        "hypothesis",
        "discovery",
        "publish",
        "journal",
        "study",
        "literature",
        "simulation",
        "lab",
    ],
}

TRAIT_OPPOSITES = {
    "hardware_interest": ["software_interest"],
    "software_interest": ["hardware_interest"],
    "entrepreneurship": ["research_interest"],
    "research_interest": ["entrepreneurship"],
}

BRANCH_PROFILES = {
    "CS": {
        "hardware_interest": 0.25,
        "software_interest": 0.98,
        "analytical_thinking": 0.92,
        "creativity": 0.62,
        "leadership": 0.45,
        "teamwork": 0.56,
        "biology_interest": 0.10,
        "design_interest": 0.48,
        "entrepreneurship": 0.58,
        "research_interest": 0.72,
    },
    "Electronics": {
        "hardware_interest": 0.90,
        "software_interest": 0.58,
        "analytical_thinking": 0.88,
        "creativity": 0.54,
        "leadership": 0.44,
        "teamwork": 0.53,
        "biology_interest": 0.08,
        "design_interest": 0.46,
        "entrepreneurship": 0.46,
        "research_interest": 0.64,
    },
    "Mechanical": {
        "hardware_interest": 0.95,
        "software_interest": 0.22,
        "analytical_thinking": 0.78,
        "creativity": 0.74,
        "leadership": 0.58,
        "teamwork": 0.64,
        "biology_interest": 0.06,
        "design_interest": 0.70,
        "entrepreneurship": 0.54,
        "research_interest": 0.42,
    },
    "Civil": {
        "hardware_interest": 0.56,
        "software_interest": 0.18,
        "analytical_thinking": 0.74,
        "creativity": 0.84,
        "leadership": 0.82,
        "teamwork": 0.86,
        "biology_interest": 0.05,
        "design_interest": 0.96,
        "entrepreneurship": 0.63,
        "research_interest": 0.36,
    },
    "Medical": {
        "hardware_interest": 0.14,
        "software_interest": 0.10,
        "analytical_thinking": 0.82,
        "creativity": 0.48,
        "leadership": 0.62,
        "teamwork": 0.84,
        "biology_interest": 0.99,
        "design_interest": 0.22,
        "entrepreneurship": 0.28,
        "research_interest": 0.92,
    },
}


def _question(
    trait: str,
    number: int,
    text: str,
    category: str,
    difficulty: int,
    branches_affected: list[str],
    semantic_group: str,
    secondary_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    weights = {trait: 1.0}
    if secondary_weights:
        weights.update(secondary_weights)
    return {
        "id": f"{trait}_{number:02d}",
        "text": text,
        "trait_weights": weights,
        "branches_affected": branches_affected,
        "category": category,
        "difficulty": difficulty,
        "semantic_group": semantic_group,
    }


QUESTION_BANK = [
    _question("hardware_interest", 1, "When a device stops working, do you feel like opening it up to understand the hardware issue?", "interest", 2, ["Electronics", "Mechanical"], "repair_device", {"analytical_thinking": 0.35}),
    _question("hardware_interest", 2, "Would you rather spend an afternoon with a toolkit and sensors than only on a laptop screen?", "interest", 2, ["Electronics", "Mechanical", "Civil"], "toolkit_sensors", {"software_interest": 0.25}),
    _question("hardware_interest", 3, "Do physical prototypes excite you more than purely digital mockups?", "aptitude", 2, ["Mechanical", "Electronics", "Civil", "CS"], "prototype_vs_mockup", {"design_interest": 0.25}),
    _question("hardware_interest", 4, "If your college had a makerspace, would motors, boards, and fabrication tools pull you in first?", "interest", 2, ["Electronics", "Mechanical"], "makerspace_tools", {"creativity": 0.20}),
    _question("hardware_interest", 5, "Would debugging a robot arm feel satisfying even before the software is perfect?", "aptitude", 3, ["Mechanical", "Electronics", "CS"], "debug_robot_arm", {"analytical_thinking": 0.30}),
    _question("hardware_interest", 6, "Do you enjoy the idea of building something you can touch, test, and physically improve?", "workstyle", 2, ["Mechanical", "Civil", "Electronics"], "touch_and_test", {"creativity": 0.20}),
    _question("hardware_interest", 7, "When you see a drone or electric vehicle, are you drawn to the components inside it?", "interest", 2, ["Electronics", "Mechanical"], "drone_components", {"research_interest": 0.20}),
    _question("hardware_interest", 8, "Would you volunteer for the lab station that involves wiring, instruments, and hardware troubleshooting?", "workstyle", 3, ["Electronics", "Mechanical"], "lab_station", {"teamwork": 0.15}),
    _question("hardware_interest", 9, "Does assembling systems from parts sound more rewarding than only configuring software features?", "interest", 3, ["Mechanical", "Electronics", "CS"], "assemble_parts", {"software_interest": 0.30}),
    _question("hardware_interest", 10, "Would you trust your instincts more around machines and equipment than around codebases and APIs?", "aptitude", 3, ["Mechanical", "Electronics", "CS", "Civil"], "machines_vs_apis", {"analytical_thinking": 0.25}),

    _question("software_interest", 1, "Do you get excited by the idea of writing code that automates a repetitive task?", "interest", 2, ["CS", "Electronics"], "automate_task", {"analytical_thinking": 0.35}),
    _question("software_interest", 2, "Would building an app from scratch feel more fun than building a physical prototype?", "interest", 2, ["CS", "Electronics", "Mechanical"], "app_vs_prototype", {"hardware_interest": 0.30}),
    _question("software_interest", 3, "When you imagine solving problems, do you naturally think in logic flows, functions, or systems?", "aptitude", 3, ["CS", "Electronics"], "logic_flows", {"analytical_thinking": 0.35}),
    _question("software_interest", 4, "Do APIs, data models, and software architecture sound interesting to you?", "aptitude", 3, ["CS", "Electronics"], "api_architecture", {"research_interest": 0.20}),
    _question("software_interest", 5, "Would you enjoy improving an algorithm even if nobody sees the interface change?", "workstyle", 3, ["CS", "Electronics"], "improve_algorithm", {"analytical_thinking": 0.40}),
    _question("software_interest", 6, "Does debugging code feel like a challenge you would willingly stay with until it works?", "workstyle", 3, ["CS", "Electronics"], "debug_code", {"analytical_thinking": 0.35}),
    _question("software_interest", 7, "Would you rather ship a useful digital feature than assemble a physical device?", "interest", 2, ["CS", "Electronics", "Mechanical"], "ship_feature", {"entrepreneurship": 0.20}),
    _question("software_interest", 8, "If given free time, would you explore a new programming language or framework on your own?", "interest", 2, ["CS"], "learn_framework", {"research_interest": 0.20}),
    _question("software_interest", 9, "Do you enjoy turning vague ideas into step-by-step software workflows?", "aptitude", 3, ["CS", "Electronics"], "workflow_design", {"design_interest": 0.20}),
    _question("software_interest", 10, "Would version control, code reviews, and product sprints feel natural to you?", "workstyle", 3, ["CS", "Electronics"], "code_reviews", {"teamwork": 0.20}),

    _question("analytical_thinking", 1, "When a problem looks messy, do you instinctively break it into smaller parts?", "aptitude", 2, BRANCHES, "break_into_parts"),
    _question("analytical_thinking", 2, "Do logic puzzles or pattern-based questions usually energize you?", "aptitude", 2, ["CS", "Electronics", "Mechanical"], "logic_puzzles", {"software_interest": 0.15}),
    _question("analytical_thinking", 3, "Would you rather compare evidence carefully before deciding than go with your first instinct?", "decision", 2, BRANCHES, "compare_evidence"),
    _question("analytical_thinking", 4, "If a result seems wrong, do you like tracing the exact root cause?", "aptitude", 3, BRANCHES, "trace_root_cause"),
    _question("analytical_thinking", 5, "Do spreadsheets, measurements, or structured data usually help you think clearly?", "workstyle", 2, ["CS", "Electronics", "Civil", "Medical"], "structured_data"),
    _question("analytical_thinking", 6, "Would you enjoy evaluating trade-offs with numbers instead of relying only on opinions?", "decision", 3, BRANCHES, "tradeoff_numbers", {"leadership": 0.15}),
    _question("analytical_thinking", 7, "Do you notice assumptions quickly when people explain their solutions?", "aptitude", 3, BRANCHES, "spot_assumptions"),
    _question("analytical_thinking", 8, "When you study, do step-by-step derivations help more than broad summaries?", "aptitude", 2, ["CS", "Electronics", "Mechanical", "Medical"], "step_by_step"),
    _question("analytical_thinking", 9, "Would you be comfortable designing a test just to verify one hypothesis cleanly?", "research", 3, BRANCHES, "verify_hypothesis", {"research_interest": 0.25}),
    _question("analytical_thinking", 10, "Do you enjoy ranking options with clear criteria before committing to one path?", "decision", 2, BRANCHES, "rank_options", {"leadership": 0.15}),

    _question("creativity", 1, "Do open-ended problems feel exciting because you can invent your own approach?", "interest", 2, ["Civil", "Mechanical", "CS"], "open_ended_problems"),
    _question("creativity", 2, "Would you rather create a fresh concept than repeat a known solution exactly?", "interest", 2, ["Civil", "Mechanical", "CS", "Electronics"], "fresh_concept"),
    _question("creativity", 3, "Do you enjoy sketching ideas, layouts, or concepts before they are fully defined?", "design", 2, ["Civil", "Mechanical", "CS"], "sketch_ideas", {"design_interest": 0.35}),
    _question("creativity", 4, "When brainstorming, are you usually the person adding unusual possibilities?", "team", 2, ["Civil", "Mechanical", "CS"], "unusual_possibilities", {"teamwork": 0.15}),
    _question("creativity", 5, "Would you enjoy improving both function and originality at the same time?", "design", 3, ["Civil", "Mechanical", "CS", "Electronics"], "function_and_originality", {"design_interest": 0.25}),
    _question("creativity", 6, "Do you like turning rough ideas into something visually or conceptually polished?", "design", 3, ["Civil", "Mechanical", "CS"], "polish_ideas", {"design_interest": 0.30}),
    _question("creativity", 7, "If rules are unclear, do you still feel comfortable experimenting with your own style?", "workstyle", 3, ["Civil", "Mechanical", "CS"], "own_style", {"entrepreneurship": 0.15}),
    _question("creativity", 8, "Would a blank canvas or undefined challenge motivate you more than scare you?", "interest", 2, ["Civil", "Mechanical", "CS"], "blank_canvas"),
    _question("creativity", 9, "Do you often imagine how products, systems, or spaces could be more elegant?", "design", 3, ["Civil", "Mechanical", "CS", "Electronics"], "more_elegant", {"design_interest": 0.30}),
    _question("creativity", 10, "Would you rather prototype several new ideas than optimize one safe solution immediately?", "innovation", 3, ["Civil", "Mechanical", "CS"], "prototype_new_ideas", {"entrepreneurship": 0.20}),

    _question("leadership", 1, "In group projects, do you naturally take ownership of clarifying the plan?", "team", 2, ["Civil", "Mechanical", "Medical", "CS"], "clarify_plan", {"teamwork": 0.35}),
    _question("leadership", 2, "Would you be comfortable making a final call when the team is stuck?", "decision", 3, ["Civil", "Mechanical", "Medical", "CS"], "final_call", {"teamwork": 0.25}),
    _question("leadership", 3, "Do you like coordinating deadlines and keeping people aligned?", "team", 2, ["Civil", "Mechanical", "Medical"], "coordinate_deadlines", {"teamwork": 0.35}),
    _question("leadership", 4, "If others are unsure, do you usually step forward and structure the next move?", "decision", 3, ["Civil", "Mechanical", "Medical", "CS"], "structure_next_move", {"analytical_thinking": 0.15}),
    _question("leadership", 5, "Would presenting your team's solution to others feel energizing?", "communication", 2, ["Civil", "Mechanical", "Medical", "CS"], "present_solution", {"teamwork": 0.25}),
    _question("leadership", 6, "Do you enjoy mentoring classmates once you understand something well?", "team", 2, ["Civil", "Medical", "CS"], "mentor_classmates", {"teamwork": 0.30}),
    _question("leadership", 7, "Would you rather shape the vision of a project than only execute assigned tasks?", "career", 3, ["Civil", "Mechanical", "CS"], "shape_vision", {"entrepreneurship": 0.25}),
    _question("leadership", 8, "When a project slips, are you willing to delegate and reset priorities?", "decision", 4, ["Civil", "Mechanical", "Medical"], "delegate_priorities", {"teamwork": 0.35}),
    _question("leadership", 9, "Do you feel responsible for team outcomes even when the work is shared?", "team", 3, ["Civil", "Mechanical", "Medical", "CS"], "team_outcomes", {"teamwork": 0.30}),
    _question("leadership", 10, "Would running a student chapter, event, or build team appeal to you?", "career", 2, ["Civil", "Mechanical", "CS", "Electronics"], "student_chapter", {"entrepreneurship": 0.15}),

    _question("teamwork", 1, "Do you usually enjoy collaborating closely with others rather than working alone the whole time?", "team", 2, BRANCHES, "collaborate_closely"),
    _question("teamwork", 2, "Would pair work or group brainstorming improve your energy on a hard task?", "team", 2, BRANCHES, "group_brainstorming"),
    _question("teamwork", 3, "Do you seek feedback early instead of waiting until the end?", "team", 2, BRANCHES, "seek_feedback", {"leadership": 0.15}),
    _question("teamwork", 4, "Are you comfortable sharing credit openly when the result is strong?", "team", 2, BRANCHES, "share_credit"),
    _question("teamwork", 5, "If a teammate gets stuck, do you usually step in to help without being asked?", "team", 2, BRANCHES, "help_teammate", {"leadership": 0.15}),
    _question("teamwork", 6, "Do cross-functional teams sound appealing even when communication takes effort?", "workstyle", 3, ["Civil", "Medical", "CS", "Electronics"], "cross_functional"),
    _question("teamwork", 7, "Would you rather build something meaningful with a team than finish a solo project faster?", "team", 2, BRANCHES, "team_vs_solo"),
    _question("teamwork", 8, "Do you listen first and adapt your message depending on who you are speaking with?", "communication", 3, BRANCHES, "listen_and_adapt"),
    _question("teamwork", 9, "Can you compromise on one detail if it helps the whole project move forward?", "decision", 3, BRANCHES, "compromise_detail"),
    _question("teamwork", 10, "Would studio, lab, or build-team environments suit you better than isolated work only?", "workstyle", 2, BRANCHES, "lab_team_environment"),

    _question("biology_interest", 1, "Do topics like the human body, genetics, or disease mechanisms genuinely hold your attention?", "interest", 2, ["Medical"], "human_body_topics", {"research_interest": 0.25}),
    _question("biology_interest", 2, "Would you enjoy a lab where the focus is living systems rather than machines?", "interest", 2, ["Medical", "CS"], "living_systems_lab", {"hardware_interest": 0.20}),
    _question("biology_interest", 3, "If you read science news, are medical or biotech breakthroughs the stories you open first?", "interest", 2, ["Medical"], "biotech_news", {"research_interest": 0.25}),
    _question("biology_interest", 4, "Would learning anatomy or physiology feel more natural than learning machine components?", "aptitude", 3, ["Medical", "Mechanical"], "anatomy_vs_components", {"hardware_interest": 0.25}),
    _question("biology_interest", 5, "Does the idea of improving healthcare through science feel personally meaningful to you?", "career", 2, ["Medical"], "healthcare_meaning", {"teamwork": 0.15}),
    _question("biology_interest", 6, "Would you willingly spend time understanding how cells, tissues, or genes interact?", "research", 3, ["Medical"], "cells_tissues_genes", {"research_interest": 0.30}),
    _question("biology_interest", 7, "Do diagnostics, medical devices, or biotech products sound more interesting than pure infrastructure work?", "interest", 3, ["Medical", "Electronics", "Civil"], "diagnostics_vs_infra", {"design_interest": 0.15}),
    _question("biology_interest", 8, "Would a biology-heavy elective attract you even if it required detailed memorization?", "aptitude", 3, ["Medical"], "biology_elective", {"analytical_thinking": 0.15}),
    _question("biology_interest", 9, "Do you find yourself curious about how lifestyle, disease, and treatment connect?", "interest", 2, ["Medical"], "lifestyle_disease_treatment", {"research_interest": 0.20}),
    _question("biology_interest", 10, "Would you enjoy work that sits near medicine, diagnostics, or biomedical innovation?", "career", 3, ["Medical", "CS", "Electronics"], "biomedical_innovation", {"entrepreneurship": 0.15}),

    _question("design_interest", 1, "Do layouts, blueprints, interfaces, or visual structures catch your eye quickly?", "design", 2, ["Civil", "Mechanical", "CS"], "layouts_and_interfaces", {"creativity": 0.30}),
    _question("design_interest", 2, "Would you enjoy shaping how a product, building, or interface feels to use?", "design", 2, ["Civil", "Mechanical", "CS"], "feel_to_use", {"creativity": 0.25}),
    _question("design_interest", 3, "Do you like sketching or mapping ideas before jumping into execution?", "design", 2, ["Civil", "Mechanical", "CS"], "sketch_before_execution", {"analytical_thinking": 0.15}),
    _question("design_interest", 4, "Would CAD tools, wireframes, or concept boards feel appealing to you?", "design", 3, ["Civil", "Mechanical", "CS", "Electronics"], "cad_wireframes"),
    _question("design_interest", 5, "Do you notice bad design in everyday objects, apps, or spaces faster than most people do?", "design", 2, ["Civil", "Mechanical", "CS"], "notice_bad_design", {"creativity": 0.20}),
    _question("design_interest", 6, "Would you rather refine usability and form than only optimize raw performance?", "design", 3, ["Civil", "Mechanical", "CS"], "usability_and_form", {"software_interest": 0.15}),
    _question("design_interest", 7, "Do you enjoy balancing aesthetics with constraints like cost, safety, or simplicity?", "design", 4, ["Civil", "Mechanical", "CS"], "balance_aesthetics_constraints", {"analytical_thinking": 0.20}),
    _question("design_interest", 8, "Would presenting a polished visual concept be satisfying to you?", "communication", 2, ["Civil", "Mechanical", "CS"], "visual_concept", {"leadership": 0.15}),
    _question("design_interest", 9, "Do spaces, structures, and user flows interest you as much as raw technical specs?", "interest", 3, ["Civil", "CS", "Mechanical"], "spaces_and_user_flows", {"creativity": 0.20}),
    _question("design_interest", 10, "Would you willingly iterate on appearance and user experience several times to get it right?", "workstyle", 3, ["Civil", "CS", "Mechanical"], "iterate_experience", {"teamwork": 0.15}),

    _question("entrepreneurship", 1, "Do you often notice problems that could become useful products or services?", "career", 2, ["CS", "Mechanical", "Civil", "Electronics"], "notice_market_problems", {"creativity": 0.20}),
    _question("entrepreneurship", 2, "Would building something of your own excite you more than joining a very predictable path?", "career", 3, ["CS", "Mechanical", "Civil", "Electronics"], "build_something_own", {"leadership": 0.25}),
    _question("entrepreneurship", 3, "Do customer needs and market fit sound interesting, not just the technical build?", "career", 3, ["CS", "Mechanical", "Civil", "Electronics"], "market_fit", {"teamwork": 0.15}),
    _question("entrepreneurship", 4, "Would pitching an idea publicly feel worth the risk if you believed in it?", "communication", 3, ["CS", "Mechanical", "Civil", "Electronics"], "pitch_idea", {"leadership": 0.25}),
    _question("entrepreneurship", 5, "Do you like the thought of turning an invention or tool into a real product?", "career", 2, ["CS", "Mechanical", "Electronics"], "turn_into_product", {"creativity": 0.20}),
    _question("entrepreneurship", 6, "Would you rather own the outcome of a project than only contribute one part of it?", "career", 3, ["CS", "Mechanical", "Civil", "Electronics"], "own_outcome", {"leadership": 0.25}),
    _question("entrepreneurship", 7, "Do budgets, trade-offs, and resource constraints feel like part of the fun?", "decision", 4, ["CS", "Mechanical", "Civil", "Electronics"], "resource_constraints", {"analytical_thinking": 0.20}),
    _question("entrepreneurship", 8, "Would interviewing users or customers sound as important as building the solution?", "career", 3, ["CS", "Civil", "Mechanical"], "interview_users", {"teamwork": 0.20}),
    _question("entrepreneurship", 9, "Do you feel energized by competition, ownership, and creating value quickly?", "career", 3, ["CS", "Mechanical", "Civil", "Electronics"], "ownership_and_value", {"leadership": 0.20}),
    _question("entrepreneurship", 10, "If a side project gained traction, would you seriously consider growing it into something bigger?", "career", 3, ["CS", "Mechanical", "Civil", "Electronics"], "grow_side_project", {"research_interest": 0.10}),

    _question("research_interest", 1, "Do you enjoy going deep into one question until you really understand it?", "research", 2, ["Medical", "CS", "Electronics"], "go_deep_one_question", {"analytical_thinking": 0.30}),
    _question("research_interest", 2, "Would reading papers or technical articles to explore an idea feel worthwhile to you?", "research", 3, ["Medical", "CS", "Electronics"], "read_papers", {"analytical_thinking": 0.25}),
    _question("research_interest", 3, "Do experiments, simulations, or controlled investigations appeal to you?", "research", 3, ["Medical", "CS", "Electronics", "Mechanical"], "experiments_and_simulations", {"analytical_thinking": 0.30}),
    _question("research_interest", 4, "Would you stay interested in a problem even if the answer took weeks to uncover?", "research", 3, ["Medical", "CS", "Electronics"], "long_horizon_problem"),
    _question("research_interest", 5, "Do unanswered questions motivate you more than finished systems do?", "research", 3, ["Medical", "CS", "Electronics"], "unanswered_questions", {"creativity": 0.15}),
    _question("research_interest", 6, "Would collecting evidence carefully feel better than making a quick guess?", "research", 2, ["Medical", "CS", "Electronics", "Civil"], "collect_evidence", {"analytical_thinking": 0.30}),
    _question("research_interest", 7, "Do labs, study groups, or research mentorships sound attractive to you?", "research", 2, ["Medical", "CS", "Electronics"], "research_mentorship", {"teamwork": 0.15}),
    _question("research_interest", 8, "Would publishing, discovering, or contributing new knowledge feel meaningful?", "career", 3, ["Medical", "CS", "Electronics"], "publish_discover", {"leadership": 0.10}),
    _question("research_interest", 9, "Are you comfortable with ambiguity while evidence is still incomplete?", "research", 4, ["Medical", "CS", "Electronics"], "ambiguity_tolerance", {"analytical_thinking": 0.20}),
    _question("research_interest", 10, "Would you rather test a hypothesis thoroughly than rush to the first workable answer?", "research", 3, ["Medical", "CS", "Electronics", "Mechanical"], "test_hypothesis_thoroughly", {"analytical_thinking": 0.35}),
]

QUESTION_INDEX = {question["id"]: question for question in QUESTION_BANK}


def trait_question_counts() -> dict[str, int]:
    counts = {trait: 0 for trait in TRAITS}
    for question in QUESTION_BANK:
        primary_trait = question["id"].rsplit("_", 1)[0]
        counts[primary_trait] += 1
    return counts


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in STOPWORDS}


def _text_similarity(text_a: str, text_b: str) -> float:
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class AdaptiveQuestionEngine:
    def __init__(self, max_questions: int = DEFAULT_MAX_QUESTIONS):
        self.max_questions = max_questions
        self.question_bank = QUESTION_BANK
        self.question_index = QUESTION_INDEX

    def create_session(
        self,
        *,
        exam_type: str = "jee_main",
        rank: int | None = None,
        budget_lakh: float | None = None,
        preferred_location: str | None = None,
        max_questions: int | None = None,
    ) -> dict[str, Any]:
        session = {
            "exam_type": exam_type,
            "rank": rank,
            "budget_lakh": budget_lakh,
            "preferred_location": preferred_location,
            "max_questions": max_questions or self.max_questions,
            "trait_scores": {trait: 0.5 for trait in TRAITS},
            "trait_evidence": {trait: 0.0 for trait in TRAITS},
            "branch_scores": {branch: 0.5 for branch in BRANCHES},
            "top_branches": [],
            "confidence": 0.0,
            "asked_question_ids": [],
            "asked_question_texts": [],
            "asked_semantic_groups": [],
            "remaining_question_pool": [question["id"] for question in self.question_bank],
            "current_question_id": None,
            "current_question_text": None,
            "current_category": "INTEREST",
            "is_complete": False,
            "answer_history": [],
        }
        self._recompute_branch_state(session)
        return session

    def select_opening_question(self, session: dict[str, Any]) -> dict[str, Any]:
        question = self._select_next_question(session)
        if question is None:
            raise RuntimeError("Adaptive engine could not select an opening question.")
        self._mark_question_asked(session, question)
        return question

    def process_answer(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        answer = answer.strip()
        current_question = self.question_index.get(session.get("current_question_id"))
        if not current_question:
            raise ValueError("No current question available for this session.")

        session["answer_history"].append(
            {
                "question_id": current_question["id"],
                "question_text": current_question["text"],
                "answer": answer,
            }
        )

        self._update_traits_from_answer(session, current_question, answer)
        self._recompute_branch_state(session)

        if self._should_stop(session):
            session["is_complete"] = True
            return {
                "is_complete": True,
                "question": None,
                "top_branches": session["top_branches"],
                "branch_scores": session["branch_scores"],
                "confidence": session["confidence"],
                "trait_breakdown": self._rounded_trait_scores(session),
            }

        next_question = self._select_next_question(session)
        if next_question is None:
            session["is_complete"] = True
            return {
                "is_complete": True,
                "question": None,
                "top_branches": session["top_branches"],
                "branch_scores": session["branch_scores"],
                "confidence": session["confidence"],
                "trait_breakdown": self._rounded_trait_scores(session),
            }

        self._mark_question_asked(session, next_question)
        return {
            "is_complete": False,
            "question": next_question,
            "top_branches": session["top_branches"],
            "branch_scores": session["branch_scores"],
            "confidence": session["confidence"],
            "trait_breakdown": self._rounded_trait_scores(session),
        }

    def build_report(self, session: dict[str, Any]) -> dict[str, Any]:
        top_branch = session["top_branches"][0]["branch"] if session["top_branches"] else None
        standout_traits = sorted(
            session["trait_scores"].items(),
            key=lambda item: item[1],
            reverse=True,
        )[:3]
        standout_text = ", ".join(
            f"{trait.replace('_', ' ')} ({round(score * 100):.0f}%)"
            for trait, score in standout_traits
        )
        return {
            "recommended_branch": top_branch,
            "top_branches": deepcopy(session["top_branches"]),
            "branch_scores": deepcopy(session["branch_scores"]),
            "confidence": session["confidence"],
            "trait_breakdown": self._rounded_trait_scores(session),
            "asked_question_ids": list(session["asked_question_ids"]),
            "remaining_question_pool": list(session["remaining_question_pool"]),
            "branch_summary": (
                f"{top_branch} stands out because your strongest signals cluster around "
                f"{standout_text}."
                if top_branch
                else "Your profile is still broad, so the result should be treated as exploratory."
            ),
        }

    def _rounded_trait_scores(self, session: dict[str, Any]) -> dict[str, float]:
        return {
            trait: round(score, 4)
            for trait, score in session["trait_scores"].items()
        }

    def _update_traits_from_answer(
        self,
        session: dict[str, Any],
        question: dict[str, Any],
        answer: str,
    ) -> None:
        answer_lower = answer.lower()
        short_yes = len(answer_lower.split()) <= 6 and any(word in answer_lower for word in YES_WORDS)
        short_no = len(answer_lower.split()) <= 6 and any(word in answer_lower for word in NO_WORDS)
        positive_hits = sum(1 for word in YES_WORDS if word in answer_lower)
        negative_hits = sum(1 for word in NO_WORDS if word in answer_lower)
        uncertain_hits = sum(1 for word in UNCERTAIN_WORDS if word in answer_lower)

        keyword_hits = {
            trait: sum(1 for keyword in keywords if keyword in answer_lower)
            for trait, keywords in TRAIT_KEYWORDS.items()
        }

        updated_traits: set[str] = set(question["trait_weights"])
        for trait, hits in keyword_hits.items():
            if hits > 0:
                updated_traits.add(trait)

        for trait in updated_traits:
            question_weight = question["trait_weights"].get(trait, 0.18 if keyword_hits[trait] > 0 else 0.0)
            if question_weight <= 0:
                continue

            opposite_pressure = sum(keyword_hits.get(opposite, 0) for opposite in TRAIT_OPPOSITES.get(trait, []))
            signal = 0.5
            signal += min(keyword_hits.get(trait, 0), 3) * 0.12
            signal -= min(opposite_pressure, 2) * 0.10
            signal += min(positive_hits, 3) * 0.04
            signal -= min(negative_hits, 3) * 0.08
            signal -= min(uncertain_hits, 2) * 0.04

            if trait in question["trait_weights"]:
                signal += 0.06
                if short_yes:
                    signal += 0.18
                if short_no:
                    signal -= 0.22

            signal = _clamp(signal)

            current_score = session["trait_scores"][trait]
            current_evidence = session["trait_evidence"][trait]
            new_score = (
                (current_score * current_evidence) + (signal * question_weight)
            ) / (current_evidence + question_weight)

            session["trait_scores"][trait] = round(_clamp(new_score), 4)
            session["trait_evidence"][trait] = round(current_evidence + question_weight, 4)

    def _recompute_branch_state(self, session: dict[str, Any]) -> None:
        trait_scores = session["trait_scores"]
        branch_scores: dict[str, float] = {}

        for branch, profile in BRANCH_PROFILES.items():
            weighted_distance = 0.0
            total_weight = 0.0
            for trait in TRAITS:
                importance = 0.45 + (profile[trait] * 0.55)
                weighted_distance += abs(trait_scores[trait] - profile[trait]) * importance
                total_weight += importance
            alignment = 1.0 - (weighted_distance / total_weight if total_weight else 0.0)
            branch_scores[branch] = round(_clamp(alignment), 4)

        sorted_branches = sorted(
            branch_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        top_branch, top_score = sorted_branches[0]
        second_score = sorted_branches[1][1] if len(sorted_branches) > 1 else 0.0
        gap = max(top_score - second_score, 0.0)
        coverage = sum(
            min(session["trait_evidence"][trait] / TARGET_TRAIT_EVIDENCE, 1.0)
            for trait in TRAITS
        ) / len(TRAITS)
        confidence = _clamp((top_score * 0.40) + (min(gap * 3.0, 1.0) * 0.40) + (coverage * 0.20))

        session["branch_scores"] = branch_scores
        session["top_branches"] = [
            {"branch": branch, "score": round(score, 4)}
            for branch, score in sorted_branches[:3]
        ]
        session["confidence"] = round(confidence, 4)
        session["top_branch"] = top_branch

    def _should_stop(self, session: dict[str, Any]) -> bool:
        return (
            session["confidence"] >= CONFIDENCE_THRESHOLD
            or len(session["asked_question_ids"]) >= session["max_questions"]
        )

    def _select_next_question(self, session: dict[str, Any]) -> dict[str, Any] | None:
        asked_ids = set(session["asked_question_ids"])
        asked_groups = set(session["asked_semantic_groups"])
        asked_texts = session["asked_question_texts"]

        sorted_branches = sorted(
            session["branch_scores"].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        top_score = sorted_branches[0][1]
        competitive_branches = [
            branch for branch, score in sorted_branches
            if top_score - score <= 0.12
        ]
        if len(competitive_branches) < 2:
            competitive_branches = [branch for branch, _score in sorted_branches[:2]]
        competitive_branches = competitive_branches[:3]

        best_question = None
        best_gain = -1.0

        for question in self.question_bank:
            if question["id"] in asked_ids:
                continue
            if question["semantic_group"] in asked_groups:
                continue
            if any(_text_similarity(question["text"], asked_text) >= SIMILARITY_THRESHOLD for asked_text in asked_texts):
                continue

            overlap = len(set(question["branches_affected"]) & set(competitive_branches))
            relevance = 0.65 + (0.35 * (overlap / max(len(competitive_branches), 1)))

            gain = 0.0
            for trait, weight in question["trait_weights"].items():
                branch_values = [BRANCH_PROFILES[branch][trait] for branch in competitive_branches]
                mean_value = sum(branch_values) / len(branch_values)
                variance = sum((value - mean_value) ** 2 for value in branch_values) / len(branch_values)
                uncertainty = 1.0 - min(session["trait_evidence"][trait] / TARGET_TRAIT_EVIDENCE, 1.0)
                gain += (math.sqrt(variance) + 0.02) * uncertainty * (0.8 + 0.2 * weight)

            if len(session["asked_question_ids"]) < 3 and question["difficulty"] >= 4:
                gain *= 0.9

            gain *= relevance

            if gain > best_gain:
                best_gain = gain
                best_question = question

        return best_question

    def _mark_question_asked(self, session: dict[str, Any], question: dict[str, Any]) -> None:
        session["current_question_id"] = question["id"]
        session["current_question_text"] = question["text"]
        session["current_category"] = question["category"].upper()
        session["asked_question_ids"].append(question["id"])
        session["asked_question_texts"].append(question["text"])
        session["asked_semantic_groups"].append(question["semantic_group"])
        session["remaining_question_pool"] = [
            question_id
            for question_id in session["remaining_question_pool"]
            if question_id != question["id"]
        ]
