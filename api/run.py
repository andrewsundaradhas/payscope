"""
Run the PayScope API server.

Usage:
    python run.py
"""

import os
import sys

# Add src directory to Python path BEFORE importing anything else
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_path)

# Set PYTHONPATH for any subprocesses
os.environ["PYTHONPATH"] = src_path + os.pathsep + os.environ.get("PYTHONPATH", "")

import uvicorn

if __name__ == "__main__":
    # Run without reload to avoid subprocess path issues
    # For development, you can use: PYTHONPATH=src uvicorn payscope_api.app:app --reload
    uvicorn.run(
        "payscope_api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid subprocess path issues
    )
