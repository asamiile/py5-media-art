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

class VortexSim:
    def __init__(self):
        self.N = 400 # Number of quantum vortices
        self.M = 80  # Number of fixed magnetic pinning centers
        
        # Superconductor boundaries
        self.x_min, self.x_max = 260.0, 1660.0
        self.y_min, self.y_max = 140.0, 940.0
        self.width = self.x_max - self.x_min
        self.height = self.y_max - self.y_min
        
        # Pinning center coordinates (randomly dispersed)
        np.random.seed(137) # Keep pinning centers identical for consistent crystal structure
        self.px = np.random.uniform(self.x_min + 50.0, self.x_max - 50.0, size=self.M)
        self.py = np.random.uniform(self.y_min + 50.0, self.y_max - 50.0, size=self.M)
        
        # Initialize vortices in a beautiful hexagonal Abrikosov grid
        spacing = 58.0
        v_list = []
        for r in range(16):
            for c in range(26):
                shift = (spacing / 2.0) if (r % 2 == 1) else 0.0
                vx = self.x_min + c * spacing + shift + np.random.uniform(-1, 1)
                vy = self.y_min + 30.0 + r * spacing * 0.866 + np.random.uniform(-1, 1)
                
                # Check bounds
                if self.x_min + 20.0 <= vx <= self.x_max - 20.0 and self.y_min + 20.0 <= vy <= self.y_max - 20.0:
                    v_list.append([vx, vy])
                    
        # Select the first N vortices
        v_list = v_list[:self.N]
        # Pad with random ones if list is too short
        while len(v_list) < self.N:
            v_list.append([np.random.uniform(self.x_min + 50.0, self.x_max - 50.0),
                           np.random.uniform(self.y_min + 50.0, self.y_max - 50.0)])
                           
        v_arr = np.array(v_list)
        self.x = v_arr[:, 0]
        self.y = v_arr[:, 1]
        
        # Velocities for color mapping
        self.vx = np.zeros(self.N, dtype=float)
        self.vy = np.zeros(self.N, dtype=float)
        
        # Reset seed so runtime is organic
        np.random.seed(None)
        
        # Physical parameters
        self.f0 = 2400.0          # Pairwise screened Yukawa repulsion strength
        self.lambda_p = 55.0      # London penetration depth
        self.f_pin = 750.0        # Pinning well attractive force strength
        self.r_pin = 28.0         # Pinning well radius
        self.k_boundary = 6.0     # Elastic top/bottom wall stiffness
        self.F_thermal = 2.5      # Thermal noise amplitude
        
        # AC Driving force parameters (3 cycles over 900 frames)
        self.F_drive_amp = 95.0
        self.omega = 2.0 * np.pi / 300.0
        
    def step(self, frame_count):
        # 1. Integration substeps for high numerical stability (5 substeps)
        substeps = 5
        dt = 0.04
        
        # Current AC Lorentz drive force
        drive_x = self.F_drive_amp * np.sin(self.omega * frame_count)
        
        for _ in range(substeps):
            # Pairwise coordinates differences
            dx = self.x[:, None] - self.x[None, :]
            dy = self.y[:, None] - self.y[None, :]
            
            # Horizontally periodic boundary mapping for pairwise forces
            dx = dx - self.width * np.round(dx / self.width)
            
            d = np.sqrt(dx**2 + dy**2)
            np.fill_diagonal(d, 1.0) # Avoid self-pair division by zero
            
            # Screened Yukawa pairwise repulsion force: F = f0 * exp(-d / lambda) / d
            F_rep = self.f0 * np.exp(-d / self.lambda_p) / (d + 1e-2)
            np.fill_diagonal(F_rep, 0.0) # No self-repulsion
            
            # Sum repulsive forces on each vortex
            fx = np.sum(F_rep * dx, axis=1)
            fy = np.sum(F_rep * dy, axis=1)
            
            # Pinning center forces (Gaussian potential wells)
            dx_pin = self.x[:, None] - self.px[None, :]
            # Horizontal horizontal periodic mapping for pinning
            dx_pin = dx_pin - self.width * np.round(dx_pin / self.width)
            
            dy_pin = self.y[:, None] - self.py[None, :]
            d_pin = np.sqrt(dx_pin**2 + dy_pin**2)
            
            # Attractive force F_pin = -f_pin * d * exp(-d^2 / r_pin^2)
            F_pin_mat = -self.f_pin * np.exp(-d_pin**2 / self.r_pin**2)
            
            fx += np.sum(F_pin_mat * dx_pin, axis=1)
            fy += np.sum(F_pin_mat * dy_pin, axis=1)
            
            # Top/bottom elastic boundaries
            # Top boundary (y_min)
            top_overlap = (self.y_min + 30.0) - self.y
            top_contact = top_overlap > 0
            fy += top_contact * self.k_boundary * top_overlap
            
            # Bottom boundary (y_max)
            bottom_overlap = self.y - (self.y_max - 30.0)
            bottom_contact = bottom_overlap > 0
            fy -= bottom_contact * self.k_boundary * bottom_overlap
            
            # Applied AC Lorentz drive force & Thermal noise (overdamped Langevin dynamics)
            thermal_x = np.random.normal(0, self.F_thermal, size=self.N)
            thermal_y = np.random.normal(0, self.F_thermal, size=self.N)
            
            total_fx = fx + drive_x + thermal_x
            total_fy = fy + thermal_y
            
            # In overdamped dynamics, velocity is proportional to force
            self.vx = total_fx
            self.vy = total_fy
            
            # Update positions
            self.x += self.vx * dt
            self.y += self.vy * dt
            
            # Horizontal periodic boundary wrap
            self.x = (self.x - self.x_min) % self.width + self.x_min
            
            # Clamp vertical coordinates in case of extreme thermal kicks
            self.y = np.clip(self.y, self.y_min + 15.0, self.y_max - 15.0)

sim = None

def setup():
    global sim
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    sim = VortexSim()
    py5.background(8, 10, 16) # Initialize background with deep quantum blue-black

def draw():
    global sim
    
    # 1. Accumulate trails (draw translucent overlay instead of background call)
    py5.no_stroke()
    py5.fill(8, 10, 16, 26) # 10% opacity for long, silken, glowing trails
    py5.rect(0, 0, py5.width, py5.height)
    
    # Advance simulation
    sim.step(py5.frame_count)
    
    # 2. DRAW PINNING WELLS (Subtle glowing rings)
    py5.stroke_weight(1.5)
    py5.no_fill()
    for m in range(sim.M):
        # Draw pinning centers with a pulsing alpha based on global AC drive
        pulse = 45 + 25 * np.sin(sim.omega * py5.frame_count)
        py5.stroke(138, 43, 226, int(pulse)) # Deep violet magnetic wells
        py5.ellipse(sim.px[m], sim.py[m], 32.0, 32.0)
        
        # Center core indicator
        py5.stroke(0, 195, 255, int(pulse * 0.6))
        py5.ellipse(sim.px[m], sim.py[m], 6.0, 6.0)
        
    # 3. DRAW SUPERCONDUCTING THIN FILM BOUNDARIES (High-tech neon guides)
    py5.stroke(40, 50, 75, 120)
    py5.stroke_weight(2.0)
    py5.line(sim.x_min, sim.y_min, sim.x_max, sim.y_min)
    py5.line(sim.x_min, sim.y_max, sim.x_max, sim.y_max)
    
    # Double lines for structural frame
    py5.stroke(0, 195, 255, 60)
    py5.line(sim.x_min, sim.y_min - 4, sim.x_max, sim.y_min - 4)
    py5.line(sim.x_min, sim.y_max + 4, sim.x_max, sim.y_max + 4)
    
    # 4. DRAW QUANTUM VORTICES (Velocity-mapped color)
    speed = np.sqrt(sim.vx**2 + sim.vy**2)
    
    for i in range(sim.N):
        v_speed = speed[i]
        
        # Speed classification mapping:
        if v_speed < 8.0:
            # Locked state (Stable triangular lattice): Deep Cyan/Cobalt
            py5.stroke(0, 195, 255, 210)
            weight = 4.0
        elif v_speed < 24.0:
            # Shearing state (Plastic unpinning region): Hot Purple/Magenta
            py5.stroke(230, 0, 180, 230)
            weight = 5.0
        else:
            # High-velocity flow state (Vortex River channels): Glowing Solar Gold
            py5.stroke(255, 230, 100, 255)
            weight = 6.0
            
        py5.stroke_weight(weight)
        
        # Horizontal periodic boundary split drawing to prevent trail glitches at wraps
        px = sim.x[i]
        py_val = sim.y[i]
        
        # Draw vortex center core
        py5.point(px, py_val)
        
        # Draw horizontal wraps helper to keep wrap borders visually seamless
        if px < sim.x_min + 30.0:
            py5.point(px + sim.width, py_val)
        elif px > sim.x_max - 30.0:
            py5.point(px - sim.width, py_val)
            
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
