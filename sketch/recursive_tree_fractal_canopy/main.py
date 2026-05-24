from pathlib import Path
import shutil
import subprocess
import sys
import py5

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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def setup():
    py5.size(*SIZE, py5.P3D) # P3D for performance
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_branch(len, depth, max_depth, t):
    # Map depth to color and thickness
    hue = (depth * 25 + t * 20) % 360
    py5.stroke(hue, 80, 100, 90)
    py5.stroke_weight(py5.remap(depth, 0, max_depth, 15, 1))
    
    # Draw current branch
    py5.line(0, 0, 0, -len)
    
    # Move to the end of the branch
    py5.translate(0, -len)
    
    if depth < max_depth:
        # Calculate wind effect using Perlin noise
        # The noise space is sampled based on depth and time to create propagating waves
        noise_val = py5.noise(depth * 0.1, t * 0.5)
        wind_angle = py5.remap(noise_val, 0, 1, -py5.PI/8, py5.PI/8)
        
        # Base branch angles
        angle_a = py5.PI / 6 + wind_angle
        angle_b = -py5.PI / 5 + wind_angle
        angle_c = wind_angle * 1.5 # Center small branch
        
        len_shrink = 0.7
        
        # Right branch
        py5.push_matrix()
        py5.rotate(angle_a)
        draw_branch(len * len_shrink, depth + 1, max_depth, t)
        py5.pop_matrix()
        
        # Left branch
        py5.push_matrix()
        py5.rotate(angle_b)
        draw_branch(len * len_shrink, depth + 1, max_depth, t)
        py5.pop_matrix()
        
        # Occasional center branch for fuller canopy
        if depth % 2 == 0:
            py5.push_matrix()
            py5.rotate(angle_c)
            draw_branch(len * 0.5, depth + 1, max_depth, t)
            py5.pop_matrix()
    else:
        # Draw glowing leaves at the tips
        py5.no_stroke()
        py5.fill(hue, 60, 100, 80)
        leaf_size = 10 + py5.sin(t * 3 + depth) * 5
        py5.circle(0, 0, leaf_size)

def draw():
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    # Draw three overlapping trees to form a forest canopy
    py5.translate(py5.width / 2, py5.height)
    
    # Center tree
    py5.push_matrix()
    draw_branch(250, 0, 10, t)
    py5.pop_matrix()
    
    # Left tree
    py5.push_matrix()
    py5.translate(-500, 100)
    py5.rotate(py5.PI/16)
    draw_branch(200, 0, 9, t + 10)
    py5.pop_matrix()
    
    # Right tree
    py5.push_matrix()
    py5.translate(500, 100)
    py5.rotate(-py5.PI/16)
    draw_branch(200, 0, 9, t + 20)
    py5.pop_matrix()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
