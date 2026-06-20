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

# Grid size
COLS = 40
ROWS = 40
SPACING = 30

class Protein:
    def __init__(self, c, r):
        self.c = c
        self.r = r
        self.w = py5.random(40, 80)
        self.h = py5.random(80, 150)
        self.hue = py5.random(0, 40) # Red/Orange proteins

proteins = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Add a few transmembrane proteins
    for _ in range(15):
        c = int(py5.random(COLS))
        r = int(py5.random(ROWS))
        proteins.append(Protein(c, r))

def draw_lipid(y_offset, is_top, noise_val):
    # Lipid head
    py5.push_matrix()
    py5.translate(0, y_offset, 0)
    py5.no_stroke()
    if is_top:
        py5.fill(200, 80, 100) # Blue-ish top layer
    else:
        py5.fill(160, 80, 100) # Green-ish bottom layer
    py5.sphere_detail(5)
    py5.sphere(8)
    
    # Lipid tails (two lines)
    py5.stroke(200 if is_top else 160, 40, 80, 60)
    py5.stroke_weight(2)
    tail_len = 25
    dir_y = 1 if is_top else -1
    
    # wiggle tails based on noise
    wiggle_x = (noise_val - 0.5) * 20
    wiggle_z = py5.sin(noise_val * py5.TWO_PI) * 10
    
    py5.line(-3, 0, 0, -3 + wiggle_x, tail_len * dir_y, wiggle_z)
    py5.line(3, 0, 0, 3 - wiggle_x, tail_len * dir_y, -wiggle_z)
    py5.pop_matrix()

def draw():
    py5.background(240, 100, 10) # Deep ocean/cellular blue
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.translate(py5.width/2, py5.height/2, -300)
    
    # Slowly rotate camera
    py5.rotate_x(py5.PI/3)
    py5.rotate_z(t * py5.TWO_PI)
    
    # Center grid
    offset_x = -COLS * SPACING / 2
    offset_z = -ROWS * SPACING / 2
    
    # Use directional light to give form to the spheres
    py5.lights()
    py5.directional_light(0, 0, 100, 0, 1, -1)
    
    for r in range(ROWS):
        for c in range(COLS):
            x = offset_x + c * SPACING
            z = offset_z + r * SPACING
            
            # Continuous loop noise
            angle = t * py5.TWO_PI
            nx = py5.cos(angle) * 0.5 + c * 0.1
            ny = py5.sin(angle) * 0.5 + r * 0.1
            
            n_val = py5.os_noise(nx, ny, t * 2)
            
            # Undulating Y position
            y = (n_val - 0.5) * 150
            
            py5.push_matrix()
            py5.translate(x, y, z)
            
            # Check if there's a protein here
            protein_here = None
            for p in proteins:
                if p.c == c and p.r == r:
                    protein_here = p
                    break
                    
            if protein_here:
                py5.no_stroke()
                py5.fill(protein_here.hue, 80, 90)
                py5.box(protein_here.w, protein_here.h, protein_here.w)
            else:
                # Draw top lipid
                draw_lipid(-20, True, n_val)
                # Draw bottom lipid
                draw_lipid(20, False, n_val)
                
            py5.pop_matrix()

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
