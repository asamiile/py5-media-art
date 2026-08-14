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

# Viscoelastic Droplet Parameters
N = 180  # Number of boundary nodes
theta = np.linspace(0, 2 * np.pi, N, endpoint=False)
radius = 160.0

# Initial position (centered horizontally, near top)
center = np.array([SIM_W / 2, 280.0])
pos = center + np.stack([np.cos(theta), np.sin(theta)], axis=-1) * radius
prev_pos = pos.copy()

# Rest lengths for structural (neighbor) and shear (opposite) springs
rest_len_struct = 2.0 * radius * np.sin(np.pi / N)
# Shear links connect node i to i + 2
rest_len_shear = 2.0 * radius * np.sin(2.0 * np.pi / N)

# Physics parameters
gravity = 0.28
damping = 0.993
k_struct = 0.35
k_shear = 0.20
k_pressure = 480.0  # Gas volume pressure coefficient
rest_area = np.pi * (radius ** 2)

# Floor collision boundary
floor_y = SIM_H - 120.0

# Energy logs
strain_energies = []
kinetic_energies = []
img_rgb_mid = None


def get_current_area(p):
    """Computes signed area of the polygon using shoelace formula."""
    x = p[:, 0]
    y = p[:, 1]
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(5, 0, 12)


def draw():
    global pos, prev_pos, img_rgb_mid
    
    # --- 1. Physics: Verlet Integration + Spring & Pressure Forces ---
    vel = (pos - prev_pos) * damping
    prev_pos = pos.copy()
    
    # Gravity
    pos[:, 1] += gravity
    pos += vel
    
    # Accumulate forces
    forces = np.zeros_like(pos)
    
    # Structural springs (i to i+1)
    diff_next = np.roll(pos, -1, axis=0) - pos
    dist_next = np.linalg.norm(diff_next, axis=-1)[:, None]
    force_next = (diff_next / (dist_next + 1e-6)) * (dist_next - rest_len_struct) * k_struct
    forces += force_next
    forces -= np.roll(force_next, 1, axis=0)  # Equal and opposite to previous
    
    # Shear springs (i to i+2)
    diff_shear = np.roll(pos, -2, axis=0) - pos
    dist_shear = np.linalg.norm(diff_shear, axis=-1)[:, None]
    force_shear = (diff_shear / (dist_shear + 1e-6)) * (dist_shear - rest_len_shear) * k_shear
    forces += force_shear
    forces -= np.roll(force_shear, 2, axis=0)
    
    # Gas pressure force: acts outwards perpendicular to boundary, scaled by volume difference
    current_area = get_current_area(pos)
    area_ratio = rest_area / (current_area + 1e-6)
    pressure = (area_ratio - 1.0) * k_pressure
    
    # Normal vectors pointing outwards (perpendicular to segments)
    segments = np.roll(pos, -1, axis=0) - pos
    normals = np.stack([-segments[:, 1], segments[:, 0]], axis=-1)
    normals /= (np.linalg.norm(normals, axis=-1)[:, None] + 1e-6)
    
    # Apply pressure force along normals
    forces += normals * pressure
    
    # Update positions from springs/pressure
    pos += forces
    
    # Boundary Collisions (floor and walls)
    for i in range(N):
        # Floor collision
        if pos[i, 1] > floor_y:
            pos[i, 1] = floor_y
            # Friction
            pos[i, 0] = prev_pos[i, 0] + (pos[i, 0] - prev_pos[i, 0]) * 0.7
            
        # Left wall
        if pos[i, 0] < 120.0:
            pos[i, 0] = 120.0
        # Right wall
        if pos[i, 0] > SIM_W - 120.0:
            pos[i, 0] = SIM_W - 120.0
            
    # --- 2. Telemetry: Energy Calculation ---
    # Kinetic energy
    v = pos - prev_pos
    ke = 0.5 * np.sum(v ** 2)
    kinetic_energies.append(ke)
    
    # Strain energy (from structural spring deformation)
    se = 0.5 * k_struct * np.sum((dist_next - rest_len_struct) ** 2)
    strain_energies.append(se)
    
    if len(kinetic_energies) > 300:
        kinetic_energies.pop(0)
        strain_energies.pop(0)
        
    # --- 3. Rendering ---
    py5.blend_mode(py5.BLEND)
    # Slow fading trail rectangle
    py5.fill(5, 0, 12, 18)
    py5.rect(0, 0, py5.width, py5.height)
    
    # Scale coordinates to 4K
    py5.push_matrix()
    py5.scale(SIZE[0] / SIM_W, SIZE[1] / SIM_H)
    
    # Draw floor boundary line
    py5.stroke(255, 255, 255, 12)
    py5.stroke_weight(2.0)
    py5.line(80, floor_y, SIM_W - 80, floor_y)
    
    # Additive blend mode for soft droplet light
    py5.blend_mode(py5.ADD)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    
    # Render viscoelastic droplet body
    py5.no_stroke()
    # Fill body with transparent gradient depending on deformation (strain)
    # Calculate deformation ratio at each node
    dev = np.abs(dist_next.squeeze() - rest_len_struct) / rest_len_struct
    avg_dev = np.mean(dev)
    
    # Map average deformation to Hue (violet to amber/orange)
    body_hue = 280.0 - min(avg_dev * 400.0, 160.0)
    py5.fill(body_hue, 80, 90, 32)
    
    py5.begin_shape()
    for i in range(N):
        py5.vertex(pos[i, 0], pos[i, 1])
    py5.end_shape(py5.CLOSE)
    
    # Render boundary glowing line
    py5.no_fill()
    py5.stroke_weight(4.0)
    for i in range(N):
        next_i = (i + 1) % N
        # Local deformation controls color of the segment
        local_dev = np.clip(dev[i] * 3.5, 0.0, 1.0)
        h = 280.0 - local_dev * 200.0  # Violet to Aqua to Amber
        py5.stroke(h, 85, 95, 180)
        py5.line(pos[i, 0], pos[i, 1], pos[next_i, 0], pos[next_i, 1])
        
    py5.pop_matrix()
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("VISCOELASTIC DROPLET SPLAT // VERLET MASS-SPRING PHYSICS", 50, 50)
    py5.text(f"MASS NODES: {N} | STRUCT/SHEAR SPRINGS: 360", 50, 85)
    py5.text(f"DROPLET AREA: {current_area/1000.0:.1f}k px² | VOLUME DEVIATION: {(area_ratio - 1.0)*100.0:+.2f}%", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"ELASTIC STRAIN ENERGY: {se:.2f} J", SIZE[0] - 50, 85)
    
    # Energy Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("ENERGY PROFILE (KE / SE)", gx + 5, gy + 5)
    
    # Draw Kinetic Energy trail in Cyan
    py5.no_fill()
    py5.stroke(0, 240, 255, 150)
    py5.begin_shape()
    for idx, val in enumerate(kinetic_energies):
        xx = gx + idx * (graph_w / 300)
        yy = gy + graph_h - (val / 1200.0) * (graph_h - 10) - 5
        py5.vertex(xx, yy)
    py5.end_shape()
    
    # Draw Strain Energy trail in Amber
    py5.stroke(255, 150, 0, 150)
    py5.begin_shape()
    for idx, val in enumerate(strain_energies):
        xx = gx + idx * (graph_w / 300)
        yy = gy + graph_h - (val / 1200.0) * (graph_h - 10) - 5
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
