#!/usr/bin/env python3
"""
Simplified development server
"""
import os
os.environ["ENVIRONMENT"] = "development"

import uvicorn

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 California Motion Writer - Development Server")
    print("="*50)
    print("📍 Local URL: http://localhost:8080")
    print("📚 API Docs: http://localhost:8080/docs")
    print("🏠 Homepage: http://localhost:8080")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)