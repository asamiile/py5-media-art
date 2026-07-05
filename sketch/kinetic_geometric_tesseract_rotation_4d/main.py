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

# Generate 4D hypercube vertices
vertices_4d = []
for i in [-1, 1]:
    for j in [-1, 1]:
        for k in [-1, 1]:
            for l in [-1, 1]:
                vertices_4d.append([i, j, k, l])
vertices_4d = np.array(vertices_4d, dtype=np.float32)

# Generate edges (connect if they differ by exactly 1 coordinate)
edges = []
for i in range(16):
    for j in range(i + 1, 16):
        diff = np.abs(vertices_4d[i] - vertices_4d[j])
        if np.sum(diff) == 2.0: # since diff between -1 and 1 is 2
            edges.append((i, j))

num_tesseracts = 40

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 10, 15)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_weight(2)

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.015
    
    # Draw nested tesseracts
    for t in range(num_tesseracts):
        # Phase offset for each nested shape
        phase = time_val + t * 0.05
        scale_4d = 1.0 + (t * 0.05)
        
        # 4D Rotation matrix (XW and YZ planes)
        cos_xw, sin_xw = np.cos(phase), np.sin(phase)
        cos_yz, sin_yz = np.cos(phase * 0.7), np.sin(phase * 0.7)
        cos_zw, sin_zw = np.cos(phase * 0.3), np.sin(phase * 0.3)
        
        rot_xw = np.array([
            [cos_xw, 0, 0, -sin_xw],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [sin_xw, 0, 0, cos_xw]
        ])
        
        rot_yz = np.array([
            [1, 0, 0, 0],
            [0, cos_yz, -sin_yz, 0],
            [0, sin_yz, cos_yz, 0],
            [0, 0, 0, 1]
        ])
        
        rot_zw = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, cos_zw, -sin_zw],
            [0, 0, sin_zw, cos_zw]
        ])
        
        # Apply 4D rotations
        v_rot = vertices_4d.dot(rot_xw).dot(rot_yz).dot(rot_zw) * scale_4d
        
        # Stereographic projection 4D -> 3D
        # Distance from projection point
        w_dist = 4.0
        w_factor = 1.0 / (w_dist - v_rot[:, 3])
        
        v_3d = np.zeros((16, 3))
        v_3d[:, 0] = v_rot[:, 0] * w_factor
        v_3d[:, 1] = v_rot[:, 1] * w_factor
        v_3d[:, 2] = v_rot[:, 2] * w_factor
        
        # 3D rotation (slow orbit)
        cos_y, sin_y = np.cos(time_val * 0.2), np.sin(time_val * 0.2)
        rot_y = np.array([
            [cos_y, 0, sin_y],
            [0, 1, 0],
            [-sin_y, 0, cos_y]
        ])
        v_3d = v_3d.dot(rot_y)
        
        # 3D -> 2D Perspective
        fov = 1000.0
        z_dist = 2.0
        z_factor = fov / (z_dist - v_3d[:, 2])
        
        v_2d = np.zeros((16, 2))
        v_2d[:, 0] = v_3d[:, 0] * z_factor + py5.width / 2
        v_2d[:, 1] = v_3d[:, 1] * z_factor + py5.height / 2
        
        # Color mapping based on nested depth
        hue = (160 + t * 4) % 360
        py5.stroke(hue, 90, 100, 25)
        
        # Draw edges
        for edge in edges:
            p1 = v_2d[edge[0]]
            p2 = v_2d[edge[1]]
            py5.line(p1[0], p1[1], p2[0], p2[1])

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
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
            
        import os
        os._exit(0)

py5.run_sketch()
