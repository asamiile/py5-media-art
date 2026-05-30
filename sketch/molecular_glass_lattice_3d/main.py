from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

GRID_SIZE = 7
SPACING = 150
nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes
    offset = (GRID_SIZE - 1) * SPACING / 2.0
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for z in range(GRID_SIZE):
                px = x * SPACING - offset
                py = y * SPACING - offset
                pz = z * SPACING - offset
                
                # Only keep nodes inside a roughly spherical volume
                dist = np.sqrt(px*px + py*py + pz*pz)
                if dist < offset * 1.2:
                    nodes.append({
                        "pos": np.array([px, py, pz]),
                        "dist": dist,
                        "idx": (x, y, z)
                    })

def draw():
    py5.background(15) # Very dark warm grey
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.04
    
    py5.light_specular(255, 255, 255)
    py5.directional_light(0, 0, 100, 1, 1, -1) # White light
    py5.directional_light(40, 100, 100, -1, -1, -0.5) # Amber light
    py5.ambient_light(30, 20, 20)
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_y(t * 0.3)
    py5.rotate_x(t * 0.2)
    py5.rotate_z(t * 0.1)
    
    py5.blend_mode(py5.ADD)
    
    # Store transformed positions to draw lines efficiently
    current_positions = []
    
    # Draw nodes
    py5.no_stroke()
    py5.specular(255, 255, 255)
    py5.shininess(80)
    
    for n in nodes:
        # Breathing pulse based on distance from center
        pulse = np.sin(n["dist"] * 0.01 - t) * 0.5 + 0.5
        
        # Expand out
        expansion = 1.0 + pulse * 0.3
        pos = n["pos"] * expansion
        current_positions.append(pos)
        
        py5.push_matrix()
        py5.translate(*pos)
        
        # Size pulses
        size = 15 + pulse * 15
        
        # Color pulses from deep orange to bright amber
        hue = 20 + pulse * 20
        py5.fill(hue, 80, 50 + pulse*50, 80)
        
        py5.sphere(size)
        py5.pop_matrix()
        
    # Draw connections
    py5.stroke_weight(2)
    
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1 = nodes[i]
            n2 = nodes[j]
            
            # If they are adjacent in the original grid
            dx = abs(n1["idx"][0] - n2["idx"][0])
            dy = abs(n1["idx"][1] - n2["idx"][1])
            dz = abs(n1["idx"][2] - n2["idx"][2])
            
            if dx + dy + dz == 1:
                p1 = current_positions[i]
                p2 = current_positions[j]
                
                # Pulse connection color
                avg_dist = (n1["dist"] + n2["dist"]) / 2
                pulse = np.sin(avg_dist * 0.01 - t) * 0.5 + 0.5
                
                py5.stroke(10 + pulse*20, 100, 40 + pulse*60, 60 + pulse*40)
                py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
                
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)

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
            
        os._exit(0)

py5.run_sketch()
