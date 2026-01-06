#!/usr/bin/env python3
"""
Add JWT keys to .env file.
Handles multiline PEM keys properly.
"""

import sys
from pathlib import Path

def main():
    env_file = Path(".env")
    private_key_file = Path("jwt_private.pem")
    public_key_file = Path("jwt_public.pem")
    example_file = Path("env/local.env.example")
    
    # Check if key files exist
    if not private_key_file.exists():
        print(f"[FAIL] Private key file not found: {private_key_file}", file=sys.stderr)
        sys.exit(1)
    
    if not public_key_file.exists():
        print(f"[FAIL] Public key file not found: {public_key_file}", file=sys.stderr)
        sys.exit(1)
    
    # Read key files
    private_key_content = private_key_file.read_text().strip()
    public_key_content = public_key_file.read_text().strip()
    
    # Create .env file if it doesn't exist
    if not env_file.exists():
        print("Creating .env file from example...")
        if example_file.exists():
            env_file.write_text(example_file.read_text())
            print(f"[OK] Created .env from {example_file}")
        else:
            print("[WARNING] Example file not found, creating empty .env")
            env_file.write_text("")
        print()
    
    # Read existing .env content
    env_content = env_file.read_text() if env_file.exists() else ""
    lines = env_content.splitlines() if env_content else []
    
    # Remove existing JWT key entries
    new_lines = []
    for line in lines:
        if line.strip().startswith("JWT_PRIVATE_KEY=") or line.strip().startswith("JWT_PUBLIC_KEY="):
            continue
        new_lines.append(line)
    
    # Find insertion point (after last non-empty, non-comment line)
    insert_index = len(new_lines)
    for i in range(len(new_lines) - 1, -1, -1):
        trimmed = new_lines[i].strip()
        if trimmed and not trimmed.startswith("#"):
            insert_index = i + 1
            break
    
    # Build final content
    final_lines = new_lines[:insert_index]
    
    # Add empty line before JWT section if needed
    if final_lines and final_lines[-1].strip():
        final_lines.append("")
    
    # Add JWT keys section
    # For .env files, store PEM keys with escaped newlines
    # Format: KEY="line1\nline2\nline3"
    # python-dotenv supports this format
    private_key_escaped = private_key_content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    public_key_escaped = public_key_content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    
    final_lines.append("# JWT Keys (PEM format with escaped newlines)")
    final_lines.append(f'JWT_PRIVATE_KEY="{private_key_escaped}"')
    final_lines.append(f'JWT_PUBLIC_KEY="{public_key_escaped}"')
    
    # Add remaining lines
    final_lines.extend(new_lines[insert_index:])
    
    # Write back to file
    env_file.write_text("\n".join(final_lines) + "\n")
    
    print(f"[OK] Added JWT keys to {env_file.absolute()}")
    print()
    print("Keys are stored with escaped newlines (\\n) for .env compatibility.")
    print("This format works with python-dotenv (used by pydantic-settings).")
    print()
    
    # Verify keys were added
    verify_content = env_file.read_text()
    if "JWT_PRIVATE_KEY=" in verify_content and "JWT_PUBLIC_KEY=" in verify_content:
        print("[OK] Verification: JWT keys found in .env file")
    else:
        print("[WARNING] Could not verify keys were added correctly", file=sys.stderr)

if __name__ == "__main__":
    main()

