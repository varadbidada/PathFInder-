#!/usr/bin/env python3
"""
Test chat without reactive AI to isolate the issue
"""
import requests
import json

def test_simple_chat():
    print("🧪 Testing Simple Chat (No Reactive AI)")
    print("=" * 50)
    
    # Step 1: Create session
    print("1. Creating session...")
    try:
        session_response = requests.post(
            "http://127.0.0.1:8080/session/start",
            json={"jee_rank": 5000, "budget_lakh": 3.0},
            timeout=10
        )
        
        if session_response.status_code != 200:
            print(f"❌ Session creation failed: {session_response.status_code}")
            print(f"   Response: {session_response.text}")
            return False
        
        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id[:20]}...")
        
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Step 2: Test health endpoint
    print("\n2. Testing health endpoint...")
    try:
        health_response = requests.get("http://127.0.0.1:8080/health", timeout=5)
        print(f"✅ Health check: {health_response.status_code}")
        print(f"   Response: {health_response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Step 3: Test LLM status
    print("\n3. Testing LLM status...")
    try:
        llm_response = requests.get("http://127.0.0.1:8080/api/llm-status", timeout=5)
        print(f"✅ LLM status: {llm_response.status_code}")
        print(f"   Response: {llm_response.json()}")
    except Exception as e:
        print(f"❌ LLM status failed: {e}")
    
    # Step 4: Send a simple chat message with short timeout
    print("\n4. Sending chat message (10s timeout)...")
    try:
        chat_response = requests.post(
            "http://127.0.0.1:8080/chat",
            json={
                "session_id": session_id,
                "user_message": "yes"
            },
            timeout=10  # Short timeout
        )
        
        print(f"   Response status: {chat_response.status_code}")
        
        if chat_response.status_code == 200:
            print("✅ Chat successful!")
            chat_data = chat_response.json()
            print(f"   Assistant message: {chat_data.get('assistant_message', '')[:100]}...")
            return True
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(f"   Response: {chat_response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ Chat timed out after 10 seconds")
        print("   This suggests the backend is hanging on LLM calls")
        return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

if __name__ == "__main__":
    test_simple_chat()