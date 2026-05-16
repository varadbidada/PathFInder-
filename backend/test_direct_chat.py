#!/usr/bin/env python3
"""
Test chat functionality directly to identify the exact failure point
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm_client import call_llm, check_llm_health
from services.ai_service import extract_signals, get_reactive_question
from engines.conversation_controller import ConversationController
from engines.session_manager import SessionManager

async def test_llm_direct():
    """Test LLM client directly"""
    print("🧪 Testing LLM Client Direct")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Checking LLM health...")
    health = check_llm_health()
    print(f"   Status: {health}")
    
    if not health.get("active_provider"):
        print("❌ No LLM provider active!")
        return False
    
    # Test 2: Simple LLM call
    print("\n2. Testing simple LLM call...")
    try:
        response = call_llm(
            prompt="Say 'Hello' in one word",
            expect_json=False,
            temperature=0.7,
            max_tokens=10,
            retries=1
        )
        print(f"✅ LLM Response: '{response}'")
    except Exception as e:
        print(f"❌ LLM Call failed: {e}")
        return False
    
    # Test 3: Signal extraction
    print("\n3. Testing signal extraction...")
    try:
        signals = await extract_signals(
            user_answer="I love programming and coding",
            question_asked="What do you enjoy?"
        )
        print(f"✅ Signal extraction successful")
        print(f"   Math Aptitude: {signals.Math_Aptitude_ability}")
        print(f"   Logical Thinking: {signals.Logical_Thinking_ability}")
    except Exception as e:
        print(f"❌ Signal extraction failed: {e}")
        return False
    
    # Test 4: Reactive question generation
    print("\n4. Testing reactive question generation...")
    try:
        session_state = {
            "last_user_message": "I love programming",
            "last_question": "What do you enjoy?",
            "messages": [],
            "student_profile": {},
            "questions_text": []
        }
        
        question = await get_reactive_question(session_state)
        print(f"✅ Reactive question: {question[:100]}...")
    except Exception as e:
        print(f"❌ Reactive question failed: {e}")
        print(f"   This might be the issue!")
        return False
    
    return True

async def test_conversation_controller():
    """Test the conversation controller"""
    print("\n🧪 Testing Conversation Controller")
    print("=" * 40)
    
    controller = ConversationController()
    
    # Test session creation
    print("1. Creating test session...")
    try:
        session_id = "test-session-123"
        q_id, q_text = await controller.start_conversation(
            session_id=session_id,
            rank=5000,
            budget_lakh=3.0
        )
        print(f"✅ Session created: {q_text[:50]}...")
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return False
    
    # Test message processing
    print("\n2. Processing test message...")
    try:
        result = await controller.process_message(
            session_id=session_id,
            user_message="yes, I'm ready to start"
        )
        print(f"✅ Message processed successfully")
        print(f"   Question: {result.get('question_text', '')[:50]}...")
        print(f"   Used reactive: {result.get('used_reactive', 'Unknown')}")
        print(f"   Stage: {result.get('stage')}")
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   This is likely the root cause!")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    print("🔍 Pathfinder Backend Diagnosis")
    print("=" * 50)
    
    # Test LLM components
    llm_ok = await test_llm_direct()
    
    if not llm_ok:
        print("\n❌ LLM components failed - this is the issue!")
        return
    
    # Test conversation controller
    controller_ok = await test_conversation_controller()
    
    if controller_ok:
        print("\n🎉 All backend components working!")
        print("✅ The issue might be in frontend-backend communication")
        print("💡 Try checking browser network tab for detailed error")
    else:
        print("\n❌ Conversation controller failed - this is the issue!")
        print("🔧 The error above shows the exact problem")

if __name__ == "__main__":
    asyncio.run(main())