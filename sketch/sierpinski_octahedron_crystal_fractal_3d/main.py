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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def draw_octahedron(r):
    py5.begin_shape(py5.TRIANGLES)
    # Top half
    py5.vertex(0, -r, 0); py5.vertex(r, 0, 0); py5.vertex(0, 0, r)
    py5.vertex(0, -r, 0); py5.vertex(0, 0, r); py5.vertex(-r, 0, 0)
    py5.vertex(0, -r, 0); py5.vertex(-r, 0, 0); py5.vertex(0, 0, -r)
    py5.vertex(0, -r, 0); py5.vertex(0, 0, -r); py5.vertex(r, 0, 0)
    # Bottom half
    py5.vertex(0, r, 0); py5.vertex(r, 0, 0); py5.vertex(0, 0, r)
    py5.vertex(0, r, 0); py5.vertex(0, 0, r); py5.vertex(-r, 0, 0)
    py5.vertex(0, r, 0); py5.vertex(-r, 0, 0); py5.vertex(0, 0, -r)
    py5.vertex(0, r, 0); py5.vertex(0, 0, -r); py5.vertex(r, 0, 0)
    py5.end_shape()

def recursive_octahedron(r, depth, max_depth, t_phase, x, y, z):
    if depth == max_depth:
        # Distance from center calculates color and breathing pulse
        dist = np.sqrt(x**2 + y**2 + z**2)
        
        # Inner cores pulse differently than outer shells
        pulse = 1.0 + 0.15 * np.sin(t_phase * 2 + dist * 0.005)
        
        # Color shifts from Amethyst (280) on the outside to Hot Pink (330) on the inside
        hue = py5.remap(dist, 0, 600, 330, 270)
        
        py5.fill(hue, 90, 100, 60) # highly saturated and translucent
        draw_octahedron(r * pulse)
    else:
        new_r = r / 2.0
        # Breathing effect dynamically scales the distance of the vertices
        breathe = 1.0 + 0.05 * np.sin(t_phase * 1 + depth * 0.5)
        offset = new_r * breathe
        
        offsets = [
            (offset, 0, 0), (-offset, 0, 0),
            (0, offset, 0), (0, -offset, 0),
            (0, 0, offset), (0, 0, -offset)
        ]
        
        for ox, oy, oz in offsets:
            py5.push_matrix()
            py5.translate(ox, oy, oz)
            recursive_octahedron(new_r, depth + 1, max_depth, t_phase, x + ox, y + oy, z + oz)
            py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(280, 50, 5) # Very dark obsidian/amethyst black
    py5.lights()
    
    # Core internal point light
    py5.point_light(330, 100, 100, SIZE[0] / 2, SIZE[1] / 2, -200)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, -200)
    
    t_phase = (py5.frame_count / TOTAL_FRAMES) * py5.TWO_PI
    
    # Elegantly rotate the crystal
    py5.rotate_x(t_phase * 0.5)
    py5.rotate_y(t_phase)
    py5.rotate_z(t_phase * 0.25)
    
    py5.blend_mode(py5.ADD)
    py5.stroke(300, 80, 100, 20)
    py5.stroke_weight(1)
    
    # 5 levels of depth generates 6^5 = 7776 tiny octahedrons!
    recursive_octahedron(600, 1, 5, t_phase, 0, 0, 0)

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
