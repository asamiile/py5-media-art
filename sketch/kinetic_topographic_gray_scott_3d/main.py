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

# Grid Size for 3D Topographic Projection (kept small for python sorting speed)
N = 72
u = np.ones((N, N), dtype=np.float32)
v = np.zeros((N, N), dtype=np.float32)

# Seed initial spot in center
r = 6
cx, cy = N // 2, N // 2
u[cy-r:cy+r, cx-r:cx+r] = 0.50
v[cy-r:cy+r, cx-r:cx+r] = 0.25
# Add some noise to break symmetry
u += np.random.normal(0, 0.02, (N, N))
v += np.random.normal(0, 0.02, (N, N))

# Gray-Scott constants (Bacteria spots / mitosis parameters)
Du, Dv, F, k = 0.16, 0.08, 0.035, 0.060

# Telemetry: Spatial variance of concentration
variance_history = []
img_rgb_mid = None


def update_gray_scott(steps=12):
    """
    Solves the Gray-Scott reaction diffusion PDEs using finite difference method.
    """
    global u, v
    
    # 5-point Laplacian roll slices
    for _ in range(steps):
        lap_u = (
            np.roll(u, 1, axis=0) +
            np.roll(u, -1, axis=0) +
            np.roll(u, 1, axis=1) +
            np.roll(u, -1, axis=1) -
            4.0 * u
        )
        lap_v = (
            np.roll(v, 1, axis=0) +
            np.roll(v, -1, axis=0) +
            np.roll(v, 1, axis=1) +
            np.roll(v, -1, axis=1) -
            4.0 * v
        )
        
        uvv = u * v * v
        u += Du * lap_u - uvv + F * (1.0 - u)
        v += Dv * lap_v + uvv - (F + k) * v
        
        # Clip values for stability
        np.clip(u, 0.0, 1.0, out=u)
        np.clip(v, 0.0, 1.0, out=v)


def get_projected_grid(t):
    """
    Constructs 3D mesh points from concentrations, rotates, and projects to 2D screen coordinates.
    """
    # Create coordinate grid in [-350, 350]
    x = np.linspace(-420.0, 420.0, N)
    y = np.linspace(-420.0, 420.0, N)
    xx, yy = np.meshgrid(x, y)
    
    # Map activator concentration v to Z height
    # Scale height (mountain peaks) up to 260px
    zz = v * 280.0
    
    # Flatten arrays for matrix transforms
    pts = np.stack([xx.flatten(), yy.flatten(), zz.flatten()], axis=-1)
    
    # Rotate 3D points
    # Pitch (look down slightly)
    angle_x = np.radians(45.0)
    # Yaw (slowly rotate over time)
    angle_z = t * 0.08
    
    # Rotation matrix Z (yaw)
    Rz = np.array([
        [np.cos(angle_z), -np.sin(angle_z), 0],
        [np.sin(angle_z),  np.cos(angle_z), 0],
        [0, 0, 1]
    ], dtype=np.float32)
    
    # Rotation matrix X (pitch)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(angle_x), -np.sin(angle_x)],
        [0, np.sin(angle_x),  np.cos(angle_x)]
    ], dtype=np.float32)
    
    # Combine rotations
    R = Rx @ Rz
    rotated_pts = pts @ R.T
    
    # Orthographic projection to center of screen (1920x1080)
    proj_pts = rotated_pts[:, :2] + np.array([1920 / 2, 1080 / 2 + 50], dtype=np.float32)
    
    # Keep track of depth (Z coordinate after rotation) for Painter's depth sorting
    depths = rotated_pts[:, 2]
    
    return proj_pts.reshape(N, N, 2), depths.reshape(N, N)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 2, 5)


def draw():
    global img_rgb_mid
    
    # --- 1. Physics update ---
    update_gray_scott()
    
    # Calculate telemetry
    variance = np.var(v)
    variance_history.append(variance)
    if len(variance_history) > 300:
        variance_history.pop(0)
        
    t = py5.frame_count / 60.0
    
    # Get projected mesh positions and depths
    proj_grid, depths = get_projected_grid(t)
    
    # --- 2. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Slow fading background rect
    py5.fill(2, 2, 5, 24)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.push_matrix()
    # Scale simulation coordinate (1920x1080) to 4K
    py5.scale(SIZE[0] / 1920, SIZE[1] / 1080)
    
    # Additive neon glow
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Painter's Algorithm: Sort rows by average depth from back to front
    # The back rows have smaller depth (Z after rotation)
    row_depths = np.mean(depths, axis=1)
    sorted_rows = np.argsort(row_depths)
    
    for r_idx in sorted_rows:
        # Draw horizontal polyline for this row
        py5.begin_shape()
        py5.no_fill()
        py5.stroke_weight(1.8)
        
        for c_idx in range(N):
            px, py = proj_grid[r_idx, c_idx]
            # Height intensity (from concentration v)
            h_val = v[r_idx, c_idx]
            
            # Map concentration to Hue (Violet to Aqua to Amber)
            h = 280.0 - h_val * 200.0
            s = 85.0
            b = 75.0 + h_val * 25.0
            
            py5.stroke(h, s, b, 140)
            py5.vertex(px, py)
        py5.end_shape()
        
        # Connect vertical grid lines to the previous row (columns)
        # If not the back-most row (average depth is smallest), connect to neighbor row in depth order
        if r_idx > 0:
            py5.stroke_weight(1.2)
            for c_idx in range(0, N, 2):  # Sparser columns for clean lattice wireframe
                px1, py1 = proj_grid[r_idx, c_idx]
                px2, py2 = proj_grid[r_idx - 1, c_idx]
                h_val = 0.5 * (v[r_idx, c_idx] + v[r_idx - 1, c_idx])
                h = 280.0 - h_val * 200.0
                py5.stroke(h, 80, 80, 80)
                py5.line(px1, py1, px2, py2)
                
    py5.pop_matrix()
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("TOPOGRAPHIC GRAY-SCOTT SYSTEM // 3D PROJ NEON WIREFRAME", 50, 50)
    py5.text(f"GRID RESOLUTION: {N} x {N} | DEPTH-SORTED LATTICE LINES: {N*N // 2}", 50, 85)
    py5.text(f"GS PARAMETERS: Du={Du:.2f}, Dv={Dv:.2f}, F={F:.3f}, k={k:.3f}", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"SURFACE VARIANCE INDEX: {variance:.5f}", SIZE[0] - 50, 85)
    
    # Variance Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("SPATIAL VARIANCE HISTORY", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(255, 0, 255, 180)
    py5.begin_shape()
    for idx, val in enumerate(variance_history):
        xx = gx + idx * (graph_w / 300)
        # Normalize variance range to fit graph (variance is around 0.0 to 0.08)
        yy = gy + graph_h - (val / 0.08) * (graph_h - 10) - 5
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
