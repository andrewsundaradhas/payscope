#!/usr/bin/env python3
"""
Check external dependencies before starting services.
Verifies: Pinecone, Neo4j, MinIO/S3, Docker port conflicts
"""

import os
import sys
import socket
from pathlib import Path
from typing import Optional

def check_port(host: str, port: int) -> bool:
    """Check if a port is available (not in use)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0  # Port is available if connection fails
    except Exception:
        return False

def check_pinecone() -> tuple[bool, str]:
    """Check Pinecone index exists and is accessible."""
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME") or os.getenv("PINECONE_INDEX")
    
    if not api_key:
        return False, "PINECONE_API_KEY not set"
    
    if not index_name:
        return False, "PINECONE_INDEX_NAME or PINECONE_INDEX not set"
    
    try:
        try:
            from pinecone import Pinecone
        except ImportError:
            # Fallback to old package name
            from pinecone_client import Pinecone
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        index_names = [idx.name for idx in indexes]
        
        if index_name in index_names:
            # Get index info
            index = pc.Index(index_name)
            stats = index.describe_index_stats()
            return True, f"Index '{index_name}' exists (dimensions: {stats.get('dimension', 'unknown')})"
        else:
            return False, f"Index '{index_name}' not found. Available indexes: {', '.join(index_names) if index_names else 'none'}"
    
    except ImportError:
        return False, "pinecone-client not installed (pip install pinecone-client)"
    except Exception as e:
        return False, f"Error connecting to Pinecone: {str(e)}"

def check_neo4j() -> tuple[bool, str]:
    """Check Neo4j is reachable."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        return False, "NEO4J_PASSWORD not set"
    
    try:
        from neo4j import GraphDatabase
        
        # Parse URI
        if not uri.startswith("bolt://") and not uri.startswith("neo4j://"):
            return False, f"Invalid NEO4J_URI format: {uri} (must start with bolt:// or neo4j://)"
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        
        driver.close()
        return True, f"Connected to Neo4j at {uri}"
    
    except ImportError:
        return False, "neo4j driver not installed (pip install neo4j)"
    except Exception as e:
        return False, f"Error connecting to Neo4j: {str(e)}"

def check_minio_s3() -> tuple[bool, str]:
    """Check MinIO/S3 bucket exists and SSE is enabled."""
    endpoint = os.getenv("S3_ENDPOINT_URL") or os.getenv("S3_ENDPOINT")
    access_key = os.getenv("S3_ACCESS_KEY_ID") or os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_ACCESS_KEY") or os.getenv("S3_SECRET_KEY")
    bucket = os.getenv("S3_BUCKET")
    
    if not endpoint:
        return False, "S3_ENDPOINT_URL or S3_ENDPOINT not set"
    
    if not access_key:
        return False, "S3_ACCESS_KEY_ID or S3_ACCESS_KEY not set"
    
    if not secret_key:
        return False, "S3_SECRET_ACCESS_KEY or S3_SECRET_KEY not set"
    
    if not bucket:
        return False, "S3_BUCKET not set"
    
    try:
        import boto3
        from botocore.exceptions import ClientError, EndpointConnectionError
        
        # Parse endpoint (remove http:// or https:// for boto3)
        endpoint_url = endpoint if endpoint.startswith("http") else f"http://{endpoint}"
        
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                return False, f"Bucket '{bucket}' does not exist. Create it first."
            else:
                return False, f"Error accessing bucket '{bucket}': {error_code}"
        
        # Check bucket encryption (SSE)
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket)
            rules = encryption.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            if rules:
                sse_type = rules[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm', 'unknown')
                return True, f"Bucket '{bucket}' exists with SSE: {sse_type}"
            else:
                return False, f"Bucket '{bucket}' exists but SSE is not configured"
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                return False, f"Bucket '{bucket}' exists but SSE is not enabled. Enable SSE on the bucket."
            else:
                # Some S3-compatible services don't support encryption API
                return True, f"Bucket '{bucket}' exists (SSE check not supported by this endpoint)"
        
    except ImportError:
        return False, "boto3 not installed (pip install boto3)"
    except EndpointConnectionError as e:
        return False, f"Cannot connect to S3 endpoint '{endpoint}': {str(e)}"
    except Exception as e:
        return False, f"Error checking S3: {str(e)}"

def check_docker_ports() -> tuple[bool, str]:
    """Check if Docker service ports are available."""
    ports_to_check = [
        (5432, "PostgreSQL/TimescaleDB"),
        (6379, "Redis"),
        (7687, "Neo4j"),
        (7474, "Neo4j Browser"),
        (9000, "MinIO API"),
        (9001, "MinIO Console"),
        (8000, "API service"),
        (8080, "Ingestion service"),
    ]
    
    conflicts = []
    for port, service in ports_to_check:
        if not check_port("localhost", port):
            conflicts.append(f"{service} (port {port})")
    
    if conflicts:
        return False, f"Port conflicts detected: {', '.join(conflicts)}"
    else:
        return True, "All required ports are available"

def load_env_file(env_file: Path) -> None:
    """Load environment variables from .env file."""
    if not env_file.exists():
        return
    
    try:
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
    except Exception as e:
        print(f"[WARNING] Error loading .env file: {e}", file=sys.stderr)

def main():
    """Run all dependency checks."""
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_env_file(env_file)
        print("Loaded environment variables from .env file")
        print()
    
    checks = [
        ("Pinecone Index", check_pinecone),
        ("Neo4j Connection", check_neo4j),
        ("MinIO/S3 Bucket", check_minio_s3),
        ("Docker Ports", check_docker_ports),
    ]
    
    print("=" * 60)
    print("External Dependencies Check")
    print("=" * 60)
    print()
    
    all_passed = True
    results = []
    
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ", flush=True)
        try:
            passed, message = check_func()
            if passed:
                print(f"[OK] {message}")
                results.append((name, True, message))
            else:
                print(f"[FAIL] {message}")
                results.append((name, False, message))
                all_passed = False
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            results.append((name, False, f"Exception: {str(e)}"))
            all_passed = False
        print()
    
    print("=" * 60)
    if all_passed:
        print("[OK] All dependencies are ready!")
        print()
        print("You can now start services with: docker compose up -d")
        return 0
    else:
        print("[FAIL] Some dependencies are not ready")
        print()
        print("Summary of issues:")
        for name, passed, message in results:
            if not passed:
                print(f"  - {name}: {message}")
        print()
        print("Please fix the issues above before starting services.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

