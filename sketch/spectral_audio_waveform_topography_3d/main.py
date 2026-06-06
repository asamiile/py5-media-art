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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height * 0.6, 200)
    py5.rotate_x(py5.PI / 2.5)
    
    cols = 60
    rows = 60
    scl = 30
    w = cols * scl
    h = rows * scl
    
    py5.translate(-w / 2, -h / 2, 0)
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    flying = t * 2
    
    # "Audio" bands mock
    # We create a pseudo-frequency spectrum for the 60 columns
    spectrum = []
    for x in range(cols):
        # A mix of high frequency and low frequency noise to mock an audio FFT
        val = py5.os_noise(x * 0.2, t * 1.5) * 0.6 + py5.os_noise(x * 0.05, t * 0.5) * 0.4
        # Add some rhythmic beats
        beat = pow(py5.sin(t * 3 + x * 0.1), 4) * 0.5
        spectrum.append((val + beat) * 200)
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # Calculate heights based on history (y position) + the current spectrum
            # The closer to y=0 (front), the closer to the current spectrum
            
            y_off1 = y - flying
            y_off2 = y + 1 - flying
            
            # Dampen the spectrum as it goes back (history fading)
            damp1 = py5.remap(y, 0, rows, 1, 0)
            damp2 = py5.remap(y + 1, 0, rows, 1, 0)
            
            z1 = py5.os_noise(x * 0.1, y_off1 * 0.1) * 100 + spectrum[x] * damp1
            z2 = py5.os_noise(x * 0.1, y_off2 * 0.1) * 100 + spectrum[x] * damp2
            
            hue = (280 + z1 * 0.2 - y * 2) % 360
            py5.stroke(hue, 90, 100, 100 * damp1 + 20)
            
            py5.vertex(x * scl, y * scl, z1)
            py5.vertex(x * scl, (y + 1) * scl, z2)
        py5.end_shape()

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2. Aborting.")
            import os
            os._exit(1)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
