"""Quick test to check if backend starts correctly"""
import sys
sys.path.insert(0, 'backend')

try:
    from main import app
    print("✅ Backend imports successfully")
    print("✅ FastAPI app created")
    print("\nTo start the backend server, run:")
    print("  cd backend")
    print("  uvicorn main:app --reload --host 127.0.0.1 --port 8080")
except Exception as e:
    print(f"❌ Error importing backend: {e}")
    import traceback
    traceback.print_exc()
