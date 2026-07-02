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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle system params
NUM_PARTICLES = 150000
positions = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
velocities = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
lifetimes = np.zeros(NUM_PARTICLES, dtype=np.float32)
colors = np.zeros(NUM_PARTICLES, dtype=np.float32) # Hue

def spawn_particles(mask, t):
    num_to_spawn = np.sum(mask)
    if num_to_spawn == 0:
        return
        
    # Reset lifetimes
    lifetimes[mask] = np.random.uniform(1.0, 3.0, num_to_spawn)
    
    # Spawn at center
    positions[mask, 0] = SIZE[0] / 2
    positions[mask, 1] = SIZE[1] / 2
    
    # Complex radial emission pattern
    # Determine base angle
    angles = np.random.uniform(0, 2 * np.pi, num_to_spawn)
    
    # Mandala symmetry
    num_petals = 12
    sym_angles = np.round(angles * num_petals / (2 * np.pi)) * (2 * np.pi / num_petals)
    
    # Modulate speed and angle offset based on symmetry and time
    speed = 2.0 + 3.0 * np.sin(sym_angles * 3 + t * 2)
    angle_offset = np.sin(t * 3) * 0.5 * np.cos(sym_angles * 2)
    
    final_angles = angles + angle_offset
    
    velocities[mask, 0] = np.cos(final_angles) * speed
    velocities[mask, 1] = np.sin(final_angles) * speed
    
    # Color based on angle and time
    colors[mask] = (np.degrees(sym_angles) + t * 100) % 360

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initial spawn all
    mask = np.ones(NUM_PARTICLES, dtype=bool)
    spawn_particles(mask, 0)
    
def draw():
    py5.blend_mode(py5.BLEND)
    # Slow fade
    py5.fill(10, 80, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.015
    
    global positions, velocities, lifetimes, colors
    
    # Update physics
    dt = 0.02
    positions += velocities * (dt * 60)
    lifetimes -= dt
    
    # Add curl/vortex forces based on distance from center
    dx = positions[:, 0] - SIZE[0]/2
    dy = positions[:, 1] - SIZE[1]/2
    dist = np.sqrt(dx*dx + dy*dy) + 0.1
    
    # Tangent vectors
    tx = -dy / dist
    ty = dx / dist
    
    # Modulate vortex strength based on time and distance
    vortex_strength = np.sin(dist * 0.01 - t * 5) * 0.5
    velocities[:, 0] += tx * vortex_strength
    velocities[:, 1] += ty * vortex_strength
    
    # Find dead particles and respawn
    dead_mask = lifetimes <= 0
    spawn_particles(dead_mask, t)
    
    # Draw points
    # We can batch draw by hue ranges if we want, or just draw all.
    # Since drawing 150k individual colored points in py5 without custom shaders
    # is tricky if each has a different color, let's group by hue bins.
    
    num_bins = 20
    py5.stroke_weight(2)
    
    for i in range(num_bins):
        hue_start = (i / num_bins) * 360
        hue_end = ((i + 1) / num_bins) * 360
        
        bin_mask = (colors >= hue_start) & (colors < hue_end)
        bin_positions = positions[bin_mask]
        
        if len(bin_positions) > 0:
            py5.stroke(hue_start, 80, 100, 30)
            py5.begin_shape(py5.POINTS)
            # Py5 currently requires looping for points unless we use py5.points() which isn't always available in all versions, let's try looping or numpy conversion.
            # Using py5.points() if possible, else loop:
            try:
                py5.points(bin_positions)
            except AttributeError:
                for p in bin_positions:
                    py5.vertex(p[0], p[1])
            py5.end_shape()

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
