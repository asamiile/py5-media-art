from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE
spacing_x = 0

def setup():
    global shapes, colors, spacing_x
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Bauhaus palette
    colors = [
        "#E63946", # Primary Red
        "#F4A261", # Orange-Yellow
        "#E9C46A", # Yellow
        "#2A9D8F", # Teal/Blue
        "#264653", # Deep Black/Blue
    ]
    
    shapes = []
    # Grid of shapes
    cols = 8
    rows = 6
    
    margin_x = SIZE[0] * 0.15
    margin_y = SIZE[1] * 0.15
    spacing_x = (SIZE[0] - 2 * margin_x) / (cols - 1)
    spacing_y = (SIZE[1] - 2 * margin_y) / (rows - 1)
    
    for i in range(cols):
        for j in range(rows):
            if random.random() > 0.8: continue # leave some gaps
            
            x = margin_x + i * spacing_x
            y = margin_y + j * spacing_y
            
            s_type = random.choice(['rect', 'circle', 'triangle', 'arc'])
            size = spacing_x * random.uniform(0.6, 1.4)
            
            shapes.append({
                'x': x,
                'y': y,
                'type': s_type,
                'size': size,
                'color_idx': random.randint(0, len(colors) - 1),
                'rot_start': random.uniform(0, py5.TWO_PI),
                'rot_target': random.choice([0, py5.PI/2, py5.PI, py5.PI*1.5, py5.TWO_PI]),
                'scale_start': random.uniform(0.5, 1.2),
                'scale_target': random.choice([0.5, 1.0, 1.5, 2.0]),
                'delay': random.uniform(0, 0.3)
            })

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def draw():
    py5.background(240, 240, 235) # Off-white parchment background
    
    # Add some grain - wait, we shouldn't do this every frame as it's slow, 
    # instead we can draw a grain overlay or just skip grain for animation efficiency.
    # We will skip grain for 60fps real-time recording to avoid huge mp4 files.
    
    t = py5.frame_count / TOTAL_FRAMES
    
    for obj in shapes:
        # Calculate local time with delay
        local_t = py5.constrain((t - obj['delay']) / (1.0 - obj['delay']), 0, 1) if obj['delay'] < 1 else 0
        
        # We want to animate from start to target, then back to start over the whole loop
        # so it loops perfectly.
        if local_t < 0.5:
            phase_t = local_t * 2
            current_rot = py5.lerp(obj['rot_start'], obj['rot_target'], ease_in_out(phase_t))
            current_scale = py5.lerp(obj['scale_start'], obj['scale_target'], ease_in_out(phase_t))
        else:
            phase_t = (local_t - 0.5) * 2
            current_rot = py5.lerp(obj['rot_target'], obj['rot_start'], ease_in_out(phase_t))
            current_scale = py5.lerp(obj['scale_target'], obj['scale_start'], ease_in_out(phase_t))
            
        with py5.push_matrix():
            py5.translate(obj['x'], obj['y'])
            py5.rotate(current_rot)
            py5.scale(current_scale)
            
            c = obj['color_idx']
            if c < len(colors):
                py5.fill(colors[c])
            py5.no_stroke()
            
            s = obj['size']
            if obj['type'] == 'rect':
                py5.rect_mode(py5.CENTER)
                py5.rect(0, 0, s, s)
            elif obj['type'] == 'circle':
                py5.ellipse(0, 0, s, s)
            elif obj['type'] == 'triangle':
                py5.triangle(0, -s/2, -s/2, s/2, s/2, s/2)
            elif obj['type'] == 'arc':
                py5.arc(0, 0, s, s, 0, py5.PI)
                
            # Add a contrasting dot in the center occasionally
            if obj['size'] > spacing_x * 0.8:
                py5.fill(20) # Almost black
                py5.ellipse(0, 0, s*0.1, s*0.1)

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
        import os
        os._exit(0)

py5.run_sketch()
