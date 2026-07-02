from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# L-System rules for a bonsai-like tree
# axiom: X
# X -> F-[[X]+X]+F[+FX]-X
# F -> FF
# with some stochastic variation

axiom = "X"
rules = {
    "X": "F-[[X]+X]+F[+FX]-X",
    "F": "FF"
}

tree_string = axiom
for _ in range(6):
    next_string = ""
    for char in tree_string:
        if char in rules:
            next_string += rules[char]
        else:
            next_string += char
    tree_string = next_string

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(40, 10, 90) # Soft paper background
    
    py5.translate(SIZE[0]/2, SIZE[1] - 100)
    
    length = py5.remap(py5.frame_count, 0, TOTAL_FRAMES, 5, 6) # Slow growth
    base_angle = 25 * py5.PI / 180
    
    # Wind effect
    wind_t = py5.frame_count * 0.02
    
    py5.stroke(25, 60, 30) # Dark brown trunk
    py5.stroke_weight(10)
    
    stack = []
    
    # Pre-calculate leaf colors for stability or just use index
    idx = 0
    
    # To make it fast, we might not want to draw the *whole* string every frame if it's too long
    # But 6 iterations of this rule is ~3000 chars, very fast in py5.
    
    py5.push_matrix()
    
    depth = 0
    for char in tree_string:
        if char == "F":
            # the higher we go, the thinner the stroke
            py5.line(0, 0, 0, -length)
            py5.translate(0, -length)
            idx += 1
        elif char == "+":
            # Add wind
            wind = py5.os_noise(idx * 0.1, wind_t) * 0.1 - 0.05
            py5.rotate(base_angle + wind)
        elif char == "-":
            wind = py5.os_noise(idx * 0.1 + 100, wind_t) * 0.1 - 0.05
            py5.rotate(-base_angle + wind)
        elif char == "[":
            py5.push()
            depth += 1
            py5.stroke_weight(max(1, 10 - depth * 1.5))
        elif char == "]":
            py5.pop()
            depth -= 1
        elif char == "X":
            # Draw leaf
            py5.no_stroke()
            leaf_hue = (330 + py5.os_noise(idx*0.2, 0.0) * 40) % 360
            py5.fill(leaf_hue, 60, 90, 200) # Cherry blossom pink
            
            # Flutter leaf
            flutter = py5.sin(wind_t * 5 + idx) * 0.2
            py5.push_matrix()
            py5.rotate(flutter)
            py5.ellipse(0, 0, 15, 8)
            py5.pop_matrix()
            
            # restore stroke for branches
            py5.stroke(25, 60, 30)
            
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
