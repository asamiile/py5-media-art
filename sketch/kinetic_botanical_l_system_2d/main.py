from pathlib import Path
import random
import shutil
import subprocess
import sys
import math
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
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# L-System Parameters
AXIOM = "X"
RULES = {
    "X": "F-[[X]+X]+F[+FX]-X",
    "F": "FF"
}
GENERATIONS = 5
BASE_ANGLE = 23.5
BASE_STEP = 5.2

# Global L-System sentence
sentence = ""
max_depth = 1

def expand_l_system():
    global sentence, max_depth
    print("[L-System] Expanding production rules...")
    current = AXIOM
    for _ in range(GENERATIONS):
        current = "".join(RULES.get(symbol, symbol) for symbol in current)
    sentence = current
    
    # Pre-calculate max branch depth for normalized coloring
    depth = 0
    max_d = 0
    for symbol in sentence:
        if symbol == "[":
            depth += 1
            max_d = max(max_d, depth)
        elif symbol == "]":
            depth = max(0, depth - 1)
    max_depth = max(max_d, 1)
    print(f"[L-System] Expanded length: {len(sentence)} symbols, Max Depth: {max_depth}")

def setup():
    py5.size(*SIZE)
    py5.smooth(8)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    expand_l_system()

def draw():
    fc = py5.frame_count
    
    # Deep amethyst background with a soft ambient glow
    py5.background(280, 80, 7, 100)
    py5.blend_mode(py5.ADD)
    
    # Move origin to bottom center
    py5.translate(py5.width / 2.0, py5.height - 120.0)
    
    # Global plant growth over time
    # 0 - 660 frames (11s): Progressive growth
    # 660 - 900 frames (4s): Full size sway and slow wither/fade
    if fc < 660:
        grow_ratio = py5.remap(fc, 0, 660, 0.0, 1.0)
    else:
        grow_ratio = 1.0
        
    draw_limit = int(len(sentence) * grow_ratio)
    
    # Wind dynamics: continuous wind sway using 2D Perlin noise
    wind_intensity = py5.noise(fc * 0.012) * 5.5
    
    # Render plant
    branch_depth = 0
    matrix_depth = 0
    pushed_at_depth = []
    
    # Pre-seed random generator with a fixed seed every frame to keep random structural variations stable
    # but still allow dynamic sway
    random.seed(42)
    
    # Simple stack for tracking depth during rendering
    for i in range(draw_limit):
        symbol = sentence[i]
        depth_ratio = branch_depth / max_depth
        
        # Calculate dynamic step length and segment width
        step = BASE_STEP * (1.0 - depth_ratio * 0.35)
        weight = max(0.8, 6.0 * (1.0 - depth_ratio) + 0.5)
        
        # Compute dynamic wind offset at this branch depth
        # Alternates direction based on depth and uses time to sway
        wind_offset = py5.sin(fc * 0.024 + branch_depth * 0.35) * wind_intensity
        
        if symbol == "F":
            # Draw stem: shifting from dark forest emerald to neon mint
            stem_hue = py5.lerp(120, 165, depth_ratio)
            stem_sat = py5.lerp(85, 45, depth_ratio)
            stem_bri = py5.lerp(35, 80, depth_ratio)
            
            py5.stroke(stem_hue, stem_sat, stem_bri, 65)
            py5.stroke_weight(weight)
            py5.line(0, 0, 0, -step)
            py5.translate(0, -step)
            
        elif symbol == "+":
            # Rotate right + wind offset
            py5.rotate(py5.radians(BASE_ANGLE + wind_offset + random.uniform(-2, 2)))
            
        elif symbol == "-":
            # Rotate left + wind offset
            py5.rotate(py5.radians(-BASE_ANGLE + wind_offset + random.uniform(-2, 2)))
            
        elif symbol == "[":
            if matrix_depth < 30:
                py5.push_matrix()
                matrix_depth += 1
                branch_depth += 1
                pushed_at_depth.append(True)
            else:
                pushed_at_depth.append(False)
                branch_depth += 1
            
        elif symbol == "]":
            if pushed_at_depth:
                was_pushed = pushed_at_depth.pop()
                if was_pushed:
                    py5.pop_matrix()
                    matrix_depth -= 1
            branch_depth = max(0, branch_depth - 1)
            
        elif symbol == "X":
            # Terminal symbol: draw bioluminescent flowers at tips
            if depth_ratio > 0.65:
                py5.push_matrix()
                py5.no_stroke()
                
                # Petal color shifts from deep magenta to glowing gold
                flower_hue = py5.lerp(320, 360, math.sin(fc * 0.03 + branch_depth) * 0.5 + 0.5)
                py5.fill(flower_hue, 75, 95, 80)
                
                # Dynamic flower scale based on depth and growth phase
                flower_size = step * 1.8 * py5.remap(grow_ratio, 0, 1, 0.2, 1.0)
                
                # Draw simple 5-petal flower structure
                for _ in range(5):
                    py5.rotate(py5.TWO_PI / 5)
                    py5.ellipse(0, -flower_size * 0.4, flower_size * 0.35, flower_size)
                    
                # Center pistil
                py5.fill(48, 80, 95, 95)
                py5.circle(0, 0, flower_size * 0.35)
                py5.pop_matrix()

    # Pop any remaining matrices that were left pushed at the end of the loop due to truncation
    while matrix_depth > 0:
        py5.pop_matrix()
        matrix_depth -= 1

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame is at frame 450)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
