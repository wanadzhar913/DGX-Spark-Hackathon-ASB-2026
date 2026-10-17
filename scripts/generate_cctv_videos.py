#!/usr/bin/env python3
"""
Generate 6 realistic, high-impact CCTV scenario videos for EdgeVision SOC.
Uses standard Python byte stream piped directly into ffmpeg.
Zero external pip dependencies required.
"""

import os
import math
import random
import subprocess

WIDTH = 480
HEIGHT = 270
FPS = 25
DURATION_SEC = 6
TOTAL_FRAMES = FPS * DURATION_SEC
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "videos")

def clamp(val, min_val=0, max_val=255):
    return max(min_val, min(max_val, int(val)))

def set_pixel(buf, x, y, r, g, b, alpha=1.0):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        idx = (y * WIDTH + x) * 3
        if alpha >= 1.0:
            buf[idx] = r
            buf[idx+1] = g
            buf[idx+2] = b
        else:
            buf[idx] = clamp(buf[idx] * (1 - alpha) + r * alpha)
            buf[idx+1] = clamp(buf[idx+1] * (1 - alpha) + g * alpha)
            buf[idx+2] = clamp(buf[idx+2] * (1 - alpha) + b * alpha)

def fill_rect(buf, rx, ry, rw, rh, r, g, b, alpha=1.0):
    rx = int(rx)
    ry = int(ry)
    rw = int(rw)
    rh = int(rh)
    for y in range(max(0, ry), min(HEIGHT, ry + rh)):
        for x in range(max(0, rx), min(WIDTH, rx + rw)):
            set_pixel(buf, x, y, r, g, b, alpha)

def draw_circle(buf, cx, cy, radius, r, g, b, alpha=1.0):
    cx = int(cx)
    cy = int(cy)
    rad = int(radius)
    for y in range(max(0, cy - rad), min(HEIGHT, cy + rad + 1)):
        for x in range(max(0, cx - rad), min(WIDTH, cx + rad + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= rad ** 2:
                set_pixel(buf, x, y, r, g, b, alpha)

def draw_ellipse(buf, cx, cy, rx, ry, r, g, b, alpha=1.0):
    cx = int(cx)
    cy = int(cy)
    rx = max(1, int(rx))
    ry = max(1, int(ry))
    for y in range(max(0, cy - ry), min(HEIGHT, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(WIDTH, cx + rx + 1)):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                set_pixel(buf, x, y, r, g, b, alpha)

def draw_line(buf, x0, y0, x1, y1, r, g, b):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        set_pixel(buf, x0, y0, r, g, b)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def draw_hollow_rect(buf, rx, ry, rw, rh, r, g, b, thickness=2):
    rx, ry, rw, rh = int(rx), int(ry), int(rw), int(rh)
    fill_rect(buf, rx, ry, rw, thickness, r, g, b)
    fill_rect(buf, rx, ry + rh - thickness, rw, thickness, r, g, b)
    fill_rect(buf, rx, ry, thickness, rh, r, g, b)
    fill_rect(buf, rx + rw - thickness, ry, thickness, rh, r, g, b)

def apply_cctv_effects(buf, frame_idx):
    # Scan lines
    for y in range(0, HEIGHT, 2):
        row_start = y * WIDTH * 3
        for x in range(WIDTH):
            idx = row_start + x * 3
            buf[idx] = int(buf[idx] * 0.85)
            buf[idx+1] = int(buf[idx+1] * 0.85)
            buf[idx+2] = int(buf[idx+2] * 0.85)
    
    # Subtle digital sensor noise
    random.seed(frame_idx * 997)
    for _ in range(120):
        nx = random.randint(0, WIDTH - 1)
        ny = random.randint(0, HEIGHT - 1)
        v = random.randint(180, 240)
        set_pixel(buf, nx, ny, v, v, v, alpha=0.3)

def generate_video(cam_id, scenario, output_path):
    print(f"🎬 Rendering [{cam_id}] scenario: {scenario}...")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-movflags", "+faststart",
        output_path
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for f in range(TOTAL_FRAMES):
        t = f / FPS
        # Initialize frame buffer (dark surveillance tint)
        buf = bytearray([12, 18, 28] * (WIDTH * HEIGHT))

        # Common ground plane with perspective grid
        horizon = int(HEIGHT * 0.42)
        fill_rect(buf, 0, horizon, WIDTH, HEIGHT - horizon, 18, 24, 34)

        for gy in range(horizon, HEIGHT, 18):
            draw_line(buf, 0, gy, WIDTH, gy, 28, 38, 52)
        for gx in range(-WIDTH, WIDTH * 2, 40):
            draw_line(buf, gx, HEIGHT, int(WIDTH * 0.5 + (gx - WIDTH * 0.5) * 0.2), horizon, 28, 38, 52)

        # ---------------- SCENARIO SPECIFIC DRAWINGS ----------------
        if scenario == "no_helmet":
            # CAM 01: Factory Assembly Bay - Worker without hard hat
            # Overhead Crane rail & trolley
            fill_rect(buf, 20, 15, WIDTH - 40, 16, 45, 55, 72)
            trolley_x = int(WIDTH * 0.45 + math.sin(t * 1.5) * 60)
            fill_rect(buf, trolley_x, 12, 42, 22, 230, 170, 20) # Yellow crane
            # Cable drop
            draw_line(buf, trolley_x + 21, 34, trolley_x + 21, 80, 180, 180, 180)

            # Hazard floor tape
            for tx in range(0, WIDTH, 30):
                fill_rect(buf, tx, HEIGHT - 22, 14, 22, 220, 180, 20, alpha=0.7)

            # Worker walking across frame
            wx = int(WIDTH * 0.2 + (t / DURATION_SEC) * (WIDTH * 0.55))
            wy = int(HEIGHT * 0.65)
            # Head (NO HELMET - RED PULSING indicator)
            pulse_rad = 10 + math.sin(t * 8) * 2
            draw_circle(buf, wx, wy - 35, pulse_rad, 255, 50, 60, alpha=0.9)
            # Face
            draw_circle(buf, wx, wy - 35, 7, 240, 180, 150)
            # Body (blue work uniform)
            fill_rect(buf, wx - 12, wy - 24, 24, 40, 30, 50, 90)
            # Legs walking cycle
            leg_offset = int(math.sin(t * 10) * 8)
            fill_rect(buf, wx - 10, wy + 16, 8, 28 + leg_offset, 20, 30, 50)
            fill_rect(buf, wx + 2, wy + 16, 8, 28 - leg_offset, 20, 30, 50)

            # AI Bounding Box
            draw_hollow_rect(buf, wx - 20, wy - 48, 40, 96, 255, 51, 68, thickness=2)
            fill_rect(buf, wx - 20, wy - 60, 105, 12, 255, 51, 68)

        elif scenario == "unauthorized_entry":
            # CAM 02: Datacenter Server Vault - Intruder in restricted rack corridor
            # Server racks lining both sides
            for r in range(4):
                rx = 20 + r * 110
                fill_rect(buf, rx, 35, 90, int(HEIGHT * 0.72), 15, 22, 35)
                # Rack server blades
                for b in range(12):
                    by = 45 + b * 14
                    fill_rect(buf, rx + 6, by, 78, 10, 8, 12, 18)
                    # Blinking LEDs (Blue/Cyan and Amber)
                    led1 = 255 if math.sin(t * 6 + r + b) > 0 else 30
                    led2 = 255 if math.cos(t * 4 + b) > 0 else 30
                    fill_rect(buf, rx + 10, by + 3, 4, 4, 0, led1, 255)
                    fill_rect(buf, rx + 18, by + 3, 4, 4, 255, led2, 50)

            # Intruder sneaking in dark hoodie
            ix = int(WIDTH * 0.48 + math.sin(t * 0.8) * 25)
            iy = int(HEIGHT * 0.68)
            # Dark hooded head
            draw_circle(buf, ix, iy - 34, 11, 20, 25, 35)
            # Dark jacket
            fill_rect(buf, ix - 14, iy - 22, 28, 42, 15, 20, 30)
            fill_rect(buf, ix - 10, iy + 20, 8, 26, 10, 14, 22)
            fill_rect(buf, ix + 2, iy + 20, 8, 26, 10, 14, 22)

            # AI Bounding Box
            draw_hollow_rect(buf, ix - 22, wy_box := (iy - 48), 44, 98, 255, 51, 68, thickness=2)
            fill_rect(buf, ix - 22, wy_box - 12, 120, 12, 255, 51, 68)

        elif scenario == "slip_fall_hazard":
            # CAM 03: Logistics Aisle - Chemical spill liquid puddle
            # High storage pallet racks on edges
            fill_rect(buf, 10, 25, 60, int(HEIGHT * 0.8), 24, 34, 48)
            fill_rect(buf, WIDTH - 70, 25, 60, int(HEIGHT * 0.8), 24, 34, 48)

            # Moving background forklift silhouette
            fx = int(WIDTH * 0.2 + (t / DURATION_SEC) * (WIDTH * 0.4))
            fill_rect(buf, fx, horizon + 10, 48, 30, 220, 160, 20)
            fill_rect(buf, fx + 36, horizon - 5, 8, 45, 40, 40, 40) # Mast

            # Liquid puddle expanding on floor
            p_size = 50 + math.sin(t * 2) * 6
            draw_ellipse(buf, WIDTH * 0.5, HEIGHT * 0.76, p_size, 20, 255, 183, 3, alpha=0.65)
            draw_ellipse(buf, WIDTH * 0.5 - 15, HEIGHT * 0.74, 16, 7, 255, 220, 100, alpha=0.8)

            # AI Hazard Box
            draw_hollow_rect(buf, WIDTH * 0.5 - 65, HEIGHT * 0.76 - 25, 130, 48, 255, 183, 3, thickness=2)
            fill_rect(buf, WIDTH * 0.5 - 65, HEIGHT * 0.76 - 37, 105, 12, 255, 183, 3)

        elif scenario == "exit_blocked":
            # CAM 04: Emergency Fire Exit - Door obstructed by cargo
            # Red fire exit door
            door_x = int(WIDTH * 0.38)
            door_w = int(WIDTH * 0.25)
            fill_rect(buf, door_x, 35, door_w, int(HEIGHT * 0.75), 70, 20, 25)
            # Green illuminated EXIT sign above door
            fill_rect(buf, door_x + 20, 20, door_w - 40, 14, 20, 160, 60)

            # Stacked wooden freight crates blocking exit
            fill_rect(buf, door_x - 10, int(HEIGHT * 0.52), 55, 48, 140, 90, 40)
            fill_rect(buf, door_x + 35, int(HEIGHT * 0.56), 65, 44, 125, 80, 35)
            fill_rect(buf, door_x + 12, int(HEIGHT * 0.38), 50, 40, 155, 100, 45)

            # AI Bounding Box
            draw_hollow_rect(buf, door_x - 15, int(HEIGHT * 0.34), door_w + 35, int(HEIGHT * 0.65), 255, 183, 3, thickness=2)
            fill_rect(buf, door_x - 15, int(HEIGHT * 0.34) - 12, 115, 12, 255, 183, 3)

        elif scenario == "normal_traffic":
            # CAM 05: Main Entrance Turnstiles - Safe badged pedestrian flow
            # Turnstile gates
            fill_rect(buf, int(WIDTH * 0.28), int(HEIGHT * 0.55), 16, 42, 60, 75, 95)
            fill_rect(buf, int(WIDTH * 0.62), int(HEIGHT * 0.55), 16, 42, 60, 75, 95)

            # Pedestrian walking through smoothly
            px = int(WIDTH * 0.36 + math.sin(t * 1.2) * 35)
            py = int(HEIGHT * 0.65)
            # Head with Green Verified Badge
            draw_circle(buf, px, py - 32, 8, 230, 180, 150)
            draw_circle(buf, px + 8, py - 38, 5, 118, 185, 0) # Green check badge
            # Body
            fill_rect(buf, px - 10, py - 22, 20, 38, 40, 50, 65)
            fill_rect(buf, px - 8, py + 16, 7, 26, 25, 30, 40)
            fill_rect(buf, px + 1, py + 16, 7, 26, 25, 30, 40)

            # Safe perimeter tag
            fill_rect(buf, px - 25, py - 52, 60, 10, 118, 185, 0, alpha=0.85)

        else:
            # CAM 06: Chemical Storage Loading Dock
            # Delivery Truck docked
            truck_x = int(WIDTH * 0.22)
            fill_rect(buf, truck_x, int(HEIGHT * 0.35), int(WIDTH * 0.55), int(HEIGHT * 0.45), 35, 45, 60)
            fill_rect(buf, truck_x + 15, int(HEIGHT * 0.42), int(WIDTH * 0.4), int(HEIGHT * 0.3), 50, 65, 85)
            # Wheels
            draw_circle(buf, truck_x + 50, int(HEIGHT * 0.8), 16, 20, 20, 25)
            draw_circle(buf, truck_x + int(WIDTH * 0.45), int(HEIGHT * 0.8), 16, 20, 20, 25)
            # Safety cones
            fill_rect(buf, truck_x - 25, int(HEIGHT * 0.75), 14, 20, 255, 110, 20)

        # Apply scanlines and surveillance noise
        apply_cctv_effects(buf, f)

        # Pipe frame bytes into ffmpeg
        proc.stdin.write(buf)

    proc.stdin.close()
    proc.wait()
    print(f"✅ Generated: {output_path} ({os.path.getsize(output_path) // 1024} KB)")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    scenarios = [
        ("CAM-01", "no_helmet", os.path.join(OUTPUT_DIR, "cam1_factory_helmet.mp4")),
        ("CAM-02", "unauthorized_entry", os.path.join(OUTPUT_DIR, "cam2_server_intruder.mp4")),
        ("CAM-03", "slip_fall_hazard", os.path.join(OUTPUT_DIR, "cam3_warehouse_spill.mp4")),
        ("CAM-04", "exit_blocked", os.path.join(OUTPUT_DIR, "cam4_exit_blocked.mp4")),
        ("CAM-05", "normal_traffic", os.path.join(OUTPUT_DIR, "cam5_entrance_clear.mp4")),
        ("CAM-06", "loading_dock", os.path.join(OUTPUT_DIR, "cam6_loading_dock.mp4"))
    ]

    print("\n🎥 Rendering All 6 EdgeVision CCTV Scenarios into H.264 MP4s...")
    for cam_id, sc, path in scenarios:
        generate_video(cam_id, sc, path)
    
    print("\n🎉 All 6 video clips generated successfully in static/videos/!")

if __name__ == "__main__":
    main()
