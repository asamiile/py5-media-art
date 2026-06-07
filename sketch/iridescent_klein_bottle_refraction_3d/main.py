from pathlib import Path
import shutil
import subprocess
import sys
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(0)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Orbiting camera/rotation
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.sin(py5.frame_count * 0.005) * 0.5)
    
    py5.blend_mode(py5.ADD)
    
    # Lighting to enhance iridescent look
    py5.ambient_light(200, 50, 20)
    py5.directional_light(180, 80, 100, 1, 1, -1)
    py5.directional_light(300, 80, 100, -1, -1, 1)
    py5.specular(0, 0, 100)
    py5.shininess(100)
    
    py5.no_stroke()
    
    # Draw a parametric figure-8 Klein bottle or distorted Torus
    # We will use a dense grid of points/quads
    steps_u = 50
    steps_v = 50
    scale_factor = 200
    
    py5.begin_shape(py5.QUADS)
    for i in range(steps_u):
        for j in range(steps_v):
            # We map i and j to u and v
            # To draw quads, we need (i, j), (i+1, j), (i+1, j+1), (i, j+1)
            def get_vertex(u_idx, v_idx):
                u = (u_idx / steps_u) * py5.TWO_PI
                v = (v_idx / steps_v) * py5.TWO_PI
                
                # Figure-8 Klein bottle equations
                r = 2 + py5.cos(v / 2) * py5.sin(u) - py5.sin(v / 2) * py5.sin(2 * u)
                x = r * py5.cos(v) * scale_factor
                y = r * py5.sin(v) * scale_factor
                z = (py5.sin(v / 2) * py5.sin(u) + py5.cos(v / 2) * py5.sin(2 * u)) * scale_factor
                
                # Add organic breathing/distortion
                nx = py5.os_noise(x * 0.005, y * 0.005, py5.frame_count * 0.01) * 50
                ny = py5.os_noise(y * 0.005, z * 0.005, py5.frame_count * 0.01 + 100) * 50
                nz = py5.os_noise(z * 0.005, x * 0.005, py5.frame_count * 0.01 + 200) * 50
                
                return x + nx, y + ny, z + nz, u, v
            
            x1, y1, z1, u1, v1 = get_vertex(i, j)
            x2, y2, z2, u2, v2 = get_vertex(i + 1, j)
            x3, y3, z3, u3, v3 = get_vertex(i + 1, j + 1)
            x4, y4, z4, u4, v4 = get_vertex(i, j + 1)
            
            # Iridescent coloring based on normals/position
            hue = (py5.frame_count * 0.5 + i * 2 + j * 2) % 360
            py5.fill(hue, 70, 100, 40)
            
            py5.vertex(x1, y1, z1)
            py5.vertex(x2, y2, z2)
            py5.vertex(x3, y3, z3)
            py5.vertex(x4, y4, z4)
            
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

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
