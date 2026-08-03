import math
import shutil
import subprocess
import sys
from pathlib import Path
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"

# 20 seconds @ 60 FPS
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Offscreen drawing resolution (960x540)
SIM_W, SIM_H = 960, 540

# Epicycle Parameters: (radius, base_frequency, phase_offset)
ARMS = [
    (150.0, 1.0, 0.0),
    (80.0, -3.0, 0.5),
    (45.0, 7.0, 1.2),
    (20.0, -13.0, 2.3)
]

# State Variables
t = 0.0
prev_tip = None
pg = None

def setup():
    global pg
    py5.size(*SIZE)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Create offscreen trail graphics buffer
    pg = py5.create_graphics(SIM_W, SIM_H)
    pg.begin_draw()
    pg.background(8, 6, 12)  # Obsidian Space Void
    pg.end_draw()

def _get_linkage_points(time, speed_mod, arm2_drift, arm3_drift):
    """Calculate the absolute positions of all joints in the linkage."""
    cx, cy = SIM_W / 2.0, SIM_H / 2.0
    points = [(cx, cy)]
    
    x, y = cx, cy
    for i, (r, freq, phi) in enumerate(ARMS):
        f = freq * speed_mod
        if i == 1:
            f += arm2_drift
        elif i == 2:
            f += arm3_drift
            
        angle = f * time + phi
        x += r * math.cos(angle)
        y += r * math.sin(angle)
        points.append((x, y))
        
    return points

def draw():
    global t, prev_tip
    fc = py5.frame_count

    # 1. Modulation LFOs
    speed_mod = 1.0 + 0.25 * math.sin(fc * 0.004)
    arm2_drift = 0.12 * math.cos(fc * 0.007)
    arm3_drift = 0.18 * math.sin(fc * 0.005)

    # 2. Render Trail to Offscreen Buffer (Run multiple steps for high density)
    steps = 15
    dt = 0.008
    
    pg.begin_draw()
    pg.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Fade trail slowly over time to create a organic decay tail
    pg.no_stroke()
    pg.fill(248, 50, 10, 2)  # Decay overlay (HSB equivalent of deep obsidian)
    pg.rect(0, 0, SIM_W, SIM_H)
    
    for _ in range(steps):
        pts = _get_linkage_points(t, speed_mod, arm2_drift, arm3_drift)
        tip = pts[-1]
        
        if prev_tip is not None:
            # Color shifts through hues dynamically
            hue = (fc * 0.1 + t * 50) % 360
            pg.stroke(hue, 85, 95, 80)
            pg.stroke_weight(1.2)
            pg.line(prev_tip[0], prev_tip[1], tip[0], tip[1])
            
        prev_tip = tip
        t += dt
        
    pg.end_draw()

    # 3. Blit upscaled trail buffer to 4K canvas
    py5.image(pg, 0, 0, py5.width, py5.height)

    # 4. Draw Mechanical Linkage and Gears in 4K
    scale_x = py5.width / SIM_W
    scale_y = py5.height / SIM_H
    
    # Get current 4K linkage points
    pts = _get_linkage_points(t, speed_mod, arm2_drift, arm3_drift)
    pts_4k = [(x * scale_x, y * scale_y) for x, y in pts]
    
    # Draw gear orbits and arm lines
    for i in range(len(pts_4k) - 1):
        p1 = pts_4k[i]
        p2 = pts_4k[i + 1]
        
        # Calculate arm length in 4K
        r_4k = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        
        # Draw circular gear tracks
        py5.no_fill()
        py5.stroke(0, 240, 255, 30 - i * 6)
        py5.stroke_weight(1)
        py5.ellipse(p1[0], p1[1], r_4k * 2, r_4k * 2)
        
        # Draw glowing structural arm linkages
        py5.stroke(255, 140)
        py5.stroke_weight(2)
        py5.line(p1[0], p1[1], p2[0], p2[1])
        
        # Draw joint nodes
        py5.fill(0, 240, 255, 200)
        py5.no_stroke()
        py5.ellipse(p1[0], p1[1], 10, 10)
        
    # Draw final drawing tip node
    py5.fill(255, 180, 0, 255)
    py5.ellipse(pts_4k[-1][0], pts_4k[-1][1], 14, 14)

    # 5. Draw Astro-Laboratory HUD in 4K
    # Border & Targets
    py5.stroke(0, 240, 255, 100)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.rect(40, 40, py5.width - 80, py5.height - 80)
    
    # Corner target ticks
    for cx, cy in [(40, 40), (py5.width - 40, 40), (40, py5.height - 40), (py5.width - 40, py5.height - 40)]:
        py5.stroke(0, 240, 255, 180)
        py5.stroke_weight(3)
        py5.line(cx - 20, cy, cx + 20, cy)
        py5.line(cx, cy - 20, cx, cy + 20)

    # Telemetry data text block (left side)
    py5.fill(0, 240, 255, 220)
    py5.text_size(24)
    py5.text("SYSTEM: ASTRO-MECHANICAL FOURIER PANTOGRAPH", 80, 100)
    
    py5.text_size(18)
    py5.fill(255, 200)
    py5.text("ACTIVE HARMONIC LINKAGES : 4 CHANNELS", 80, 140)
    py5.text(f"BASE FREQUENCIES         : {[a[1] for a in ARMS]} rad/s", 80, 170)
    py5.text(f"LFO SPEED MODULATION     : {speed_mod:.4f}x", 80, 200)
    py5.text(f"RESOLVED PATH STEPS      : {fc * steps} ORBITS", 80, 230)
    
    # Draw real-time Fourier amplitude spectrum chart
    py5.text("FOURIER SPECTRUM MATRIX :", 80, 280)
    chart_y = 310
    for i, (r, freq, _) in enumerate(ARMS):
        # Base amplitude height
        bar_h = int(r * 0.7)
        # Add a tiny resonance animation to the bars
        bar_h += int(8 * math.sin(fc * 0.05 + i))
        
        py5.fill(0, 240, 255, 60)
        py5.rect(80 + i * 45, chart_y + (120 - bar_h), 30, bar_h)
        py5.fill(255, 200)
        py5.text_size(12)
        py5.text(f"F{i+1}", 90 + i * 45, chart_y + 140)

    # Diagnostic circular radar (left bottom corner)
    radar_cx, radar_cy = 150, py5.height - 180
    py5.no_fill()
    py5.stroke(0, 240, 255, 50)
    py5.stroke_weight(1)
    py5.ellipse(radar_cx, radar_cy, 120, 120)
    py5.ellipse(radar_cx, radar_cy, 60, 60)
    py5.line(radar_cx - 70, radar_cy, radar_cx + 70, radar_cy)
    py5.line(radar_cx, radar_cy - 70, radar_cx, radar_cy + 70)
    
    # Draw sweep indicators showing angular state of each arm
    for i, (r, freq, phi) in enumerate(ARMS):
        f = freq * speed_mod
        if i == 1:
            f += arm2_drift
        elif i == 2:
            f += arm3_drift
        angle = f * t + phi
        
        py5.stroke(0, 240, 255, 100 + i * 40)
        py5.stroke_weight(2)
        rad = 20 + i * 12
        py5.line(radar_cx, radar_cy, radar_cx + rad * math.cos(angle), radar_cy + rad * math.sin(angle))
        
    py5.text_size(14)
    py5.fill(0, 240, 255, 180)
    py5.text("ORBITAL DIAGNOSTICS", radar_cx - 70, radar_cy + 90)

    # Progress bar (right side)
    bar_width = 300
    bar_x = py5.width - 80 - bar_width
    bar_y = 90
    py5.no_fill()
    py5.stroke(0, 240, 255, 100)
    py5.stroke_weight(2)
    py5.rect(bar_x, bar_y, bar_width, 16)
    
    py5.fill(0, 240, 255, 180)
    py5.no_stroke()
    py5.rect(bar_x + 2, bar_y + 2, (bar_width - 4) * (fc / TOTAL_FRAMES), 12)
    
    py5.fill(255, 220)
    py5.text_size(18)
    py5.text(f"FRAME RENDER : {fc} / {TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)", bar_x, bar_y - 15)

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if fc == 2 or fc % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {fc} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Render progress logging
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
