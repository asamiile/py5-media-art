from pathlib import Path
import shutil
import subprocess
import sys
import random
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

# Physarum simulation parameters
NUM_AGENTS = 150000
SENSOR_ANGLE = np.pi / 4.0
SENSOR_OFFSET = 35
ROTATION_ANGLE = np.pi / 4.0
STEP_SIZE = 3
DECAY = 0.90

agents_pos = None
agents_ang = None
trail_map = None

def setup():
    global agents_pos, agents_ang, trail_map
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize agents at the center
    agents_pos = np.zeros((NUM_AGENTS, 2), dtype=np.float32)
    agents_pos[:, 0] = SIZE[0] / 2.0 + np.random.randn(NUM_AGENTS) * 50
    agents_pos[:, 1] = SIZE[1] / 2.0 + np.random.randn(NUM_AGENTS) * 50
    agents_ang = np.random.rand(NUM_AGENTS).astype(np.float32) * 2 * np.pi
    
    trail_map = np.zeros((SIZE[1], SIZE[0]), dtype=np.float32)
    
    py5.background(0)

def draw():
    global agents_pos, agents_ang, trail_map
    
    w, h = SIZE[0], SIZE[1]
    
    # 1. Sense
    def get_sense(angle_offset):
        angles = agents_ang + angle_offset
        sx = np.clip((agents_pos[:, 0] + np.cos(angles) * SENSOR_OFFSET).astype(np.int32), 0, w - 1)
        sy = np.clip((agents_pos[:, 1] + np.sin(angles) * SENSOR_OFFSET).astype(np.int32), 0, h - 1)
        return trail_map[sy, sx]

    sense_f = get_sense(0)
    sense_l = get_sense(-SENSOR_ANGLE)
    sense_r = get_sense(SENSOR_ANGLE)
    
    # 2. Rotate
    rand_steer = (np.random.rand(NUM_AGENTS).astype(np.float32) - 0.5) * 0.5
    
    mask_f = (sense_f > sense_l) & (sense_f > sense_r)
    mask_lr = (sense_f < sense_l) & (sense_f < sense_r)
    mask_l = (~mask_f) & (~mask_lr) & (sense_l > sense_r)
    mask_r = (~mask_f) & (~mask_lr) & (sense_r > sense_l)
    
    turn_l_or_r = np.random.rand(NUM_AGENTS) < 0.5
    mask_lr_l = mask_lr & turn_l_or_r
    mask_lr_r = mask_lr & ~turn_l_or_r
    
    agents_ang[mask_l | mask_lr_l] -= ROTATION_ANGLE
    agents_ang[mask_r | mask_lr_r] += ROTATION_ANGLE
    agents_ang += rand_steer
    
    # 3. Move
    agents_pos[:, 0] += np.cos(agents_ang) * STEP_SIZE
    agents_pos[:, 1] += np.sin(agents_ang) * STEP_SIZE
    
    # 4. Handle bounds
    out_x = (agents_pos[:, 0] < 0) | (agents_pos[:, 0] >= w)
    out_y = (agents_pos[:, 1] < 0) | (agents_pos[:, 1] >= h)
    
    agents_pos[out_x, 0] = np.clip(agents_pos[out_x, 0], 0, w - 1)
    agents_pos[out_y, 1] = np.clip(agents_pos[out_y, 1], 0, h - 1)
    
    agents_ang[out_x | out_y] = np.random.rand(np.sum(out_x | out_y)).astype(np.float32) * 2 * np.pi
    
    # 5. Deposit
    px = np.clip(agents_pos[:, 0].astype(np.int32), 0, w - 1)
    py = np.clip(agents_pos[:, 1].astype(np.int32), 0, h - 1)
    np.add.at(trail_map, (py, px), 1.0)
    
    # 6. Decay
    trail_map *= DECAY
    
    # Draw via np_pixels
    py5.load_np_pixels()
    
    # Use color map
    c_val = np.clip(trail_map, 0, 5) / 5.0
    r = (c_val * 50).astype(np.uint8)
    g = (c_val * 255).astype(np.uint8)
    b = (c_val * 200).astype(np.uint8)
    a = np.full_like(r, 255)
    
    color_arr = np.dstack((a, r, g, b))
    
    rh, rw = py5.np_pixels.shape[:2]
    if rh != h or rw != w:
        # Retina fallback
        import cv2
        resized = cv2.resize(color_arr, (rw, rh), interpolation=cv2.INTER_NEAREST)
        py5.np_pixels[:, :, :] = resized
    else:
        py5.np_pixels[:, :, :] = color_arr

    py5.update_np_pixels()
    
    # Draw agents as points using point() for brightness
    py5.blend_mode(py5.ADD)
    py5.stroke(100, 255, 255, 100)
    py5.stroke_weight(1)
    # Using py5.points() instead of looping
    py5.points(agents_pos)
    py5.blend_mode(py5.BLEND)
    
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
