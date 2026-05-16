#!/usr/bin/env python3
"""
Test the complete chat flow to identify where it's failing.
"""
import requests
import json
import time

def test_complete_flow():
    """Test the complete chat flow step by step."""
    print("🧪 Testing Complete Chat Flow")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Step 1: Check backend health
    print("1. Checking backend health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False
    
    # Step 2: Create session
    print("\n2. Creating session...")
    try:
        session_data = {
            "jee_rank": 5000,
            "budget_lakh": 3.0,
            "preferred_location": "Bangalore"
        }
        
        response = requests.post(f"{base_url}/session/start", json=session_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            session_id = data["session_id"]
            print(f"✅ Session created: {session_id}")
            print(f"   Message: {data.get('message', '')[:100]}...")
            print(f"   First question: {data.get('first_question', '')[:100]}...")
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return False
    
    # Step 3: Send first chat message
    print("\n3. Sending first chat message...")
    try:
        chat_data = {
            "session_id": session_id,
            "user_message": "I love programming and building software applications. I enjoy solving complex problems and creating innovative solutions."
        }
        
        response = requests.post(f"{base_url}/chat", json=chat_data, timeout=60)  # Increased timeout for Ollama
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat message processed successfully")
            print(f"   Question ID: {data.get('question_id')}")
            print(f"   Question: {data.get('question_text', '')[:150]}...")
            print(f"   Stage: {data.get('stage')}")
            print(f"   Branch scores: {data.get('branch_scores', {})}")
            print(f"   Used reactive: {data.get('used_reactive', 'Not specified')}")
            print(f"   Is complete: {data.get('is_complete', False)}")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
            # If it's a 500 error, it might be LLM related
            if response.status_code == 500:
                print("\n🔍 This looks like an LLM error. Let's check LLM status...")
                try:
                    llm_response = requests.get(f"{base_url}/api/llm-status", timeout=10)
                    if llm_response.status_code == 200:
                        llm_data = llm_response.json()
                        print(f"   LLM Status: {json.dumps(llm_data, indent=2)}")
                        
                        if not llm_data.get("active_provider"):
                            print("\n💡 Solution: No LLM provider available!")
                            print("   Option 1: Install Ollama and run 'ollama pull mistral'")
                            print("   Option 2: Set GROQ_API_KEY environment variable")
                            print("   Option 3: Run SETUP_AND_START.bat to install everything")
                    else:
                        print(f"   LLM status check failed: {llm_response.status_code}")
                except Exception as e:
                    print(f"   LLM status error: {e}")
            
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def main():
    """Run the test."""
    success = test_complete_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Chat flow test PASSED!")
        print("✅ The backend is working correctly")
        print("✅ Session creation works")
        print("✅ Chat processing works")
        print("\n💡 If frontend is not navigating to chat:")
        print("   1. Check browser console for errors")
        print("   2. Use the Debug Panel (🐛 button)")
        print("   3. Make sure frontend is running on http://localhost:5173")
    else:
        print("❌ Chat flow test FAILED!")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Make sure backend is running: python backend/main.py")
        print("   2. Install Ollama: Run SETUP_AND_START.bat")
        print("   3. Or set GROQ_API_KEY environment variable")
        print("   4. Check backend logs for detailed errors")

if __name__ == "__main__":
    main()