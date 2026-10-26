# 🎯 Pathfinder Career Counseling Workflow - Complete Redesign Plan

**Date**: June 20, 2026  
**Status**: Design Phase - Implementation Pending  
**Goal**: Transform generic chatbot into structured career counseling system

---

## 📋 Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Problem Statement](#problem-statement)
3. [New Workflow Design](#new-workflow-design)
4. [Architecture Overview](#architecture-overview)
5. [Implementation Plan](#implementation-plan)
6. [Database Schema Extensions](#database-schema-extensions)
7. [API Endpoints](#api-endpoints)
8. [Frontend Changes](#frontend-changes)
9. [Timeline & Milestones](#timeline--milestones)

---

## 🔍 Current State Analysis

### Existing System Overview

**Current Flow**:

```
User → Initial Form (Rank, Budget, Location) → Adaptive Questions (5-12) → Branch Recommendation → College List
```

**Current Components**:

1. **Backend (`backend/main.py`)**:
   - `/session/start` - Creates session with initial form data
   - `/chat` - Handles Q&A exchanges using AdaptiveQuestionEngine
   - Completes after 5-12 questions based on confidence threshold
   - Returns branch recommendation + college list

2. **Engines**:
   - `AdaptiveQuestionEngine` - Trait-based branch matching (10 traits × 5 branches)
   - `recommendation.py` - College recommendations using ML cutoff predictions
   - Question bank with 100+ questions across 10 trait dimensions

3. **Frontend (`frontend/src/App.jsx`)**:
   - Landing page → Form → Chat → Results
   - Linear flow with no branching paths
   - Results show: recommended branch, colleges (Dream/Moderate/Safe), trait breakdown

4. **Database**:
   - MongoDB collections: users, chats, resumes, roadmaps, skill_assessments, internships
   - Currently only users and chats are actively used
   - Other collections ready but not integrated

### Strengths ✅

1. **Solid Foundation**: MongoDB persistence, ML predictions, adaptive questioning
2. **Good UI/UX**: Modern, responsive interface with glass-morphism design
3. **Data-Driven**: Real JoSAA data, XGBoost cutoff model (10.3% MAPE)
4. **Persistence**: Auto-save user profiles and chat history
5. **Scalability**: Clean architecture with layers (API → Service → Repository → Database)

### Weaknesses ❌

1. **No Career Goals**: System assumes "engineering branch selection" is the only goal
2. **One-Shot Process**: After results, user has nowhere to go
3. **Generic Chatbot Feel**: Post-results chat has no context or purpose
4. **Unused Database Collections**: Roadmaps, assessments, internships exist but aren't used
5. **No Progress Tracking**: No way to track user's learning journey
6. **No Skill Gap Analysis**: System doesn't identify what skills user needs to learn
7. **No Personalization**: Every user gets same adaptive questions regardless of career goal
8. **Missing Career Paths**: Only supports engineering students, no CS-specific career paths

---

## 🎯 Problem Statement

**Current Issue**: The application behaves like a one-time quiz that gives a branch recommendation. There's no ongoing career counseling, skill development guidance, or personalized learning paths.

**User Pain Points**:

- "What do I do after knowing my branch recommendation?"
- "How do I prepare for my target role (AI Engineer, Full Stack Developer, etc.)?"
- "What skills am I missing?"
- "What courses/projects should I do?"
- "Where can I find internships?"
- "How do I track my progress?"

---

## 🚀 New Workflow Design

### High-Level Workflow (7 Stages)

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  1. USER ONBOARDING                                                  │
│     ├─ Profile Info (Name, Email, College, Branch, Year, CGPA)      │
│     ├─ Academic Details (JEE Rank, Skills, Projects)                │
│     └─ Save to MongoDB (users collection)                           │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  2. CAREER GOAL SELECTION                                            │
│     ├─ Present 6 career paths:                                       │
│     │  • AI/ML Engineer                                              │
│     │  • Software Engineer (SDE)                                     │
│     │  • Data Scientist                                              │
│     │  • Full Stack Developer                                        │
│     │  • Cybersecurity Engineer                                      │
│     │  • Other (Custom Path)                                         │
│     └─ Save selected career goal                                     │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  3. SKILL ASSESSMENT                                                 │
│     ├─ Dynamic questionnaire based on selected career goal          │
│     ├─ Technical skills (Programming, DSA, ML, Web Dev, etc.)       │
│     ├─ Soft skills (Communication, Leadership, Teamwork)            │
│     ├─ Calculate skill scores (0-100)                               │
│     └─ Save to MongoDB (skill_assessments collection)               │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  4. SKILL GAP ANALYSIS                                               │
│     ├─ Compare current skills with target role requirements         │
│     ├─ Identify missing/weak skills                                 │
│     ├─ Prioritize skills by importance                              │
│     └─ Generate recommendations                                      │
│                                                                      │
```

├──────────────────────────────────────────────────────────────────────┤
│ │
│ 5. PERSONALIZED ROADMAP GENERATION │
│ ├─ AI-generated learning path with milestones │
│ ├─ Timeline (weeks/months) │
│ ├─ Resources (courses, books, projects) │
│ ├─ Prerequisites and dependencies │
│ └─ Save to MongoDB (roadmaps collection) │
│ │
├──────────────────────────────────────────────────────────────────────┤
│ │
│ 6. PROGRESS TRACKING │
│ ├─ Weekly check-ins │
│ ├─ Milestone completion tracking │
│ ├─ Update skill scores │
│ └─ Adjust roadmap based on progress │
│ │
├──────────────────────────────────────────────────────────────────────┤
│ │
│ 7. INTERNSHIP RECOMMENDATIONS │
│ ├─ Based on current skill level │
│ ├─ Match with career goal │
│ ├─ Filtered by eligibility │
│ └─ Save to MongoDB (internship_recommendations collection) │
│ │
├──────────────────────────────────────────────────────────────────────┤
│ │
│ ONGOING: CAREER CHAT (Context-Aware AI Assistant) │
│ ├─ Access to user profile, roadmap, assessments │
│ ├─ Access to previous conversations │
│ ├─ Provide personalized career advice │
│ └─ Help with doubts, resources, motivation │
│ │
└──────────────────────────────────────────────────────────────────────┘

```

---

## 🏗️ Architecture Overview

### System Architecture (Layered)

```

┌────────────────────────────────────────────────────────────────────┐
│ FRONTEND LAYER │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ React Components │ │
│ │ ├─ OnboardingForm │ │
│ │ ├─ CareerGoalSelector │ │
│ │ ├─ SkillAssessment │ │
│ │ ├─ SkillGapDashboard │ │
│ │ ├─ RoadmapView │ │
│ │ ├─ ProgressTracker │ │
│ │ ├─ InternshipBoard │ │
│ │ └─ CareerChat │ │
│ └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
↕ HTTP/REST
┌────────────────────────────────────────────────────────────────────┐
│ API LAYER (FastAPI) │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Endpoints │ │
│ │ ├─ /api/onboarding/complete │ │
│ │ ├─ /api/career-goals (GET/POST) │ │
│ │ ├─ /api/skill-assessment/start │ │
│ │ ├─ /api/skill-assessment/submit │ │
│ │ ├─ /api/skill-gap/analyze │ │
│ │ ├─ /api/roadmap/generate │ │
│ │ ├─ /api/roadmap/{id}/progress (PUT) │ │
│ │ ├─ /api/internships/recommend │ │
│ │ └─ /api/career-chat (with context) │ │
│ └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
↕
┌────────────────────────────────────────────────────────────────────┐
│ SERVICE LAYER │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Services │ │
│ │ ├─ CareerGoalService - Manages career paths & requirements │ │
│ │ ├─ SkillAssessmentService - Dynamic assessments │ │
│ │ ├─ SkillGapService - Gap analysis algorithms │ │
│ │ ├─ RoadmapGeneratorService - AI roadmap creation │ │
│ │ ├─ ProgressTrackerService - Track completion │ │
│ │ ├─ InternshipService - Match & recommend internships │ │
│ │ └─ ContextualChatService - Context-aware AI chat │ │
│ └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
↕
┌────────────────────────────────────────────────────────────────────┐
│ ENGINE LAYER │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Engines (Keep Existing + Add New) │ │
│ │ ├─ AdaptiveQuestionEngine (existing) │ │
│ │ ├─ RecommendationEngine (existing) │ │
│ │ ├─ SkillMatchingEngine (NEW) │ │
│ │ ├─ RoadmapEngine (NEW) │ │
│ │ └─ ContextEngine (NEW) │ │
│ └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
↕
┌────────────────────────────────────────────────────────────────────┐
│ REPOSITORY LAYER │
│ (Existing - No changes needed) │
│ └─ CRUD operations for all collections │
└────────────────────────────────────────────────────────────────────┘
↕
┌────────────────────────────────────────────────────────────────────┐
│ DATABASE LAYER (MongoDB) │
│ └─ 6 collections (all now fully utilized) │
└────────────────────────────────────────────────────────────────────┘

```

---

```
