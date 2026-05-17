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
DURATION_SEC = 15  # 15 seconds is perfect for developing complex chaotic orbits
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
N = 256  # Wave grid size
NUM_WALKERS = 8
WAVE_MEMORY = 180  # Keep recent bounces (in frames) to maintain path-memory
WAVE_DECAY = 0.025  # Faraday wave damping factor
WAVE_FREQ = 0.15  # Standing wave temporal frequency
WAVE_K = 0.25  # Wavenumber of ripples
WAVE_SIGMA = 24.0  # Spatial decay width of ripples
KICK_COEFF = 45.0  # Pilot-wave deflection force
DRAG = 0.02  # Medium resistance
dt = 1.0

# Grid for Wave Field
x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# Allocate Wave Image
wave_img_data = np.zeros((N, N, 3), dtype=np.uint8)

# Walker class to manage state in continuous space
class Walker:
    def __init__(self, idx, px, py):
        self.idx = idx
        self.px = px
        self.py = py
        self.vx = np.random.uniform(-1.0, 1.0)
        self.vy = np.random.uniform(-1.0, 1.0)
        
        # Bouncing phase and frequency
        self.phase = np.random.uniform(0, 2.0 * np.pi)
        self.bounce_freq = 0.12 + idx * 0.005  # Slightly out of phase
        
        # Trajectory History
        self.history = []
        self.max_history = 400
        
    def update(self, frame, H_grad_x, H_grad_y):
        # 1. Update Bounce Height (z)
        # Bounces are represented by the absolute sine of the phase
        z_height = np.abs(np.sin(frame * self.bounce_freq + self.phase))
        is_impacting = (z_height < 0.15)
        
        # 2. Pilot-Wave Slope Coupling (At landing/impact)
        if is_impacting:
            # Map screen position to grid coordinates
            gx = int((self.px / py5.width) * N) % N
            gy = int((self.py / py5.height) * N) % N
            
            # Read local gradients of the wave field
            slope_x = H_grad_x[gy, gx]
            slope_y = H_grad_y[gy, gx]
            
            # Kick velocity down the slope
            self.vx -= KICK_COEFF * slope_x
            self.vy -= KICK_COEFF * slope_y
            
            # Add small fluctuations to drive chaos
            self.vx += np.random.normal(0, 0.05)
            self.vy += np.random.normal(0, 0.05)
            
            # Deposit bounce event
            bounce_events.append({
                "x": self.px,
                "y": self.py,
                "frame": frame,
                "amp": 1.2
            })
            
        # 3. Apply drag
        self.vx *= (1.0 - DRAG)
        self.vy *= (1.0 - DRAG)
        
        # Keep velocities bounded
        v_mag = np.sqrt(self.vx**2 + self.vy**2)
        if v_mag > 4.5:
            self.vx = (self.vx / v_mag) * 4.5
            self.vy = (self.vy / v_mag) * 4.5
            
        # 4. Move Walker
        self.px += self.vx * dt
        self.py += self.vy * dt
        
        # 5. Boundary Collisions (Elastic reflection off container meniscus)
        margin = 40
        if self.px < margin:
            self.px = margin
            self.vx *= -1
        elif self.px > py5.width - margin:
            self.px = py5.width - margin
            self.vx *= -1
            
        if self.py < margin:
            self.py = margin
            self.vy *= -1
        elif self.py > py5.height - margin:
            self.py = py5.height - margin
            self.vy *= -1
            
        # 6. Record history
        self.history.append((self.px, self.py))
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        return z_height


# Global State
walkers = []
bounce_events = []
py5_img = None


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Walkers distributed on a circle
    cx, cy = py5.width / 2.0, py5.height / 2.0
    r_ring = 350.0
    for i in range(NUM_WALKERS):
        ang = (i / NUM_WALKERS) * 2.0 * np.pi
        px = cx + r_ring * np.cos(ang)
        py = cy + r_ring * np.sin(ang)
        walkers.append(Walker(i, px, py))
        
    # Allocate a py5 image to hold our low-resolution shaded fluid bath
    global py5_img
    py5_img = py5.create_image(N, N, py5.RGB)
    
    py5.background(11, 12, 16)


def draw():
    global bounce_events, wave_img_data
    frame = py5.frame_count
    
    # 1. Clean up old bounce events to avoid infinite memory accumulation
    bounce_events = [b for b in bounce_events if (frame - b["frame"]) < WAVE_MEMORY]
    
    # 2. Compute Wave Field H(x, y) as the superposition of decaying Faraday wave ripples
    H = np.zeros((N, N))
    
    for b in bounce_events:
        t_age = frame - b["frame"]
        
        # Grid positions of the bounce source
        bx_grid = (b["x"] / py5.width) * N
        by_grid = (b["y"] / py5.height) * N
        
        # Distance squared from source
        r2 = (X - bx_grid)**2 + (Y - by_grid)**2
        r = np.sqrt(r2)
        
        # Faraday Standing Wave Profile: Bessel-like damped circular wave
        # Amp = InitialAmp * temporal_decay * standing_wave_oscillation * spatial_decay
        amp = b["amp"] * np.exp(-WAVE_DECAY * t_age) * np.cos(WAVE_FREQ * t_age)
        ripple = amp * np.cos(WAVE_K * r) * np.exp(-r2 / (2.0 * WAVE_SIGMA**2))
        
        H += ripple
        
    # 3. Compute Wave Field Gradients
    # Use central differences with edge replication
    H_grad_y, H_grad_x = np.gradient(H)
    
    # 4. Fluid Caustics Specular Shading
    # Compute normal field from gradients and perform lighting reflections
    slope = np.sqrt(H_grad_x**2 + H_grad_y**2)
    
    # Colors (Midnight Navy Base, Electric Cyan, Deep Indigo)
    r_base, g_base, b_base = 11, 12, 16
    r_wave, g_wave, b_wave = 0, 245, 220
    r_peak, g_peak, b_peak = 75, 0, 230
    
    # Blend base with wave peaks based on height H
    H_norm = np.clip(H * 6.0, -1, 1)
    peak_mask = np.abs(H_norm)
    
    r = r_base * (1.0 - peak_mask) + np.where(H_norm > 0, r_peak, 20) * peak_mask
    g = g_base * (1.0 - peak_mask) + np.where(H_norm > 0, g_peak, 10) * peak_mask
    b = b_base * (1.0 - peak_mask) + np.where(H_norm > 0, b_peak, 100) * peak_mask
    
    # Blend with slope for glowing turquoise caustics on wavefronts
    slope_norm = np.clip(slope * 18.0, 0, 1)
    r = r * (1.0 - slope_norm) + r_wave * slope_norm
    g = g * (1.0 - slope_norm) + g_wave * slope_norm
    b = b * (1.0 - slope_norm) + b_wave * slope_norm
    
    # Specular Highlight (Light source from top-left)
    specular = np.clip((H_grad_x + H_grad_y) * 12.0, 0, 1)**6 * 200.0
    r = np.clip(r + specular, 0, 255)
    g = np.clip(g + specular, 0, 255)
    b = np.clip(b + specular, 0, 255)
    
    # Write to image buffer
    wave_img_data[:, :, 0] = r.astype(np.uint8)
    wave_img_data[:, :, 1] = g.astype(np.uint8)
    wave_img_data[:, :, 2] = b.astype(np.uint8)
    
    # Copy numpy array to py5 image pixels using packed ARGB integers
    py5_img.load_pixels()
    r_int = r.astype(np.uint32)
    g_int = g.astype(np.uint32)
    b_int = b.astype(np.uint32)
    packed = (0xff000000) | (r_int << 16) | (g_int << 8) | b_int
    py5_img.pixels[:] = packed.astype(np.int32).ravel()
    py5_img.update_pixels()
    
    # 5. Draw Fluid Surface (Bilinearly upscaled low-resolution shaded grid)
    py5.image(py5_img, 0, 0, py5.width, py5.height)
    
    # 6. Update and Draw Walker Agents
    z_heights = []
    for w in walkers:
        z = w.update(frame, H_grad_x, H_grad_y)
        z_heights.append(z)
        
    # 7. Draw Trajectory History Trails (Amber path-memory trails)
    py5.blend_mode(py5.ADD)
    for w in walkers:
        if len(w.history) < 2:
            continue
        
        # Draw path as a connected series of fading glowing lines
        num_segments = len(w.history) - 1
        for j in range(num_segments):
            p0 = w.history[j]
            p1 = w.history[j + 1]
            
            # Fade trails as they get older
            alpha_trail = int((j / num_segments)**2 * 110)
            
            py5.stroke(204, 163, 0, alpha_trail)
            py5.stroke_weight(1.5)
            py5.line(p0[0], p0[1], p1[0], p1[1])
            
    # 8. Draw Walkers (Glowing pearls bouncing in and out of phase)
    py5.stroke_weight(1.0)
    for idx, w in enumerate(walkers):
        z = z_heights[idx]
        
        # Scale droplet size based on bouncing height to simulate 3D altitude!
        # Smaller when high in the air, larger and glowing on impact
        size = 12.0 + (1.0 - z) * 8.0
        
        # Outer golden halo (glow)
        glow_alpha = int((1.0 - z) * 160 + 40)
        py5.fill(255, 215, 0, glow_alpha)
        py5.no_stroke()
        py5.ellipse(w.px, w.py, size * 1.6, size * 1.6)
        
        # Inner white pearl core
        py5.fill(255, 255, 255, 240)
        py5.ellipse(w.px, w.py, size, size)
        
        # Draw a tiny reflection speck on the droplet for premium metallic feel
        py5.fill(255, 255, 255, 255)
        py5.ellipse(w.px - size * 0.25, w.py - size * 0.25, size * 0.3, size * 0.3)
        
    py5.blend_mode(py5.BLEND)
    
    # 9. Progress & Recording
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if frame % 60 == 0:
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({frame/TOTAL_FRAMES*100:.1f}%)")
        
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save standard preview snapshot (mid-frame)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        print(f"[Render Preview] Saved preview to {SKETCH_DIR}/{PREVIEW_FILENAME}")
        
        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")


py5.run_sketch()
