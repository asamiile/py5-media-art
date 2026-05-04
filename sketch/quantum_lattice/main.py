from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Palette
VACUUM_INDIGO = np.array([8, 5, 15], dtype=np.uint8)
POSITRON_PINK = np.array([255, 50, 150], dtype=np.uint8)
ELECTRON_BLUE = np.array([50, 150, 255], dtype=np.uint8)
QUANTUM_GOLD = np.array([255, 215, 0], dtype=np.uint8)

# Wave sources
np.random.seed(42)
sources = []
for _ in range(6):
    sources.append({
        "pos": np.random.uniform(0, 1, 2),
        "freq": np.random.uniform(2, 5),
        "phase": np.random.uniform(0, np.pi * 2),
        "type": np.random.choice(["positron", "electron"])
    })

def setup():
    py5.size(*SIZE)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(int(VACUUM_INDIGO[0]), int(VACUUM_INDIGO[1]), int(VACUUM_INDIGO[2]))

def draw():
    t = py5.frame_count * 0.05
    
    # Calculate at logical SIZE to save time, then upscale for Retina
    rows, cols = SIZE[1], SIZE[0]
    
    x = np.linspace(0, 1, cols)
    y = np.linspace(0, 1, rows)
    xv, yv = np.meshgrid(x, y)
    
    field_positron = np.zeros((rows, cols), dtype=complex)
    field_electron = np.zeros((rows, cols), dtype=complex)
    
    for s in sources:
        dist = np.sqrt((xv - s["pos"][0])**2 + (yv - s["pos"][1])**2)
        wave = np.exp(1j * (s["freq"] * 20 * dist - t + s["phase"]))
        if s["type"] == "positron":
            field_positron += wave
        else:
            field_electron += wave
            
    int_p = np.abs(field_positron)**2
    int_e = np.abs(field_electron)**2
    
    steps = 8
    int_p = np.floor(int_p * steps) / steps
    int_e = np.floor(int_e * steps) / steps
    
    # Render logic
    img = np.zeros((rows, cols, 4), dtype=np.uint8)
    img[:, :, :3] = VACUUM_INDIGO
    img[:, :, 3] = 255
    
    mask_gold = (int_p > 1.5) & (int_e > 1.5)
    mask_p = (int_p > int_e) & (int_p > 0.5) & ~mask_gold
    mask_e = (int_e >= int_p) & (int_e > 0.5) & ~mask_gold
    
    def blend(base, overlay, alpha_factor):
        f = np.minimum(1.0, alpha_factor / 4.0)[:, None]
        return (overlay * f + base * (1.0 - f)).astype(np.uint8)

    if np.any(mask_p):
        img[mask_p, :3] = blend(VACUUM_INDIGO, POSITRON_PINK, int_p[mask_p])
    if np.any(mask_e):
        img[mask_e, :3] = blend(VACUUM_INDIGO, ELECTRON_BLUE, int_e[mask_e])
    img[mask_gold, :3] = QUANTUM_GOLD
    
    # Upscale for Retina if needed
    py5.load_np_pixels()
    retina_h, retina_w = py5.np_pixels.shape[:2]
    
    if retina_h != rows or retina_w != cols:
        # Calculate scale
        sy = retina_h // rows
        sx = retina_w // cols
        # Repeat pixels for blocky/sharp quantization look
        img_retina = np.repeat(np.repeat(img, sy, axis=0), sx, axis=1)
        # Ensure exact match if division wasn't perfect
        py5.np_pixels[:] = img_retina[:retina_h, :retina_w]
    else:
        py5.np_pixels[:] = img
        
    py5.update_np_pixels()

    # Save frames and handle exit
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
