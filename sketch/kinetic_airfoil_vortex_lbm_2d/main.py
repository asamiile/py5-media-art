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

# LBM D2Q9 Grid dimensions (kept reasonable for NumPy speed)
NX = 160
NY = 80

# D2Q9 parameters
v_directions = np.array([
    [0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]
], dtype=np.int32)
weights = np.array([4/9, 1/9, 1/9, 1/9, 1/9, 1/36, 1/36, 1/36, 1/36], dtype=np.float32)

# Relaxation parameter (controls viscosity)
omega = 1.70

# Initial distribution function f
f = np.zeros((NY, NX, 9), dtype=np.float32)
# Set initial uniform flow to the right
u0 = 0.08
for i in range(9):
    # Equilibrium distribution for rest state + velocity u0
    vu = v_directions[i, 0] * u0
    f[:, :, i] = weights[i] * (1.0 + 3.0 * vu + 4.5 * vu**2 - 1.5 * u0**2)

# Solid boundary definition: NACA 0012 Airfoil
barrier = np.zeros((NY, NX), dtype=np.bool_)
# Center the airfoil
cx, cy = NX // 3, NY // 2
chord = 42.0  # Length of airfoil
thickness = 0.12  # NACA 0012 has 12% max thickness

# Generate NACA 0012 profile mask
for x in range(NX):
    dx = x - cx
    if 0 <= dx <= chord:
        xc = dx / chord
        # NACA 0012 thickness formula
        yt = 5.0 * thickness * (0.2969 * np.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4) * chord
        y_top = cy - yt
        y_bot = cy + yt
        for y in range(NY):
            if y_top <= y <= y_bot:
                barrier[y, x] = True

# Lift coefficient telemetry
lift_history = []
img_rgb_mid = None


def lbm_step():
    """
    Executes one step of the Lattice Boltzmann Method (D2Q9 model):
    1. Streaming step (propagation)
    2. Boundary bounce-back (solid airfoil)
    3. Collision step (BGK relaxation)
    """
    global f
    
    # 1. Streaming (Propagation)
    for i in range(9):
        f[:, :, i] = np.roll(f[:, :, i], v_directions[i, 1], axis=0)
        f[:, :, i] = np.roll(f[:, :, i], v_directions[i, 0], axis=1)
        
    # 2. Boundary Bounce-Back (No-slip on airfoil)
    # Opposite direction mappings
    opposite = [0, 3, 4, 1, 2, 7, 8, 5, 6]
    f_bounce = f.copy()
    for i in range(9):
        f[barrier, i] = f_bounce[barrier, opposite[i]]
        
    # 3. Macro quantities calculation
    rho = np.sum(f, axis=2)
    # Momentum density
    ux = np.sum(f * v_directions[:, 0], axis=2) / (rho + 1e-6)
    uy = np.sum(f * v_directions[:, 1], axis=2) / (rho + 1e-6)
    
    # Clip velocity to prevent LBM check explosions
    np.clip(ux, -0.2, 0.2, out=ux)
    np.clip(uy, -0.2, 0.2, out=uy)
    
    # Force inflow boundary conditions (left side velocity)
    ux[:, 0] = u0
    uy[:, 0] = 0.0
    rho[:, 0] = 1.0
    # Outflow boundary (extrapolation on right side)
    ux[:, -1] = ux[:, -2]
    uy[:, -1] = uy[:, -2]
    rho[:, -1] = rho[:, -2]
    
    # Recompute distribution functions at boundaries
    for i in range(9):
        vu = v_directions[i, 0] * ux + v_directions[i, 1] * uy
        u_sq = ux**2 + uy**2
        feq = weights[i] * rho * (1.0 + 3.0 * vu + 4.5 * vu**2 - 1.5 * u_sq)
        
        # Left boundary inflow
        f[:, 0, i] = feq[:, 0]
        # Right boundary outflow
        f[:, -1, i] = feq[:, -1]
        
    # 4. Collision step (BGK relaxation towards equilibrium)
    for i in range(9):
        vu = v_directions[i, 0] * ux + v_directions[i, 1] * uy
        u_sq = ux**2 + uy**2
        feq = weights[i] * rho * (1.0 + 3.0 * vu + 4.5 * vu**2 - 1.5 * u_sq)
        
        # Relax towards equilibrium: f_new = f - omega * (f - feq)
        f[:, :, i] = f[:, :, i] - omega * (f[:, :, i] - feq)
        
    # Set internal airfoil distributions to zero velocity
    f[barrier, :] = 0.0
    
    # Calculate force/lift coefficient: momentum exchange on airfoil
    # F_y is sum over boundary cells of delta momentum
    lift = 0.0
    for i in range(9):
        lift += np.sum(f_bounce[barrier, i] * v_directions[i, 1] - f[barrier, i] * v_directions[opposite[i], 1])
        
    return ux, uy, lift


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    
    if FRAMES_DIR.exists():
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(2, 2, 4)


def draw():
    global img_rgb_mid
    
    # --- 1. Physics update ---
    # Run multiple steps per frame to get high-frequency vortex shedding
    lift = 0.0
    for _ in range(3):
        ux, uy, l_step = lbm_step()
        lift += l_step
        
    lift_history.append(lift)
    if len(lift_history) > 300:
        lift_history.pop(0)
        
    t = py5.frame_count / 60.0
    
    # --- 2. Vorticity Calculation ---
    # curl of velocity field: w = du_y/dx - du_x/dy
    duy_dx, _ = np.gradient(uy)
    _, dux_dy = np.gradient(ux)
    vorticity = duy_dx - dux_dy
    
    # Clean up airfoil zone
    vorticity[barrier] = 0.0
    
    # --- 3. Rendering ---
    py5.blend_mode(py5.BLEND)
    
    # Map vorticity to colors
    # Clockwise vortices (negative): coral, counter-clockwise (positive): teal
    img_fluid = np.zeros((NY, NX, 3), dtype=np.uint8)
    
    for y in range(NY):
        for x in range(NX):
            if barrier[y, x]:
                # Draw dark wing shape
                img_fluid[y, x] = [10, 10, 20]
            else:
                w_val = vorticity[y, x]
                # Scale vorticity for color representation
                w_scaled = np.clip(w_val * 60.0, -1.0, 1.0)
                
                # HSB color wheel mapping
                if w_scaled > 0.05:
                    # Counter-clockwise: Teal (Hue ~170)
                    h = 170.0
                    s = 90.0
                    b = 40.0 + w_scaled * 50.0
                elif w_scaled < -0.05:
                    # Clockwise: Coral/Pink (Hue ~330)
                    h = 330.0
                    s = 90.0
                    b = 40.0 + np.abs(w_scaled) * 50.0
                else:
                    # Flat laminer flow: Dark blue background
                    h = 240.0
                    s = 70.0
                    b = 10.0 + np.abs(ux[y, x]) * 80.0
                    
                hsb_pixel = np.array([[[h / 2.0, s * 2.55, b * 2.55]]], dtype=np.uint8)
                rgb_pixel = cv2.cvtColor(hsb_pixel, cv2.COLOR_HSV2RGB)
                img_fluid[y, x] = rgb_pixel[0, 0]
                
    # Upscale LBM image to 4K resolution using bilinear filtering
    img_fluid_4k = cv2.resize(img_fluid, SIZE, interpolation=cv2.INTER_LINEAR)
    
    # Paint grid to canvas
    py5.load_np_pixels()
    py5.np_pixels[:, :, :3] = img_fluid_4k
    py5.update_np_pixels()
    
    # Additive neon wing border highlights
    py5.blend_mode(py5.ADD)
    # Draw airfoil coordinates scaled to 4K screen
    scale_x = py5.width / NX
    scale_y = py5.height / NY
    
    py5.stroke(255, 255, 255, 12)
    py5.stroke_weight(2.5)
    py5.no_fill()
    py5.begin_shape()
    # Draw outline of airfoil
    for x in range(NX):
        dx = x - cx
        if 0 <= dx <= chord:
            xc = dx / chord
            yt = 5.0 * thickness * (0.2969 * np.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4) * chord
            py5.vertex(x * scale_x, (cy - yt) * scale_y)
    for x in range(NX - 1, -1, -1):
        dx = x - cx
        if 0 <= dx <= chord:
            xc = dx / chord
            yt = 5.0 * thickness * (0.2969 * np.sqrt(xc) - 0.1260 * xc - 0.3516 * xc**2 + 0.2843 * xc**3 - 0.1015 * xc**4) * chord
            py5.vertex(x * scale_x, (cy + yt) * scale_y)
    py5.end_shape(py5.CLOSE)
    
    # Switch back to normal blend mode for technical HUD overlays
    py5.blend_mode(py5.BLEND)
    py5.color_mode(py5.RGB, 255, 255, 255)
    
    # Render HUD text
    py5.fill(255, 255, 255, 180)
    py5.text_size(24)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("AERODYNAMIC LBM WIND TUNNEL // D2Q9 VORTEX SHEDDING", 50, 50)
    py5.text(f"FLUID SOLVER: GRID {NX} x {NY} | BOUNDARY: NACA 0012 AIRFOIL", 50, 85)
    py5.text(f"RELAXATION (OMEGA): {omega:.2f} | INFLOW VELOCITY (U0): {u0:.3f}", 50, 120)
    
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text(f"FRAME: {py5.frame_count:04d} / {TOTAL_FRAMES}", SIZE[0] - 50, 50)
    py5.text(f"AIRFOIL NET LIFT COEFFICIENT: {lift:.4f} N", SIZE[0] - 50, 85)
    
    # Lift Graph
    py5.stroke(255, 255, 255, 80)
    py5.stroke_weight(1.5)
    py5.no_fill()
    graph_w, graph_h = 240, 80
    gx, gy = SIZE[0] - 290, 140
    py5.rect(gx, gy, graph_w, graph_h)
    
    py5.fill(255, 255, 255, 120)
    py5.text_size(14)
    py5.text("AIRFOIL NET LIFT HISTORY", gx + 5, gy + 5)
    
    py5.no_fill()
    py5.stroke(255, 112, 166, 180)
    py5.begin_shape()
    for idx, val in enumerate(lift_history):
        xx = gx + idx * (graph_w / 300)
        # Normalize lift range to fit graph (lift is around -10.0 to 10.0)
        yy = gy + graph_h - ((val + 10.0) / 20.0) * (graph_h - 15) - 5
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
