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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class AminoAcid:
    def __init__(self, pos, hue, index):
        self.pos = pos
        self.target_pos = np.copy(pos)
        self.hue = hue
        self.index = index
        self.size = py5.random(8, 15)
        self.connected_to = None
        
    def update(self, new_pos):
        # Move smoothly towards target position
        self.pos += (new_pos - self.pos) * 0.1

class Ribosome:
    def __init__(self):
        self.pos = np.array([-400.0, 0.0, 0.0])
        self.amino_acids = []
        self.chain_length = 0
        
    def add_amino_acid(self, t):
        # Every few frames add an amino acid
        # Ejection port of ribosome is slightly offset
        eject_pos = self.pos + np.array([0.0, 40.0, 0.0])
        hue = (t * 360 * 2 + py5.random(-20, 20)) % 360
        aa = AminoAcid(eject_pos, hue, self.chain_length)
        
        if self.chain_length > 0:
            aa.connected_to = self.amino_acids[-1]
            
        self.amino_acids.append(aa)
        self.chain_length += 1
        
    def update_chain(self, t):
        # Simulate folding using a noisy random walk for the chain
        # The chain "folds" as it gets further from the ribosome
        
        for i, aa in enumerate(self.amino_acids):
            if i == 0:
                continue
                
            prev = aa.connected_to
            
            # Target distance between acids
            rest_length = 20.0
            
            # Use noise to determine the folding angle
            # The older the acid (closer to index 0), the more "folded" it becomes
            age = self.chain_length - i
            
            nx = py5.os_noise(i * 0.1, t * 2) * 2 - 1
            ny = py5.os_noise(i * 0.1, t * 2 + 100) * 2 - 1
            nz = py5.os_noise(i * 0.1, t * 2 + 200) * 2 - 1
            
            fold_dir = np.array([nx, ny, nz])
            fold_dir = fold_dir / (np.linalg.norm(fold_dir) + 0.001)
            
            # The newest acids just push straight out
            push_dir = np.array([0.0, 1.0, 0.0])
            
            # Blend between pushing out and folding based on age
            blend = min(1.0, age / 20.0)
            
            final_dir = push_dir * (1 - blend) + fold_dir * blend
            final_dir = final_dir / (np.linalg.norm(final_dir) + 0.001)
            
            aa.target_pos = prev.target_pos + final_dir * rest_length
            aa.update(aa.target_pos)
            
        # Ensure the newest one is always attached to the ribosome
        if self.chain_length > 0:
            newest = self.amino_acids[-1]
            newest.target_pos = self.pos + np.array([0.0, 40.0, 0.0])
            newest.update(newest.target_pos)

ribosome = Ribosome()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()

def draw():
    py5.background(10, 80, 10) # Dark reddish inner cell
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.translate(py5.width/2, py5.height/2, -200)
    
    # Rotate camera around the process
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.2)
    py5.rotate_y(t * py5.TWO_PI)
    
    py5.lights()
    py5.directional_light(0, 0, 100, -1, 1, -1)
    
    # Update ribosome position (moves along X axis simulating reading mRNA)
    # Loop it back to start smoothly
    x_pos = py5.remap(t, 0, 1, -300, 300)
    ribosome.pos = np.array([x_pos, 0.0, 0.0])
    
    # Add new amino acids periodically
    if py5.frame_count % 3 == 0 and len(ribosome.amino_acids) < 150:
        ribosome.add_amino_acid(t)
        
    ribosome.update_chain(t)
    
    # Draw mRNA strand (a glowing line or tube)
    py5.stroke(200, 80, 100, 80)
    py5.stroke_weight(4)
    py5.line(-400, 0, 0, 400, 0, 0)
    
    # Draw Ribosome (Large and Small Subunits)
    py5.push_matrix()
    py5.translate(*ribosome.pos)
    py5.no_stroke()
    py5.fill(150, 60, 80) # Pale green/blue ribosome
    
    # Small subunit
    py5.push_matrix()
    py5.translate(0, -15, 0)
    py5.scale(1.5, 0.8, 1.2)
    py5.sphere_detail(15)
    py5.sphere(20)
    py5.pop_matrix()
    
    # Large subunit
    py5.push_matrix()
    py5.translate(0, 20, 0)
    py5.scale(1.2, 1.5, 1.2)
    py5.sphere(30)
    py5.pop_matrix()
    
    py5.pop_matrix()
    
    # Draw Polypeptide Chain
    for i, aa in enumerate(ribosome.amino_acids):
        py5.push_matrix()
        py5.translate(*aa.pos)
        py5.fill(aa.hue, 80, 100)
        py5.sphere_detail(8)
        py5.sphere(aa.size)
        py5.pop_matrix()
        
        # Draw peptide bonds
        if aa.connected_to:
            py5.stroke(0, 0, 100, 50)
            py5.stroke_weight(3)
            py5.line(aa.pos[0], aa.pos[1], aa.pos[2], 
                     aa.connected_to.pos[0], aa.connected_to.pos[1], aa.connected_to.pos[2])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
            
        import os
        os._exit(0)

py5.run_sketch()
