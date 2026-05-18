from pathlib import Path
import shutil
import subprocess
import sys
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

class GranularSim:
    def __init__(self):
        self.N = 650 # Number of granular soft-disks
        
        # Grid boundaries in screen space (width = 800, bottom = 980)
        self.left_wall = 560.0
        self.right_wall = 1360.0
        self.container_bottom = 980.0
        
        # Particle arrays
        self.x = np.zeros(self.N, dtype=float)
        self.y = np.zeros(self.N, dtype=float)
        self.vx = np.zeros(self.N, dtype=float)
        self.vy = np.zeros(self.N, dtype=float)
        
        # Disordered polydisperse radii (prevents crystallization/regular packing)
        np.random.seed(42) # Seed only for layout initialization to keep starting pack robust
        self.R = np.random.uniform(10.0, 16.0, size=self.N)
        self.mass = (self.R ** 2) / 100.0 # Mass proportional to area
        
        # Initialize particles in a loose grid to prevent overlapping explosions at start
        cols = 22
        grid_w = 800.0 / cols
        for idx in range(self.N):
            c = idx % cols
            r = idx // cols
            self.x[idx] = self.left_wall + grid_w * (c + 0.5) + np.random.uniform(-3, 3)
            self.y[idx] = 180.0 + 26.0 * (r + 0.5) + np.random.uniform(-3, 3)
            
        # Reset seed so runtime remains fully random/non-deterministic
        np.random.seed(None)
        
        # Physical parameters
        self.k_n = 12.0          # Spring stiffness (normal contact)
        self.gamma_n = 2.0      # Damping coefficient (contact dashpot)
        self.drag = 0.08         # Fluid/air drag coefficient
        self.gravity = 0.16      # Gravity acceleration
        
        # Piston properties
        self.piston_start_y = 520.0
        self.piston_end_y = 365.0
        self.piston_y = self.piston_start_y
        
        # Contact force network matrix
        self.contact_forces = np.zeros((self.N, self.N), dtype=float)
        
    def step(self, frame_count):
        # 1. Update compressing piston position
        if frame_count < 60:
            # Let particles settle under gravity in the first second
            self.piston_y = self.piston_start_y
        else:
            # Squeeze pack steadily over the remaining 14 seconds
            t = (frame_count - 60) / (TOTAL_FRAMES - 60)
            self.piston_y = self.piston_start_y + t * (self.piston_end_y - self.piston_start_y)
            
        # 2. Integration substeps for high-rigidity numerical stability (12 substeps, smaller dt)
        substeps = 12
        dt = 0.08
        
        for _ in range(substeps):
            # Pairwise coordinates differences
            dx = self.x[:, None] - self.x[None, :]
            dy = self.y[:, None] - self.y[None, :]
            d = np.sqrt(dx**2 + dy**2)
            
            # Avoid division by zero on self-pairs
            np.fill_diagonal(d, 1.0)
            
            # Contact overlaps
            overlap = (self.R[:, None] + self.R[None, :]) - d
            
            # Contact mask (exclude self-interactions)
            contact = overlap > 0
            np.fill_diagonal(contact, False)
            
            # Normal direction unit vectors
            nx = dx / d
            ny = dy / d
            
            # Normal spring forces
            F_spring = self.k_n * overlap * contact
            
            # Normal damping forces (relative velocity projected on normal)
            vx_diff = self.vx[:, None] - self.vx[None, :]
            vy_diff = self.vy[:, None] - self.vy[None, :]
            vn = vx_diff * nx + vy_diff * ny
            F_damping = -self.gamma_n * vn * contact
            
            # Total normal contact force (must be purely repulsive)
            F_normal = np.maximum(0.0, F_spring + F_damping)
            
            # Record force network (from the final substep)
            self.contact_forces = F_normal
            
            # Vectorized sum of contact forces acting on each grain
            fx = np.sum(F_normal * nx, axis=1)
            fy = np.sum(F_normal * ny, axis=1) + self.gravity * self.mass
            
            # Floor boundary (y = container_bottom)
            floor_overlap = self.R - (self.container_bottom - self.y)
            floor_contact = floor_overlap > 0
            F_floor = np.maximum(0.0, self.k_n * floor_overlap + self.gamma_n * self.vy)
            fy -= floor_contact * F_floor
            
            # Left wall boundary (x = left_wall)
            left_overlap = self.R - (self.x - self.left_wall)
            left_contact = left_overlap > 0
            F_left = np.maximum(0.0, self.k_n * left_overlap - self.gamma_n * self.vx)
            fx += left_contact * F_left
            
            # Right wall boundary (x = right_wall)
            right_overlap = self.R - (self.right_wall - self.x)
            right_contact = right_overlap > 0
            F_right = np.maximum(0.0, self.k_n * right_overlap + self.gamma_n * self.vx)
            fx -= right_contact * F_right
            
            # Descending piston boundary (y = piston_y)
            # (Applies downward force only when piston touches a grain from above)
            piston_overlap = self.R - (self.y - self.piston_y)
            piston_contact = piston_overlap > 0
            F_piston = np.maximum(0.0, self.k_n * piston_overlap - self.gamma_n * self.vy)
            fy += piston_contact * F_piston
            
            # Apply integration
            self.vx += (fx / self.mass) * dt
            self.vy += (fy / self.mass) * dt
            
            # Air resistance / global damping drag
            self.vx *= (1.0 - self.drag * dt)
            self.vy *= (1.0 - self.drag * dt)
            
            self.x += self.vx * dt
            self.y += self.vy * dt
            
            # Soft wall clamp to prevent absolute escape under high pressures
            self.x = np.clip(self.x, self.left_wall + self.R, self.right_wall - self.R)

sim = None

def setup():
    global sim
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    sim = GranularSim()

def draw():
    global sim
    
    # Advance DEM physical simulation
    sim.step(py5.frame_count)
    
    # 1. Background Polariscope Void
    py5.background(10, 13, 20)
    
    # Subtle dark visual vignette/grid
    py5.stroke(20, 25, 35, 120)
    py5.stroke_weight(1.0)
    for grid_x in range(560, 1361, 80):
        py5.line(grid_x, 100, grid_x, 980)
    for grid_y in range(100, 981, 80):
        py5.line(560, grid_y, 1360, grid_y)
        
    # 2. Compute local compressive stress for each grain
    # Stress is the sum of all contact normal forces on a grain
    stress_vector = np.sum(sim.contact_forces, axis=1)
    
    # 3. DRAW FORCE CHAINS (Layer 2 - Behind beads for internal diffusion aesthetic)
    # Find all active contact pairs
    indices = np.argwhere(sim.contact_forces > 0.05)
    valid_pairs = indices[indices[:, 1] > indices[:, 0]]
    
    py5.stroke_cap(py5.ROUND)
    for pair in valid_pairs:
        i, j = pair[0], pair[1]
        force = sim.contact_forces[i, j]
        
        # Filament thickness proportional to normal force magnitude
        weight = min(7.5, 0.6 + force * 1.6)
        
        if force > 3.0:
            # Critical force load: Blinding Solar Gold (#FFD700)
            py5.stroke(255, 215, 0, 220)
        elif force > 1.0:
            # Medium force load: Solar Amber/Copper (#FF7800)
            py5.stroke(255, 120, 0, 160)
        else:
            # Low force load: Deep Amethyst / Royal Indigo (#8A2BE2)
            py5.stroke(138, 43, 226, 90)
            
        py5.stroke_weight(weight)
        py5.line(sim.x[i], sim.y[i], sim.x[j], sim.y[j])
        
    # 4. DRAW TRANSLUCENT PHOTOELASTIC GRAINS (Layer 3)
    for i in range(sim.N):
        stress = np.nan_to_num(stress_vector[i])
        
        # Base grain fill: dark smoky glass
        py5.fill(18, 22, 32, 220)
        
        # Border becomes glowing electric cyan and brightens under load
        border_alpha = int(np.clip(100 + stress * 35, 100, 255))
        if stress > 0.4:
            py5.stroke(0, 242, 254, border_alpha) # Electric cyan neon border
            py5.stroke_weight(1.8)
        else:
            py5.stroke(48, 56, 74, 110) # Quiet, desaturated dark gray-blue border
            py5.stroke_weight(1.2)
            
        # Draw the physical grain boundary
        py5.ellipse(sim.x[i], sim.y[i], 2 * sim.R[i], 2 * sim.R[i])
        
        # Render internal photoelastic stress fringes inside the glass bead
        if stress > 0.08:
            s_norm = min(1.0, stress / 7.5) # Scale to [0, 1] range
            py5.no_stroke()
            
            # Outer stress fringe: Deep Royal Purple
            py5.fill(138, 43, 226, int(s_norm * 125))
            py5.ellipse(sim.x[i], sim.y[i], 2 * sim.R[i] * 0.8, 2 * sim.R[i] * 0.8)
            
            # Middle stress fringe: Electric Neon Pink
            if s_norm > 0.3:
                alpha_pink = int((s_norm - 0.3) / 0.7 * 165)
                py5.fill(255, 0, 127, alpha_pink)
                py5.ellipse(sim.x[i], sim.y[i], 2 * sim.R[i] * 0.52, 2 * sim.R[i] * 0.52)
                
            # Core stress fringe: Incandescent Golden Core
            if s_norm > 0.7:
                alpha_gold = int((s_norm - 0.7) / 0.3 * 210)
                py5.fill(255, 215, 0, alpha_gold)
                py5.ellipse(sim.x[i], sim.y[i], 2 * sim.R[i] * 0.28, 2 * sim.R[i] * 0.28)
                
    # 5. DRAW CONTAINER & COMPRESSION PISTON (Layer 4)
    # Left, right walls and bottom floor (thin, neon double rules)
    py5.stroke(45, 55, 75, 180)
    py5.stroke_weight(3.0)
    py5.line(sim.left_wall, 100, sim.left_wall, sim.container_bottom)
    py5.line(sim.right_wall, 100, sim.right_wall, sim.container_bottom)
    py5.line(sim.left_wall, sim.container_bottom, sim.right_wall, sim.container_bottom)
    
    # Descending compressing piston (glassy neon look)
    py5.fill(22, 28, 38, 160)
    py5.stroke(0, 242, 254, 210) # Glowing neon cyan top edge
    py5.stroke_weight(2.5)
    py5.rect(sim.left_wall, sim.piston_y - 25, 800.0, 25.0)
    
    # Draw dark backing on top of container to hide grains pushed above the piston
    py5.fill(10, 13, 20)
    py5.no_stroke()
    py5.rect(sim.left_wall - 10, 0, 820.0, sim.piston_y - 25.0)
    
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
