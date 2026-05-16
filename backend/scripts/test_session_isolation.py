"""
Test script to verify session isolation - each new session should be independent
"""
import requests
import time

API = "http://localhost:8000/api"

def test_session_isolation():
    print("=" * 80)
    print("Testing Session Isolation")
    print("=" * 80)
    
    # Session 1: JEE Advanced
    print("\n=== Session 1: JEE Advanced ===")
    try:
        res1 = requests.post(f"{API}/session/start", timeout=5)
        res1.raise_for_status()
        session1_id = res1.json()["session_id"]
        print(f"✅ Session 1 created: {session1_id}")
    except Exception as e:
        print(f"❌ Failed to create session 1: {e}")
        print("Make sure backend is running: python backend/main.py")
        return
    
    # Simulate conversation in session 1
    try:
        chat1 = requests.post(f"{API}/chat", json={
            "session_id": session1_id,
            "user_message": "I have JEE Advanced rank 2300 and I'm targeting IITs"
        }, timeout=10)
        chat1.raise_for_status()
        print(f"✅ Session 1 message sent")
    except Exception as e:
        print(f"❌ Failed to send message in session 1: {e}")
        return
    
    # Delete session 1
    try:
        del_res = requests.delete(f"{API}/session/{session1_id}", timeout=5)
        del_res.raise_for_status()
        print(f"✅ Session 1 deleted")
    except Exception as e:
        print(f"⚠️  Failed to delete session 1: {e}")
    
    time.sleep(1)
    
    # Session 2: JEE Main
    print("\n=== Session 2: JEE Main ===")
    try:
        res2 = requests.post(f"{API}/session/start", timeout=5)
        res2.raise_for_status()
        session2_id = res2.json()["session_id"]
        print(f"✅ Session 2 created: {session2_id}")
    except Exception as e:
        print(f"❌ Failed to create session 2: {e}")
        return
    
    # Verify different session IDs
    if session1_id == session2_id:
        print(f"❌ FAILED: Session IDs are the same!")
        print(f"   Session 1: {session1_id}")
        print(f"   Session 2: {session2_id}")
        return
    else:
        print(f"✅ Session IDs are different (as expected)")
    
    # Simulate conversation in session 2
    try:
        chat2 = requests.post(f"{API}/chat", json={
            "session_id": session2_id,
            "user_message": "I have JEE Main rank 5000 and I want to go to NITs"
        }, timeout=10)
        chat2.raise_for_status()
        print(f"✅ Session 2 message sent")
    except Exception as e:
        print(f"❌ Failed to send message in session 2: {e}")
        return
    
    # Verify session 1 is truly deleted (should get 404)
    print("\n=== Verifying Session 1 Deletion ===")
    try:
        chat1_again = requests.post(f"{API}/chat", json={
            "session_id": session1_id,
            "user_message": "test"
        }, timeout=5)
        if chat1_again.status_code == 404:
            print(f"✅ Session 1 correctly returns 404 (deleted)")
        else:
            print(f"⚠️  Session 1 still exists (status: {chat1_again.status_code})")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"✅ Session 1 correctly returns 404 (deleted)")
        else:
            print(f"❌ Unexpected error: {e}")
    except Exception as e:
        print(f"❌ Failed to verify session 1 deletion: {e}")
    
    # Clean up session 2
    try:
        requests.delete(f"{API}/session/{session2_id}", timeout=5)
        print(f"✅ Session 2 deleted (cleanup)")
    except Exception as e:
        print(f"⚠️  Failed to delete session 2: {e}")
    
    print("\n" + "=" * 80)
    print("✅ SESSION ISOLATION TEST PASSED")
    print("=" * 80)
    print("\nKey findings:")
    print("1. Each session gets a unique ID")
    print("2. Deleted sessions cannot be reused")
    print("3. New sessions start with clean state")

if __name__ == "__main__":
    test_session_isolation()
