#!/usr/bin/env python3
"""
Test script to verify frontend-backend connection and model functionality.
"""
import requests
import json
import time
import subprocess
import sys
import os
from pathlib import Path

def test_backend_health():
    """Test if backend is running and healthy."""
    print("🔍 Testing Backend Health...")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend healthy: {data['status']}")
            print(f"   Active sessions: {data.get('active_sessions', 0)}")
            return True
        else:
            print(f"❌ Backend unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_llm_status():
    """Test the new LLM status endpoint."""
    print("\n🤖 Testing LLM Status Endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/llm-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ LLM Status endpoint working")
            print(f"   Groq available: {data.get('groq', False)}")
            print(f"   Ollama available: {data.get('ollama', False)}")
            print(f"   Active provider: {data.get('active_provider', 'None')}")
            print(f"   Active model: {data.get('active_model', 'None')}")
            return True
        else:
            print(f"❌ LLM status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLM status error: {e}")
        return False

def test_model_performance():
    """Test model files and performance."""
    print("\n📊 Testing Model Performance...")
    
    model_files = [
        "backend/data/cutoff_model_ridge.pkl",
        "backend/data/cutoff_model_xgb.pkl", 
        "backend/data/model_performance.json"
    ]
    
    all_exist = True
    for file_path in model_files:
        if os.path.exists(file_path):
            print(f"✅ Model file exists: {file_path}")
        else:
            print(f"❌ Missing model file: {file_path}")
            all_exist = False
    
    # Check model performance
    try:
        with open("backend/data/model_performance.json", "r") as f:
            perf = json.load(f)
        
        print(f"✅ Model Performance Data:")
        print(f"   Winner: {perf.get('winner', 'unknown')}")
        print(f"   XGBoost MAPE: {perf.get('xgboost', {}).get('mape', 0):.2f}%")
        print(f"   XGBoost within 1000 ranks: {perf.get('xgboost', {}).get('within_1000', 0):.1f}%")
        print(f"   Training combinations: {perf.get('train_combos', 0)}")
        
        return all_exist
    except Exception as e:
        print(f"❌ Failed to read model performance: {e}")
        return False

def test_session_creation():
    """Test session creation endpoint."""
    print("\n🎯 Testing Session Creation...")
    try:
        payload = {
            "jee_rank": 5000,
            "budget_lakh": 3.0,
            "preferred_location": "Bangalore"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/session/start", 
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"✅ Session created: {session_id}")
            print(f"   First question: {data.get('first_question', '')[:100]}...")
            return session_id
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Session creation error: {e}")
        return None

def test_chat_message(session_id):
    """Test sending a chat message."""
    print("\n💬 Testing Chat Message...")
    try:
        payload = {
            "session_id": session_id,
            "user_message": "I love programming and building software applications"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat message processed")
            print(f"   Next question: {data.get('question_text', '')[:100]}...")
            print(f"   Branch scores: {data.get('branch_scores', {})}")
            print(f"   Used reactive: {data.get('used_reactive', 'Not specified')}")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def test_cutoff_prediction():
    """Test cutoff prediction endpoint."""
    print("\n🎯 Testing Cutoff Prediction...")
    try:
        params = {
            "college": "NIT Trichy",
            "branch": "Computer Science and Engineering",
            "category": "OPEN",
            "gender": "Gender-Neutral"
        }
        
        response = requests.get(
            "http://127.0.0.1:8000/cutoff-prediction",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Cutoff prediction working")
            print(f"   Predicted cutoff: {data.get('predicted_cutoff', 'N/A')}")
            print(f"   Model used: {data.get('model_used', 'N/A')}")
            return True
        else:
            print(f"❌ Cutoff prediction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cutoff prediction error: {e}")
        return False

def check_frontend_files():
    """Check if frontend files exist."""
    print("\n🎨 Checking Frontend Files...")
    
    frontend_files = [
        "frontend/package.json",
        "frontend/src/App.jsx",
        "frontend/src/components/LLMStatusIndicator.jsx",
        "frontend/src/utils/axiosConfig.js",
        "frontend/src/store/counsellorStore.js"
    ]
    
    all_exist = True
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✅ Frontend file exists: {file_path}")
        else:
            print(f"❌ Missing frontend file: {file_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("🧪 Testing Frontend-Backend Connection & Model Performance")
    print("=" * 70)
    
    # Test 1: Backend health
    backend_healthy = test_backend_health()
    
    # Test 2: LLM status
    llm_working = test_llm_status()
    
    # Test 3: Model performance
    models_ready = test_model_performance()
    
    # Test 4: Frontend files
    frontend_ready = check_frontend_files()
    
    if not backend_healthy:
        print("\n❌ Backend not running. Please start the backend first:")
        print("   cd backend && python main.py")
        return False
    
    # Test 5: Session creation
    session_id = test_session_creation()
    
    # Test 6: Chat functionality (if session created)
    chat_working = False
    if session_id:
        chat_working = test_chat_message(session_id)
    
    # Test 7: Cutoff prediction
    cutoff_working = test_cutoff_prediction()
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 Test Summary:")
    print(f"✅ Backend Health: {'✓' if backend_healthy else '✗'}")
    print(f"✅ LLM Status Endpoint: {'✓' if llm_working else '✗'}")
    print(f"✅ Model Files & Performance: {'✓' if models_ready else '✗'}")
    print(f"✅ Frontend Files: {'✓' if frontend_ready else '✗'}")
    print(f"✅ Session Creation: {'✓' if session_id else '✗'}")
    print(f"✅ Chat Functionality: {'✓' if chat_working else '✗'}")
    print(f"✅ Cutoff Prediction: {'✓' if cutoff_working else '✗'}")
    
    all_working = all([
        backend_healthy, llm_working, models_ready, 
        frontend_ready, session_id, chat_working, cutoff_working
    ])
    
    if all_working:
        print("\n🎉 All systems operational!")
        print("✅ Frontend-Backend connection: Working")
        print("✅ AI models: Trained and ready")
        print("✅ Dual-mode LLM: Configured")
        print("✅ Reactive counsellor: Active")
        print("\n🚀 Ready to start frontend!")
    else:
        print("\n⚠️  Some issues detected. Check the logs above.")
    
    return all_working

if __name__ == "__main__":
    main()