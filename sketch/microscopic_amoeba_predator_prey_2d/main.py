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
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

amoebas = []
predators = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate initial ecosystem
    for _ in range(300):
        amoebas.append({
            'x': py5.random(0, SIZE[0]),
            'y': py5.random(0, SIZE[1]),
            'vx': py5.random(-2, 2),
            'vy': py5.random(-2, 2),
            'seed': py5.random(0, 1000)
        })
        
    for _ in range(8):
        predators.append({
            'x': py5.random(0, SIZE[0]),
            'y': py5.random(0, SIZE[1]),
            'vx': py5.random(-4, 4),
            'vy': py5.random(-4, 4),
            'seed': py5.random(0, 1000),
            'energy': 100
        })

def draw_blob(x, y, r, base_color, noise_seed, time):
    py5.fill(*base_color)
    py5.no_stroke()
    py5.begin_shape()
    num_points = 12
    for i in range(num_points):
        angle = i * py5.TWO_PI / num_points
        # Organic undulation
        n = py5.os_noise(py5.cos(angle)*0.5 + noise_seed, py5.sin(angle)*0.5 + noise_seed, time)
        radius = r + n * r * 0.4
        px = x + py5.cos(angle) * radius
        py = y + py5.sin(angle) * radius
        py5.curve_vertex(px, py)
    # connect the curve
    for i in range(3):
        angle = i * py5.TWO_PI / num_points
        n = py5.os_noise(py5.cos(angle)*0.5 + noise_seed, py5.sin(angle)*0.5 + noise_seed, time)
        radius = r + n * r * 0.4
        px = x + py5.cos(angle) * radius
        py = y + py5.sin(angle) * radius
        py5.curve_vertex(px, py)
    py5.end_shape()

def draw():
    # Fluid dark background with high transparency for trails
    py5.fill(10, 15, 20, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.02
    
    # Update and draw Amoebas
    for a in amoebas:
        # Flowfield drift
        nx = py5.os_noise(a['x'] * 0.002, a['y'] * 0.002, time) * py5.TWO_PI * 2
        a['vx'] += py5.cos(nx) * 0.5
        a['vy'] += py5.sin(nx) * 0.5
        
        # Friction
        a['vx'] *= 0.95
        a['vy'] *= 0.95
        
        a['x'] += a['vx']
        a['y'] += a['vy']
        
        # Wrap
        if a['x'] < 0: a['x'] += SIZE[0]
        if a['x'] > SIZE[0]: a['x'] -= SIZE[0]
        if a['y'] < 0: a['y'] += SIZE[1]
        if a['y'] > SIZE[1]: a['y'] -= SIZE[1]
        
        draw_blob(a['x'], a['y'], 12, (0, 180, 180, 150), a['seed'], time * 2)
        
    # Update and draw Predators
    for p in predators:
        # Find nearest amoeba
        closest = None
        min_dist = float('inf')
        for a in amoebas:
            dx = a['x'] - p['x']
            dy = a['y'] - p['y']
            d2 = dx*dx + dy*dy
            if d2 < min_dist:
                min_dist = d2
                closest = a
        
        if closest and min_dist < 40000:
            dx = closest['x'] - p['x']
            dy = closest['y'] - p['y']
            dist = py5.sqrt(dx*dx + dy*dy)
            if dist > 0:
                p['vx'] += (dx/dist) * 1.5
                p['vy'] += (dy/dist) * 1.5
                
            if dist < 20: # Eat!
                closest['x'] = py5.random(0, SIZE[0])
                closest['y'] = py5.random(0, SIZE[1])
                p['energy'] = min(200, p['energy'] + 50)
                # Burst particles could be drawn here
                py5.fill(255, 255, 0, 200)
                py5.ellipse(p['x'], p['y'], 80, 80)
        else:
            nx = py5.os_noise(p['x'] * 0.002, p['y'] * 0.002, time + 100) * py5.TWO_PI * 2
            p['vx'] += py5.cos(nx) * 0.5
            p['vy'] += py5.sin(nx) * 0.5
            
        p['vx'] *= 0.92
        p['vy'] *= 0.92
        
        p['x'] += p['vx']
        p['y'] += p['vy']
        
        if p['x'] < 0: p['x'] += SIZE[0]
        if p['x'] > SIZE[0]: p['x'] -= SIZE[0]
        if p['y'] < 0: p['y'] += SIZE[1]
        if p['y'] > SIZE[1]: p['y'] -= SIZE[1]
        
        size = 30 + py5.sin(time*5 + p['seed']) * 5
        draw_blob(p['x'], p['y'], size, (220, 20, 50, 180), p['seed'], time)
        # Inner core
        draw_blob(p['x'], p['y'], size*0.4, (255, 100, 0, 200), p['seed']+10, time*1.5)
        
    py5.blend_mode(py5.BLEND)

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
