#!/usr/bin/env python3
"""
Direct test of the chat processing without FastAPI
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from engines.conversation_controller import conversation_controller

async def test_chat_direct():
    print("🧪 Testing Chat Processing Directly")
    print("=" * 50)
    
    # Step 1: Start conversation
    print("1. Starting conversation...")
    try:
        session_id = "test-session-123"
        question_id, question_text = await conversation_controller.start_conversation(
            session_id=session_id,
            rank=5000,
            budget_lakh=3.0
        )
        
        print(f"✅ Conversation started")
        print(f"   Question ID: {question_id}")
        print(f"   Question: {question_text[:100]}...")
        
    except Exception as e:
        print(f"❌ Start conversation failed: {e}")
        return False
    
    # Step 2: Process message
    print("\n2. Processing user message...")
    try:
        result = await conversation_controller.process_message(
            session_id=session_id,
            user_message="yes, I'm ready to start"
        )
        
        print("✅ Message processed successfully!")
        print(f"   Question ID: {result.get('question_id')}")
        print(f"   Question text: {result.get('question_text', '')[:100]}...")
        print(f"   Stage: {result.get('stage')}")
        print(f"   Branch scores: {result.get('branch_scores', {})}")
        print(f"   Complete: {result.get('is_complete', False)}")
        print(f"   Used reactive: {result.get('used_reactive', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_chat_direct()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 CHAT PROCESSING IS WORKING!")
        print("✅ The backend conversation controller is functional")
        print("✅ The issue might be in FastAPI routing or frontend")
    else:
        print("❌ Chat processing has issues")
        print("   Check the error above for details")

if __name__ == "__main__":
    asyncio.run(main())