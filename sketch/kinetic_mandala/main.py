from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()


def setup():
    py5.size(*SIZE)
    py5.background(16, 16, 16)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_element(w, h, t, col):
    py5.stroke(*col)
    py5.no_fill()
    py5.stroke_weight(0.8) # Slightly thicker
    
    # Draw a complex "geometric petal"
    py5.begin_shape()
    for i in range(12): # More vertices
        angle = py5.TWO_PI * i / 12
        # More complex oscillation
        r_mod = 1 + 0.3 * np.sin(t * 3 + i * 0.5)
        x = np.cos(angle) * w * r_mod
        y = np.sin(angle) * h * r_mod
        py5.vertex(x, y)
    py5.end_shape(py5.CLOSE)
    
    # More internal lines for moiré
    for i in range(8):
        py5.line(-w, -h + i * 15, w, h - i * 15)


def draw():
    # Trailing background for smoothness
    py5.no_stroke()
    py5.fill(12, 12, 12, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2)
    py5.blend_mode(py5.ADD)
    
    num_rings = 7
    num_arms = 16 # More arms
    
    for r in range(num_rings):
        py5.push_matrix()
        # Counter-rotating rings
        rot_dir = 1 if r % 2 == 0 else -1
        py5.rotate(t * (0.4 + r * 0.15) * rot_dir)
        
        # Pulsing scale
        s = 0.7 + 0.5 * np.sin(t * 0.3 + r * 0.4)
        py5.scale(s)
        
        for a in range(num_arms):
            py5.push_matrix()
            py5.rotate(py5.TWO_PI * a / num_arms)
            
            radius = 80 + r * 70
            py5.translate(radius, 0)
            
            # Spin individual elements
            py5.rotate(t * 2.0 + r * 0.5)
            
            # Higher alpha for visibility
            alpha = 30 + 10 * np.sin(t + r)
            if r % 2 == 0:
                col = (255, 204, 51, alpha) # Stellar Gold
            else:
                col = (255, 136, 0, alpha)  # Amber Glow
                
            draw_element(30 + r * 12, 60 + r * 18, t, col)
            
            py5.pop_matrix()
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

    # Video recording
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error encoding video: {e}")


if __name__ == "__main__":
    py5.run_sketch()
