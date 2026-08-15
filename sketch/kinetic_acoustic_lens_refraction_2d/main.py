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

# FDTD Wave Grid dimensions (small grid for speed, upscaled to 4K)
GRID_W = 160
GRID_H = 90

# Wave grids (current, previous, next)
p = np.zeros((GRID_H, GRID_W), dtype=np.float32)
p_prev = np.zeros((GRID_H, GRID_W), dtype=np.float32)

# Damping factor
damping = 0.985

# Telemetry: Wave RMS amplitude
rms_history = []
img_rgb_mid = None


def get_sound_speed_grid(t):
    """
    Computes a spatially varying sound speed grid c(x, y).
    Simulates a thermal ocean front or acoustic lens.
    """
    y_indices, x_indices = np.indices((GRID_H, GRID_W), dtype=np.float32)
    
    # Base sound speed
    c = np.ones((GRID_H, GRID_W), dtype=np.float32) * 0.45
    
    # Dynamic lens: a circular zone of lower sound speed (c = 0.15) that moves slowly
    # This acts like a refractive lens focusing waves
    lens_x = GRID_W * (0.6 + 0.15 * np.cos(t * 0.4))
    lens_y = GRID_H * (0.5 + 0.20 * np.sin(t * 0.4))
    
    dist_sq = (x_indices - lens_x)**2 + (y_indices - lens_y)**2
    # Circular lens boundary
    lens_mask = dist_sq < 25.0**2
    # Smooth transition
    c[lens_mask] = 0.45 - 0.30 * np.exp(-dist_sq[lens_mask] / (2.0 * 25.0**2))
    
    # Second diagonal thermal front
    front_val = x_indices * 0.4 + y_indices * 0.6 + np.sin(t * 0.5) * 15.0
    front_mask = front_val > 65.0
    c[front_mask] = np.clip(c[front_mask] + 0.15 * np.sin(front_val[front_mask] * 0.1), 0.1, 0.6)
    
    return c


def update_wave_equation(c_grid):
    """
    Updates the 2D Wave Equation using FDTD scheme:
    p_next = 2*p - p_prev + c^2 * \nabla^2 p
    """
    global p, p_prev
    
    # 5-point discrete Laplacian operator
    laplacian = (
        np.roll(p, 1, axis=0) +
        np.roll(p, -1, axis=0) +
        np.roll(p, 1, axis=1) +
        np.roll(p, -1, axis=1) -
        4.0 * p
    )
    
    # FDTD update step
    c_sq = c_grid ** 2
    p_next = 2.0 * p - p_prev + c_sq * laplacian
    
    # Apply viscous damping
    p_next *= damping
    
    # Update histories
    p_prev = p.copy()
    p = p_next
    
    # Boundary reflection damping (absorbing sponge boundaries)
    p[0, :] *= 0.85
    p[-1, :] *= 0.85
    p[:, 0] *= 0.85
    p[:, -1] *= 0.85


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 4, 15)


def draw():
    global p, img_rgb_mid
    
    t = py5.frame_count / 60.0
    
    # --- 1. Wave Physics & Source Injection ---
    c_grid = get_sound_speed_grid(t)
    
    # Continuous wave source injection: a point source at left-center oscillating sinusoidally
    src_x, src_y = int(GRID_W * 0.2), int(GRID_H * 0.5)
    # Sine wave source
    src_freq = 0.55
    p[src_y, src_x] = 12.0 * np.sin(t * src_freq * 2.0 * np.pi)
    
    # Perform multiple FDTD updates per frame for wave propagation speed
    for _ in range(4):
        update_wave_equation(c_grid)
        
    # Calculate telemetry: Root-Mean-Square (RMS) amplitude
    rms = np.sqrt(np.mean(p ** 2))
    rms_history.append(rms)
    if len(rms_history) > 300:
        rms_history.pop(0)
        
    # --- 2. Rendering ---
    py5.blend_mode(py5.BLEND)
    
    # Convert wave height field p to an image representation
    # Normal mapping and caustics shading
    # Computes spatial gradients dp/dx, dp/dy
    dy, dx = np.gradient(p)
    
    # Specular liquid caustics calculation
    # Reflected light intensity depends on curvature / gradient
    light_dir = np.array([1.0, 1.0, 1.5])  # Light vector pointing down-right-back
    light_dir /= np.linalg.norm(light_dir)
    
    # Normal vector grid
    normals = np.zeros((GRID_H, GRID_W, 3), dtype=np.float32)
    normals[:, :, 0] = -dx * 1.5  # Gradient x
    normals[:, :, 1] = -dy * 1.5  # Gradient y
    normals[:, :, 2] = 1.0
    # Normalize normals
    n_mag = np.sqrt(np.sum(normals**2, axis=-1))
    normals /= n_mag[:, :, None]
    
    # Lambertian diffuse reflection + Blinn-Phong specular highlight
    diffuse = np.sum(normals * light_dir[None, None, :], axis=-1)
    diffuse = np.clip(diffuse, 0.0, 1.0)
    
    # Specular caustics focusing
    specular = diffuse ** 18.0
    
    # Construct RGB image using HSB phase mapping
    # Wave value maps to Hues (Cyan to Ocean Navy)
    img_wave = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
    
    # Base HSB map: Hue (Cyan to Indigo to Amber accent)
    for y in range(GRID_H):
        for x in range(GRID_W):
            val = p[y, x]
            spec = specular[y, x]
            
            # Map wave amplitude to Hue
            # Positive waves are cyan-teal, negative waves are indigo-navy, caustics are amber-gold
            if spec > 0.45:
                # Golden caustics highlight
                h = 35.0
                s = 85.0
                b = 95.0
            else:
                h = 190.0 + np.clip(val * 15.0, -40.0, 40.0)
                s = 80.0
                b = np.clip(50.0 + np.abs(val) * 15.0, 20.0, 90.0)
                
            # Convert HSB to RGB via OpenCV
            hsb_pixel = np.array([[[h / 2.0, s * 2.55, b * 2.55]]], dtype=np.uint8)
            rgb_pixel = cv2.cvtColor(hsb_pixel, cv2.COLOR_HSV2RGB)
            img_wave[y, x] = rgb_pixel[0, 0]
            
    # Upscale the low-res wave image to 4K resolution using bilinear filtering
    img_wave_4k = cv2.resize(img_wave, SIZE, interpolation=cv2.INTER_LINEAR)
    
    # Paint grid to canvas
    py5.load_np_pixels()
    py5.np_pixels[:, :, :3] = img_wave_4k
    py5.update_np_pixels()
    
    # --- 3. Telemetry HUD ---
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("ACOUSTIC CAUSTIC SHIFT // FDTD HETERONORM WAVE equation", 50, 50)
    py5.text(f"WAVE RESOLUTION: {GRID_W} x {GRID_H} | PROPAGATION STEPS: 4/frame", 50, 85)
    py5.text(f"SOURCE FREQ: {src_freq:.2f} Hz | REFRACTIVE ZONE: circular acoustic lens", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"ACOUSTIC FIELD RMS AMPLITUDE: {rms:.4f} Pa", SIZE[0] - 50, 85)
    
    # RMS Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("ACOUSTIC RMS AMPLITUDE HIST", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(0, 240, 255, 180)
    py5.begin_shape()
    for idx, val in enumerate(rms_history):
        xx = gx + idx * (graph_w / 300)
        # Scale to fit graph box
        yy = gy + graph_h - (val / 1.5) * (graph_h - 10) - 5
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
