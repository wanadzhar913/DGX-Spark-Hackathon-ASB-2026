#!/usr/bin/env python3
"""
Download and trim real surveillance & industrial CCTV footage for EdgeVision SOC.
"""

import os
import subprocess
import urllib.request

VIDEOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

SOURCES = [
    {
        "id": "cam2_server_intruder",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/face-demographics-walking.mp4",
        "dest": os.path.join(VIDEOS_DIR, "cam2_server_intruder.mp4"),
        "duration": 12
    },
    {
        "id": "cam3_warehouse_spill",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/bottle-detection.mp4",
        "dest": os.path.join(VIDEOS_DIR, "cam3_warehouse_spill.mp4"),
        "duration": 12
    },
    {
        "id": "cam4_exit_blocked",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/classroom.mp4",
        "dest": os.path.join(VIDEOS_DIR, "cam4_exit_blocked.mp4"),
        "duration": 12
    },
    {
        "id": "cam5_entrance_clear",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/people-detection.mp4",
        "dest": os.path.join(VIDEOS_DIR, "cam5_entrance_clear.mp4"),
        "duration": 12
    },
    {
        "id": "cam6_loading_dock",
        "url": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4",
        "dest": os.path.join(VIDEOS_DIR, "cam6_loading_dock.mp4"),
        "duration": 12
    }
]

def download_and_trim():
    for item in SOURCES:
        temp_path = item["dest"] + ".temp.mp4"
        print(f"⬇️ Downloading real footage for [{item['id']}]...")
        try:
            req = urllib.request.Request(item["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(temp_path, "wb") as f:
                f.write(resp.read())
            
            # Trim and optimize to 10s H.264
            print(f"✂️ Trimming [{item['id']}] to {item['duration']}s H.264...")
            cmd = [
                "ffmpeg", "-y",
                "-i", temp_path,
                "-t", str(item["duration"]),
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-an",
                "-movflags", "+faststart",
                item["dest"]
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"✅ Ready: {item['dest']} ({os.path.getsize(item['dest']) // 1024} KB)")
        except Exception as e:
            print(f"⚠️ Failed for {item['id']}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    download_and_trim()
