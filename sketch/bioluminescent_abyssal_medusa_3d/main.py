from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_TENTACLES = 150
TENTACLE_LENGTH = 40
tentacles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize tentacle roots on a circle
    for i in range(NUM_TENTACLES):
        angle = py5.random(py5.TWO_PI)
        radius = py5.random(50, 200)
        # Store initial parameters: angle, radius, phase
        tentacles.append({
            'angle': angle,
            'radius': radius,
            'phase': py5.random(1000)
        })

def draw():
    py5.background(0, 0, 5) # Abyssal Black
    
    py5.ambient_light(20, 20, 40)
    py5.directional_light(0, 255, 255, 0, 1, -1) # Bioluminescent Cyan from above
    py5.point_light(138, 43, 226, 0, 400, 0) # Deep Violet from below
    
    py5.translate(py5.width / 2, py5.height / 2 - 200, -300)
    
    t = py5.frame_count * 0.02
    
    # Slow drift
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_z(np.sin(t * 0.5) * 0.1)
    
    # Draw the Medusa Bell
    py5.no_stroke()
    py5.fill(220, 240, 255, 40) # Ghostly Translucent White
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    
    res = 40
    pulse = np.sin(t * 2) * 0.2 + 1.0 # Pulsating motion
    
    for i in range(res):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        lat1 = (i / res) * py5.PI / 2 # Upper hemisphere
        lat2 = ((i + 1) / res) * py5.PI / 2
        for j in range(res + 1):
            lon = (j / res) * py5.TWO_PI
            
            # Ripple effect on the edge
            ripple1 = np.sin(lon * 8 + t * 4) * 20 * (lat1 / (py5.PI/2))
            ripple2 = np.sin(lon * 8 + t * 4) * 20 * (lat2 / (py5.PI/2))
            
            r1 = 250 * pulse + ripple1
            r2 = 250 * pulse + ripple2
            
            x1 = r1 * np.cos(lon) * np.sin(lat1)
            y1 = r1 * np.cos(lat1) - 100
            z1 = r1 * np.sin(lon) * np.sin(lat1)
            
            x2 = r2 * np.cos(lon) * np.sin(lat2)
            y2 = r2 * np.cos(lat2) - 100
            z2 = r2 * np.sin(lon) * np.sin(lat2)
            
            py5.vertex(x1, y1, z1)
            py5.vertex(x2, y2, z2)
        py5.end_shape()
        
    # Draw the tentacles
    py5.stroke_weight(2)
    py5.no_fill()
    
    for tentacle in tentacles:
        angle = tentacle['angle']
        radius = tentacle['radius'] * pulse
        phase = tentacle['phase']
        
        py5.begin_shape(py5.LINES)
        
        x = radius * np.cos(angle)
        y = 250 * pulse * np.cos(py5.PI/2) - 100 # base of the bell
        z = radius * np.sin(angle)
        
        # Color based on radius (inner = cyan, outer = violet)
        if radius < 100:
            py5.stroke(0, 255, 255, 100) # Cyan
        else:
            py5.stroke(138, 43, 226, 80) # Violet
            
        py5.vertex(x, y, z)
        
        # Draw a chain for the tentacle
        for k in range(1, TENTACLE_LENGTH):
            # Previous point
            py5.vertex(x, y, z)
            
            # Noise-driven sway
            nx = py5.os_noise(phase * 0.1, k * 0.05, t * 0.5) - 0.5
            nz = py5.os_noise(phase * 0.1 + 100, k * 0.05, t * 0.5) - 0.5
            
            x += nx * 15
            y += 20 # trails downwards
            z += nz * 15
            
            # Fade out alpha towards the tip
            alpha = int(100 * (1 - k / TENTACLE_LENGTH))
            if radius < 100:
                py5.stroke(0, 255, 255, alpha)
            else:
                py5.stroke(138, 43, 226, alpha)
                
            py5.vertex(x, y, z)
            
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
