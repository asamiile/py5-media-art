from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import cv2
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Simulation Coordinates (1920x1080)
SIM_W = 1920
SIM_H = 1080

# Metaballs (8 particles)
M = 8
mb_pos = np.zeros((M, 2), dtype=np.float32)
mb_vel = np.zeros((M, 2), dtype=np.float32)
mb_rad = np.array([120.0, 140.0, 110.0, 130.0, 150.0, 120.0, 130.0, 100.0], dtype=np.float32)

# Initialize positions and velocities
for i in range(M):
    mb_pos[i] = [np.random.rand() * SIM_W, np.random.rand() * SIM_H]
    angle = np.random.rand() * 2.0 * np.pi
    speed = 4.0 + np.random.rand() * 3.0
    mb_vel[i] = [np.cos(angle) * speed, np.sin(angle) * speed]

# Grid size for potential evaluation (downscaled for speed, upscaled for rendering)
GRID_W = 160
GRID_H = 90

# Telemetry: compact index (average distance of metaballs to centroid)
compactness_history = []
img_rgb_mid = None


def update_metaballs():
    """
    Updates positions of metaball centers, bouncing off walls.
    """
    global mb_pos, mb_vel
    mb_pos += mb_vel
    
    # Bounce off wall boundaries
    for i in range(M):
        if mb_pos[i, 0] < 150.0 or mb_pos[i, 0] > SIM_W - 150.0:
            mb_vel[i, 0] *= -1.0
        if mb_pos[i, 1] < 150.0 or mb_pos[i, 1] > SIM_H - 150.0:
            mb_vel[i, 1] *= -1.0
            
    # Clip position
    mb_pos[:, 0] = np.clip(mb_pos[:, 0], 150.0, SIM_W - 150.0)
    mb_pos[:, 1] = np.clip(mb_pos[:, 1], 150.0, SIM_H - 150.0)


def evaluate_field():
    """
    Computes potential field on the grid.
    \Phi(x, y) = \sum (r_i^2 / d_i^2)
    """
    y_indices, x_indices = np.indices((GRID_H, GRID_W), dtype=np.float32)
    
    # Scale grid coordinate to simulation space
    scale_x = SIM_W / GRID_W
    scale_y = SIM_H / GRID_H
    
    grid_x = x_indices * scale_x + scale_x / 2.0
    grid_y = y_indices * scale_y + scale_y / 2.0
    
    field = np.zeros((GRID_H, GRID_W), dtype=np.float32)
    
    for i in range(M):
        dx = grid_x - mb_pos[i, 0]
        dy = grid_y - mb_pos[i, 1]
        dist_sq = dx**2 + dy**2 + 10.0
        # Add contribution
        field += (mb_rad[i]**2) / dist_sq
        
    return field


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 1, 8)


def draw():
    global img_rgb_mid
    
    # --- 1. Physics update ---
    update_metaballs()
    field = evaluate_field()
    
    # Calculate compactness telemetry: standard deviation of distances to COM
    com = np.mean(mb_pos, axis=0)
    dists = np.linalg.norm(mb_pos - com, axis=1)
    compactness = np.mean(dists)
    compactness_history.append(compactness)
    if len(compactness_history) > 300:
        compactness_history.pop(0)
        
    t = py5.frame_count / 60.0
    
    # --- 2. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Slow fading background rect (long trails)
    py5.fill(2, 1, 8, 14)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scale coordinates to 4K
    py5.push_matrix()
    py5.scale(SIZE[0] / SIM_W, SIZE[1] / SIM_H)
    
    # Additive neon glow for outlines
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Upscale grid values to extract smooth contours via OpenCV
    # Resizing field to 960x540 for smoother contour lines
    field_upscaled = cv2.resize(field, (960, 540), interpolation=cv2.INTER_LINEAR)
    
    # Render multiple contour levels (isolines)
    levels = [0.12, 0.20, 0.32, 0.50, 0.80, 1.20, 1.80, 2.70, 4.00, 6.00]
    
    for idx, lvl in enumerate(levels):
        # Extract contour coordinates using OpenCV
        mask = (field_upscaled >= lvl).astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Color mapping: map level index to Hue (Violet to Cyan to Mint)
        h = 280.0 - (idx / len(levels)) * 140.0
        s = 85.0
        b = 60.0 + (idx / len(levels)) * 40.0
        py5.stroke(h, s, b, 120)
        
        # Dynamic stroke weight: outer lines are thin, inner cores are thick
        py5.stroke_weight(1.5 + idx * 0.4)
        py5.no_fill()
        
        # Scale contour coordinates back to SIM_W / SIM_H space
        scale_c_x = SIM_W / 960.0
        scale_c_y = SIM_H / 540.0
        
        for c in contours:
            py5.begin_shape()
            for pt in c:
                px, py = pt[0]
                py5.vertex(px * scale_c_x, py * scale_c_y)
            py5.end_shape(py5.CLOSE)
            
    py5.pop_matrix()
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("METABALL ISOLINE SPECTROMETER // MARCHING SQUARES CONTOURS", 50, 50)
    py5.text(f"METABALL CORES: {M} | CONTOUR LEVELS: {len(levels)}", 50, 85)
    py5.text(f"POTENTIAL THRESHOLDS: {levels[0]:.2f} -> {levels[-1]:.2f} V", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"FIELD SPATIAL COMPACTNESS: {compactness:.2f} px", SIZE[0] - 50, 85)
    
    # Compactness Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("SPATIAL COMPACTNESS HIST", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(181, 23, 158, 180)
    py5.begin_shape()
    for idx, val in enumerate(compactness_history):
        xx = gx + idx * (graph_w / 300)
        # Scale to fit graph box (val is between 200 and 700)
        yy = gy + graph_h - ((val - 200.0) / 500.0) * (graph_h - 10) - 5
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.jpg"))
    
    # Blank screen check
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
        
        # Save preview mid-frame (grab from screen buffer)
        py5.load_np_pixels()
        img_rgb_mid = py5.np_pixels[:, :, :3].copy()
        if img_rgb_mid is not None:
            img_bgr = cv2.cvtColor(img_rgb_mid, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(SKETCH_DIR / PREVIEW_FILENAME), img_bgr)
            print(f"[Render Preview] Saved preview to {PREVIEW_FILENAME}")
            
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.jpg"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Clean up frames
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)


py5.run_sketch()
