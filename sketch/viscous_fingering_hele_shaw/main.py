from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.ndimage import binary_dilation, gaussian_filter

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

class HeleShawSim:
    def __init__(self):
        # Downscaled grid dimensions for high-performance physics solver
        self.gw = 480
        self.gh = 270
        
        # Phase field (1.0 = invading fluid, 0.0 = viscous fluid)
        self.phi = np.zeros((self.gh, self.gw), dtype=float)
        
        # Initialize a small circular seed of invading fluid in the center
        cx, cy = self.gw // 2, self.gh // 2
        y_indices, x_indices = np.ogrid[:self.gh, :self.gw]
        dist = np.sqrt((x_indices - cx)**2 + (y_indices - cy)**2)
        self.phi[dist <= 4.0] = 1.0
        
        # Pressure field p (0.0 on cluster, 1.0 at outer boundary)
        self.p = np.ones((self.gh, self.gw), dtype=float)
        
        # Simulation parameters
        self.eta = 2.0           # DBM exponent: controls branching/dendrite sharpness
        self.noise_factor = 0.5   # Organic fluctuation strength
        self.target_growth = 20.0 # Normalized cluster cells added per frame for steady speed
        
        # Pre-cache smoothed noise fields to eliminate Gaussian filter overhead in the draw loop
        print("[Sim Setup] Pre-generating organic noise fields...")
        self.noise_cache = []
        for _ in range(60):
            raw = np.random.normal(0, 1, size=(self.gh, self.gw))
            smooth = gaussian_filter(raw, sigma=1.5)
            smooth /= (np.std(smooth) + 1e-6)
            self.noise_cache.append(smooth)
            
        # Particles visualizing the displaced viscous fluid flow
        self.num_particles = 80000
        self.px = np.random.rand(self.num_particles) * self.gw
        self.py = np.random.rand(self.num_particles) * self.gh
        self.p_age = np.random.rand(self.num_particles) * 60.0 # Staggered initial fade-in
        self.particle_speed = 4.5
        
        # Color definitions for linear interpolation (floats)
        self.C_bg = np.array([6, 9, 19], dtype=float)         # Obsidian midnight
        self.C_fog = np.array([58, 0, 120], dtype=float)       # Royal indigo viscous fog
        self.C_invading = np.array([0, 242, 254], dtype=float) # Electric cyan invading fluid
        self.C_glow = np.array([255, 159, 0], dtype=float)     # Incandescent gold tip glow

    def step(self, frame_count):
        # 1. Update mask of the cluster
        mask = self.phi >= 0.5
        
        # 2. Warm start pressure field and enforce boundary conditions
        self.p[mask] = 0.0
        self.p[0, :] = 1.0
        self.p[-1, :] = 1.0
        self.p[:, 0] = 1.0
        self.p[:, -1] = 1.0
        
        # 3. Jacobi relaxation to solve Laplace's equation in empty space (30 iterations)
        for _ in range(30):
            self.p[1:-1, 1:-1] = 0.25 * (
                self.p[2:, 1:-1] + self.p[:-2, 1:-1] + 
                self.p[1:-1, 2:] + self.p[1:-1, :-2]
            )
            self.p[mask] = 0.0
            
        # 4. Compute growth at cluster boundaries
        dilated = binary_dilation(mask)
        boundary = dilated & ~mask
        
        if np.any(boundary):
            smooth_noise = self.noise_cache[frame_count % len(self.noise_cache)]
            p_clamped = np.clip(self.p, 0.0, 1.0)
            
            # Growth rate is proportional to local pressure (gradient proxy) raised to eta
            raw_growth = (p_clamped ** self.eta) * (1.0 + self.noise_factor * smooth_noise)
            raw_growth = np.clip(raw_growth, 0.0, None)
            
            growth = np.zeros_like(self.phi)
            growth[boundary] = raw_growth[boundary]
            
            # Normalize growth to ensure constant, elegant expansion speed
            total_growth = np.sum(growth)
            if total_growth > 0:
                self.phi += (growth / total_growth) * self.target_growth
                self.phi = np.clip(self.phi, 0.0, 1.0)
                
        # 5. Advect viscous fluid tracer particles along pressure gradient (flow field)
        # u_x = dp/dx, u_y = dp/dy (pointing away from cluster boundary towards outer boundaries)
        grad_y, grad_x = np.gradient(self.p)
        
        # No extra smoothing needed as the pressure field relaxation is naturally highly diffused and smooth

        
        # Update particles using vectorized indexing
        ix = np.clip(self.px, 0, self.gw - 1).astype(int)
        iy = np.clip(self.py, 0, self.gh - 1).astype(int)
        
        vx = grad_x[iy, ix]
        vy = grad_y[iy, ix]
        
        # Apply motion
        self.px += vx * self.particle_speed
        self.py += vy * self.particle_speed
        self.p_age += 1.0
        
        # Handle out of bounds or engulfed particles
        out_of_bounds = (self.px < 0) | (self.px >= self.gw) | (self.py < 0) | (self.py >= self.gh)
        engulfed = self.phi[np.clip(self.py, 0, self.gh - 1).astype(int), np.clip(self.px, 0, self.gw - 1).astype(int)] >= 0.5
        to_respawn = out_of_bounds | engulfed
        
        if np.any(to_respawn):
            empty_y, empty_x = np.where(self.phi < 0.5)
            if len(empty_y) > 0:
                indices = np.random.choice(len(empty_y), size=np.sum(to_respawn))
                self.px[to_respawn] = empty_x[indices] + np.random.rand(len(indices))
                self.py[to_respawn] = empty_y[indices] + np.random.rand(len(indices))
                self.p_age[to_respawn] = 0.0 # Reset age for smooth fade-in

    def render_background(self):
        # Synthesize beautiful, multi-layered color mapping
        # 1. Viscous fog layer (deep royal indigo)
        w_fog = (1.0 - self.phi) * self.p
        bg_col = (1.0 - w_fog)[:, :, None] * self.C_bg + w_fog[:, :, None] * self.C_fog
        
        # 2. Invading fluid layer (electric cyan)
        blend = (1.0 - self.phi)[:, :, None] * bg_col + self.phi[:, :, None] * self.C_invading
        
        # 3. Active tips glow layer (incandescent gold/copper)
        interface = 4.0 * self.phi * (1.0 - self.phi)
        w_glow = interface * (self.p ** 1.5)
        w_glow = np.clip(w_glow, 0.0, 1.0)
        
        final_color = (1.0 - w_glow)[:, :, None] * blend + w_glow[:, :, None] * self.C_glow
        return np.clip(final_color, 0, 255).astype(np.uint8)

sim = None

def setup():
    global sim
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(6, 9, 19)
    sim = HeleShawSim()

def draw():
    global sim
    
    # Advance the physics simulation
    sim.step(py5.frame_count)
    
    # Synthesize background fluid image
    bg_rgb = sim.render_background()
    
    # Direct pixel transfer using create_image and fast ARGB packing
    img = py5.create_image(sim.gw, sim.gh, py5.ARGB)
    img.load_np_pixels()
    img.np_pixels[:, :, 0] = 255 # Alpha channel
    img.np_pixels[:, :, 1] = bg_rgb[:, :, 0] # Red
    img.np_pixels[:, :, 2] = bg_rgb[:, :, 1] # Green
    img.np_pixels[:, :, 3] = bg_rgb[:, :, 2] # Blue
    img.update_np_pixels()
    
    # Draw upscaled background image using hardware-accelerated bilinear filtering
    py5.image(img, 0, 0, py5.width, py5.height)
    
    # Map particle coordinates from simulation scale to screen scale
    screen_x = sim.px * (py5.width / sim.gw)
    screen_y = sim.py * (py5.height / sim.gh)
    coords = np.stack([screen_x, screen_y], axis=-1)
    
    # Compute velocity magnitude to color particles by flow speed
    # (Using the gradient values at particle positions)
    ix = np.clip(sim.px, 0, sim.gw - 1).astype(int)
    iy = np.clip(sim.py, 0, sim.gh - 1).astype(int)
    grad_y, grad_x = np.gradient(sim.p)
    vx = grad_x[iy, ix]
    vy = grad_y[iy, ix]
    v_mag = np.sqrt(vx**2 + vy**2)
    
    # Quantize particles into three distinct speed bins for highly detailed styling
    high_mask = v_mag > 0.12
    mid_mask = (v_mag <= 0.12) & (v_mag > 0.03)
    low_mask = v_mag <= 0.03
    
    # Calculate smooth alpha fades based on age to prevent sudden pop-ins
    alphas = np.clip(sim.p_age * 6.0, 0.0, 160.0).astype(int)
    
    # Draw points in 3 fast OpenGL batches
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    # 1. Low speed: Deep royal purple
    if np.any(low_mask):
        py5.stroke(110, 50, 200, 50) # Very low alpha
        py5.stroke_weight(1.0)
        py5.points(coords[low_mask])
        
    # 2. Mid speed: Bright electric magenta
    if np.any(mid_mask):
        py5.stroke(255, 0, 127, 95) # Mid alpha
        py5.stroke_weight(1.5)
        py5.points(coords[mid_mask])
        
    # 3. High speed (near growing tips): Blinding incandescent gold
    if np.any(high_mask):
        py5.stroke(255, 215, 0, 160) # High alpha
        py5.stroke_weight(2.2)
        py5.points(coords[high_mask])
        
    # Save the frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4 using FFmpeg
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot from the middle of the animation
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        print(f"[Render Preview] Created preview image at {SKETCH_DIR / PREVIEW_FILENAME}")
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

py5.run_sketch()
