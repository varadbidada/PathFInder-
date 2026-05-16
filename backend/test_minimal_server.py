#!/usr/bin/env python3
"""
Minimal FastAPI server to test if the issue is in our main.py
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Minimal server working"}

@app.post("/test")
async def test_endpoint(data: dict):
    return {"received": data, "status": "success"}

if __name__ == "__main__":
    print("Starting minimal server on port 8080...")
    uvicorn.run(app, host="127.0.0.1", port=8080)