from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Precompute shards
num_shards = 200
shard_pos = np.random.uniform(-400, 400, (num_shards, 3))
shard_pos[:, 2] = np.random.uniform(-800, 200, num_shards) # Z depth
shard_rot_axis = np.random.uniform(-1, 1, (num_shards, 3))
shard_rot_speed = np.random.uniform(1.0, 3.0, num_shards)
shard_sizes = np.random.uniform(20, 80, num_shards)
shard_hues = np.random.choice([180, 320, 90], num_shards) # Cyan, Magenta, Lime

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Camera gently moves forward
    py5.translate(0, 0, t * 800)
    
    # 6-fold radial symmetry
    for mirror in range(6):
        py5.push_matrix()
        py5.rotate_z(mirror * py5.TWO_PI / 6.0)
        
        for i in range(num_shards):
            py5.push_matrix()
            
            # Z position moves toward camera and wraps around
            pz = shard_pos[i, 2] + t * 800
            if pz > 400:
                pz -= 1200
            
            py5.translate(float(shard_pos[i, 0]), float(shard_pos[i, 1]), float(pz))
            
            # Additive oscillation
            pulse = py5.sin(t * py5.TWO_PI * 2.0 + i) * 0.5 + 0.5
            py5.fill(float(shard_hues[i]), 80, 80, 60 + pulse * 40)
            
            # Rotate shard
            rx, ry, rz = shard_rot_axis[i]
            py5.rotate(t * py5.TWO_PI * shard_rot_speed[i], float(rx), float(ry), float(rz))
            
            s = shard_sizes[i]
            py5.begin_shape(py5.TRIANGLES)
            py5.vertex(0, -s, 0)
            py5.vertex(s*0.866, s*0.5, 0)
            py5.vertex(-s*0.866, s*0.5, 0)
            py5.end_shape()
            
            py5.pop_matrix()
        py5.pop_matrix()

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
