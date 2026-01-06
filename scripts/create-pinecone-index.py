#!/usr/bin/env python3
"""
Create Pinecone index for PayScope.
Run this after setting PINECONE_API_KEY and PINECONE_INDEX_NAME in .env
"""

import os
import sys
from pathlib import Path

def load_env_file(env_file: Path) -> None:
    """Load environment variables from .env file."""
    if not env_file.exists():
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                # Handle escaped newlines
                value = value.replace('\\n', '\n')
                if key and key not in os.environ:
                    os.environ[key] = value

def main():
    """Create Pinecone index."""
    # Load .env file
    env_file = Path(".env")
    if env_file.exists():
        load_env_file(env_file)
    
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX")
    namespace = os.getenv("PINECONE_NAMESPACE", "payscope")
    
    if not api_key:
        print("[FAIL] PINECONE_API_KEY not set in .env file", file=sys.stderr)
        print("Add it to .env: PINECONE_API_KEY=your-api-key", file=sys.stderr)
        sys.exit(1)
    
    if not index_name:
        print("[FAIL] PINECONE_INDEX_NAME not set in .env file", file=sys.stderr)
        print("Add it to .env: PINECONE_INDEX_NAME=your-index-name", file=sys.stderr)
        sys.exit(1)
    
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError:
        print("[FAIL] pinecone-client not installed", file=sys.stderr)
        print("Install it: pip install pinecone-client", file=sys.stderr)
        sys.exit(1)
    
    print(f"Connecting to Pinecone...")
    print(f"Index name: {index_name}")
    print(f"Namespace: {namespace}")
    print()
    
    try:
        pc = Pinecone(api_key=api_key)
        
        # Check if index already exists
        indexes = pc.list_indexes()
        existing_names = [idx.name for idx in indexes]
        
        if index_name in existing_names:
            print(f"[OK] Index '{index_name}' already exists")
            
            # Get index info
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            print(f"  Dimensions: {stats.get('dimension', 'unknown')}")
            print(f"  Vector count: {stats.get('total_vector_count', 'unknown')}")
            return 0
        
        # Create index
        print(f"Creating index '{index_name}'...")
        
        # Default dimension for BAAI/bge-base-en-v1.5 is 768
        dimension = 768
        
        # For Serverless (free tier)
        # Note: Adjust cloud and region based on your Pinecone plan
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        
        print(f"[OK] Index '{index_name}' created successfully")
        print(f"  Dimensions: {dimension}")
        print(f"  Metric: cosine")
        print(f"  Spec: Serverless (AWS us-east-1)")
        return 0
        
    except Exception as e:
        print(f"[FAIL] Error: {str(e)}", file=sys.stderr)
        print()
        print("Common issues:")
        print("  - Invalid API key (get one from https://www.pinecone.io/)")
        print("  - Index name already exists with different settings")
        print("  - Insufficient quota (free tier has limits)")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())



