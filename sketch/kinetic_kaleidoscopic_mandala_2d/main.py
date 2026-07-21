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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
SYMMETRY = 12
NUM_AGENTS = 150
agents_r = np.zeros(NUM_AGENTS, dtype=np.float32)
agents_t = np.zeros(NUM_AGENTS, dtype=np.float32)
agents_type = np.zeros(NUM_AGENTS, dtype=np.int32)
agents_seed = np.zeros(NUM_AGENTS, dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize agents
    for i in range(NUM_AGENTS):
        agents_r[i] = py5.random(100, SIZE[1] * 0.45)
        agents_t[i] = py5.random(0, py5.TWO_PI)
        agents_type[i] = i % 3
        agents_seed[i] = py5.random(1000)
        
    py5.background(5, 5, 10)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 8)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.005
    
    angle_step = py5.TWO_PI / SYMMETRY
    
    for i in range(NUM_AGENTS):
        # Update polar coordinates with noise
        dr = py5.os_noise(agents_seed[i], time) * 4 - 2
        dt = py5.os_noise(agents_seed[i] + 100, time) * 0.04 - 0.02
        
        # Add a gentle pull towards center if they get too far, push if too close
        if agents_r[i] > SIZE[1] * 0.48:
            dr -= 1
        elif agents_r[i] < 50:
            dr += 1
            
        # Specific behaviors based on type
        atype = agents_type[i]
        
        if atype == 0:
            # Slow, large gold dots
            agents_r[i] += dr * 0.5
            agents_t[i] += dt * 0.2
            c = (255, 200, 50, 150)
            weight = 4.0
            style = py5.POINTS
        elif atype == 1:
            # Fast, tiny violet sweeping lines
            agents_r[i] += dr * 2.0
            agents_t[i] += dt * 1.5
            c = (150, 50, 255, 200)
            weight = 1.5
            style = py5.POINTS
        else:
            # Medium amber
            agents_r[i] += dr
            agents_t[i] += dt * 0.5
            c = (255, 100, 0, 120)
            weight = 2.5
            style = py5.POINTS
            
        r = agents_r[i]
        t = agents_t[i]
        
        # We use lines by keeping track of prev position, but for a kaleidoscopic trail,
        # drawing points with low background alpha creates continuous sweeping curves anyway.
        py5.stroke(*c)
        py5.stroke_weight(weight)
        
        py5.begin_shape(style)
        for s in range(SYMMETRY):
            base_angle = s * angle_step
            
            # Normal symmetry
            t1 = base_angle + t
            py5.vertex(r * np.cos(t1), r * np.sin(t1))
            
            # Mirror symmetry
            t2 = base_angle - t
            py5.vertex(r * np.cos(t2), r * np.sin(t2))
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
