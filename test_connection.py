#!/usr/bin/env python3
"""
Test connection to remote/local NVIDIA Vision LLM server (Ollama or vLLM).
Usage:
  python3 test_connection.py
  python3 test_connection.py http://192.168.1.100:11434
"""

import sys
import json
import urllib.request
import urllib.error

def test_nvidia_server(base_url="http://localhost:11434"):
    base_url = base_url.rstrip("/")
    print(f"\n🔍 Testing connection to NVIDIA LLM at: {base_url}")
    
    # Check 1: Ollama tags
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", headers={"User-Agent": "EdgeVision-Test"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                models = [m.get("name") for m in data.get("models", [])]
                print(f"✅ SUCCESS: Connected to Ollama on NVIDIA machine!")
                print(f"📦 Installed models: {', '.join(models) if models else 'None found'}")
                return True
    except Exception as e:
        pass

    # Check 2: vLLM models
    try:
        req = urllib.request.Request(f"{base_url}/v1/models", headers={"User-Agent": "EdgeVision-Test"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                models = [m.get("id") for m in data.get("data", [])]
                print(f"✅ SUCCESS: Connected to vLLM server on NVIDIA machine!")
                print(f"📦 Active models: {', '.join(models) if models else 'None'}")
                return True
    except Exception as e:
        pass

    # Failure diagnostics
    print(f"\n❌ FAILED: Could not reach {base_url}.")
    print("\n🛠️ HOW TO FIX THIS FOR YOUR HACKATHON:")
    print("1. If Ollama/vLLM is running on another machine:")
    print("   Open a new terminal tab on your laptop and run this SSH port forward:")
    print(f"   👉  ssh -L 11434:localhost:11434 <username>@<NVIDIA_MACHINE_IP>")
    print("   (This safely tunnels port 11434 directly to your laptop over SSH!)\n")
    print("2. If running directly without SSH:")
    print("   On the NVIDIA machine, ensure Ollama is listening on all network interfaces:")
    print("   👉  OLLAMA_HOST=0.0.0.0:11434 ollama serve")
    print("   And open the firewall on the NVIDIA machine:")
    print("   👉  sudo ufw allow 11434\n")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_nvidia_server(sys.argv[1])
    else:
        # Auto-try common ports (vLLM 8000 first, then Ollama 11434)
        print("Checking vLLM (port 8000) and Ollama (port 11434)...")
        if not test_nvidia_server("http://localhost:8000"):
            test_nvidia_server("http://localhost:11434")
