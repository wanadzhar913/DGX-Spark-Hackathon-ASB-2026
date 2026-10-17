#!/usr/bin/env python3
"""
Test vLLM omni endpoint with high token limit and reasoning extraction.
"""

import os
import json
import base64
import urllib.request
import urllib.error

FRAME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "test_frame.jpg")

with open(FRAME_PATH, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "model": "omni",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": "Analyze this CCTV security frame for safety violations or intruders. Be concise. Output ONLY a JSON object with keys: hazard_detected (boolean), incident_type (string), severity (CRITICAL/WARNING/SAFE), summary (short sentence), action (short sentence)."
                },
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        }
    ],
    "max_tokens": 800
}

url = "http://localhost:9001/v1/chat/completions"

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        msg = result["choices"][0]["message"]
        content = msg.get("content")
        reasoning = msg.get("reasoning")
        print("\n--- CONTENT ---")
        print(content)
        print("\n--- REASONING (snippet) ---")
        if reasoning:
            print(reasoning[:200] + "...")
except Exception as e:
    print("Error:", e)
