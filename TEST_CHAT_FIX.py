#!/usr/bin/env python3
"""
Test the chat fix to make sure it works properly
"""
import requests
import json
import time

def test_chat_fix():
    print("🧪 Testing Chat Fix")
    print("=" * 40)
    
    # Step 1: Create session
    print("1. Creating session...")
    session_response = requests.post("http://127.0.0.1:8000/session/start", 
                                   json={"jee_rank": 5000}, timeout=10)
    
    if session_response.status_code != 200:
        print(f"❌ Session creation failed: {session_response.status_code}")
        return False
    
    session_data = session_response.json()
    session_id = session_data["session_id"]
    print(f"✅ Session created: {session_id[:20]}...")
    
    # Step 2: Send chat message
    print("\n2. Sending chat message...")
    print("⏳ This may take 10-30 seconds for Ollama...")
    
    start_time = time.time()
    
    try:
        chat_response = requests.post("http://127.0.0.1:8000/chat",
                                    json={
                                        "session_id": session_id,
                                        "user_message": "yes, I'm ready to start"
                                    },
                                    timeout=90)  # 90 second timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat successful! ({duration:.1f}s)")
            print(f"   Response: {chat_data.get('assistant_message', '')[:100]}...")
            print(f"   Next question: {chat_data.get('next_question', '')[:100]}...")
            print(f"   Branch scores: {chat_data.get('branch_scores', {})}")
            print(f"   Used reactive: {chat_data.get('used_reactive', 'Unknown')}")
            return True
        else:
            print(f"❌ Chat failed: {chat_response.status_code}")
            print(f"   Response: {chat_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Chat timed out after 90 seconds")
        print("   This suggests Ollama is not responding properly")
        return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def main():
    success = test_chat_fix()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Chat fix successful!")
        print("✅ Frontend should now work properly")
        print("✅ Try refreshing the browser and testing again")
    else:
        print("❌ Chat fix failed")
        print("🔧 Check if Ollama is running properly")
        print("   Run: ollama list")
        print("   Should show: llama3.2:3b")

if __name__ == "__main__":
    main()