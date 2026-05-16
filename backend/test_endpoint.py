#!/usr/bin/env python3
"""
Simple test to verify the new LLM status endpoint works.
"""
from fastapi.testclient import TestClient
from main import app

def test_llm_status_endpoint():
    """Test the new /api/llm-status endpoint."""
    client = TestClient(app)
    
    print("Testing /api/llm-status endpoint...")
    response = client.get("/api/llm-status")
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    expected_keys = ["groq", "ollama", "ollama_model", "active_provider", "active_model"]
    for key in expected_keys:
        assert key in data, f"Missing key: {key}"
    
    print("✅ LLM status endpoint working correctly!")
    return True

def test_health_endpoint():
    """Test the health endpoint still works."""
    client = TestClient(app)
    
    print("Testing /health endpoint...")
    response = client.get("/health")
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    
    print("✅ Health endpoint working correctly!")
    return True

if __name__ == "__main__":
    print("🧪 Testing API Endpoints")
    print("=" * 40)
    
    try:
        test_health_endpoint()
        test_llm_status_endpoint()
        
        print("\n🎉 All endpoint tests passed!")
        print("✅ /health endpoint: Working")
        print("✅ /api/llm-status endpoint: Working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()