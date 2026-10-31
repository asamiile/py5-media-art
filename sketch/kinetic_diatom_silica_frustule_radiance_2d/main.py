"""
Kinetic Diatom Silica Frustule Radiance
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork inspired by Ernst Haeckel's diatom morphology
and polarized light confocal microscopy. Explores the biomineralization architecture
of marine diatom silica shells (frustules), featuring radial costae ribs,
concentric loculi chambers with cribrum sieve pore arrays, coronal hyaline spines,
and dynamic optical thin-film interference coloration across a hadal marine abyss.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_diatom_silica_frustule_radiance_2d"
WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 720
FPS = 60

# Paths
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
PREVIEW_PATH = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")

# Dynamic non-fixed initial phase and parameters for run variation
RNG_PHASE_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RNG_CHIRALITY = 1.0 if np.random.uniform() > 0.5 else -1.0
RNG_PULSE_RATE = float(np.random.uniform(0.95, 1.05))

# Marine snow ambient suspension particles
NUM_PARTICLES = 90
PARTICLES_DATA = [
    (
        float(np.random.uniform(50, WIDTH - 50)),
        float(np.random.uniform(50, HEIGHT - 50)),
        float(np.random.uniform(1.6, 3.6)),
        float(np.random.uniform(0.0, 2.0 * np.pi)),
        float(np.random.uniform(12.0, 28.0))
    )
    for _ in range(NUM_PARTICLES)
]

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    t_cycle = 2.0 * np.pi * tau
    
    # 1. Background: Deep Hadal Marine Abyss
    py5.background(6, 11, 18)
    
    cx, cy = WIDTH * 0.5, HEIGHT * 0.5
    
    # Drifting marine snow & micro-plankton
    py5.no_stroke()
    for (px, py_base, p_rad, p_phase, p_amp) in PARTICLES_DATA:
        drift_x = px + p_amp * 0.5 * np.sin(t_cycle + p_phase)
        drift_y = (py_base + p_amp * np.cos(t_cycle + p_phase)) % HEIGHT
        py5.fill(65, 155, 195, 65)
        py5.circle(drift_x, drift_y, p_rad)
        
    # Concentric ambient diffraction rings in seawater
    py5.no_fill()
    py5.stroke(25, 55, 80, 48)
    py5.stroke_weight(0.8)
    for r in range(120, 960, 48):
        py5.circle(cx, cy, r * 2.0)
        
    # 2. Chambered Valve Disk (Loculi Sectors)
    num_sectors = 24
    num_tiers = 6
    tier_radii = [90.0, 155.0, 230.0, 310.0, 395.0, 470.0, 530.0]
    
    for t_idx in range(num_tiers):
        r1 = tier_radii[t_idx]
        r2 = tier_radii[t_idx + 1]
        
        for s_idx in range(num_sectors):
            ang1 = s_idx * (2.0 * np.pi / num_sectors)
            ang2 = (s_idx + 1) * (2.0 * np.pi / num_sectors)
            
            # Harmonic osmotic breathing of chamber walls
            b_offset = 0.022 * np.sin(
                t_cycle * 2.0 * RNG_PULSE_RATE + 
                t_idx * 0.9 + 
                s_idx * 0.4 * RNG_CHIRALITY + 
                RNG_PHASE_OFFSET
            )
            a1 = ang1 + b_offset
            a2 = ang2 - b_offset
            
            # Polarized structural thin-film interference colors
            color_mode = (s_idx * 2 + t_idx * 3) % 4
            if color_mode == 0:
                fr, fg, fb = 14, 165, 195 # Electric turquoise / cyan
            elif color_mode == 1:
                fr, fg, fb = 168, 70, 210 # Opalescent amethyst / violet
            elif color_mode == 2:
                fr, fg, fb = 225, 175, 45 # Solar silica amber
            else:
                fr, fg, fb = 35, 195, 150 # Emerald diatom chlorophyll glow
                
            alpha = 75 + int(32 * np.sin(t_cycle + t_idx * 0.7 + s_idx * 0.3))
            py5.fill(fr, fg, fb, alpha)
            py5.stroke(fr // 2, fg // 2, fb // 2, 125)
            py5.stroke_weight(0.9)
            
            p1 = (cx + r1 * np.cos(a1), cy + r1 * np.sin(a1))
            p2 = (cx + r2 * np.cos(a1), cy + r2 * np.sin(a1))
            p3 = (cx + r2 * np.cos(a2), cy + r2 * np.sin(a2))
            p4 = (cx + r1 * np.cos(a2), cy + r1 * np.sin(a2))
            
            py5.begin_shape()
            py5.vertex(p1[0], p1[1])
            py5.vertex(p2[0], p2[1])
            py5.vertex(p3[0], p3[1])
            py5.vertex(p4[0], p4[1])
            py5.end_shape(py5.CLOSE)
            
            # Cribrum Sieve Micro-Pore Array inside each chamber
            span_a = a2 - a1
            r_steps = t_idx + 2
            a_steps = 3
            
            for ir in range(1, r_steps):
                pr = r1 + (r2 - r1) * (ir / r_steps)
                for ia in range(1, a_steps):
                    pa = a1 + span_a * (ia / a_steps)
                    px = cx + pr * np.cos(pa)
                    py_pt = cy + pr * np.sin(pa)
                    
                    # Glowing cribrum pore
                    py5.no_stroke()
                    py5.fill(215, 248, 255, 210)
                    py5.circle(px, py_pt, 2.8)
                    py5.fill(fr, fg, fb, 75)
                    py5.circle(px, py_pt, 6.8)

    # 3. Radial Silica Costae (Main Structural Ribs with 3D Emboss)
    for s_idx in range(num_sectors):
        ang = s_idx * (2.0 * np.pi / num_sectors)
        
        x_in = cx + tier_radii[0] * np.cos(ang)
        y_in = cy + tier_radii[0] * np.sin(ang)
        x_out = cx + tier_radii[-1] * np.cos(ang)
        y_out = cy + tier_radii[-1] * np.sin(ang)
        
        # Deep cast shadow for 3D tubular silica rib relief
        py5.stroke(8, 16, 28, 240)
        py5.stroke_weight(3.6)
        py5.line(x_in, y_in, x_out, y_out)
        
        # Specular crest line
        py5.stroke(140, 230, 255, 230)
        py5.stroke_weight(1.4)
        py5.line(x_in - 0.7, y_in - 0.7, x_out - 0.7, y_out - 0.7)
        
    # 4. Outer Marginal Velum & Coronal Spines
    r_rim = tier_radii[-1]
    py5.no_fill()
    py5.stroke(80, 190, 230, 210)
    py5.stroke_weight(2.6)
    py5.circle(cx, cy, r_rim * 2.0)
    
    # Outer hyaline border rings
    py5.stroke(50, 120, 160, 130)
    py5.stroke_weight(1.0)
    py5.circle(cx, cy, (r_rim + 12.0) * 2.0)
    py5.circle(cx, cy, (r_rim + 30.0) * 2.0)
    
    # Coronal silica spines with jewel beads
    num_spines = 72
    for sp_idx in range(num_spines):
        sp_ang = sp_idx * (2.0 * np.pi / num_spines) + 0.03 * np.sin(t_cycle * RNG_CHIRALITY)
        sp_len = 24.0 + 8.0 * np.sin(sp_idx * 3 + t_cycle * 2.0)
        sx1 = cx + r_rim * np.cos(sp_ang)
        sy1 = cy + r_rim * np.sin(sp_ang)
        sx2 = cx + (r_rim + sp_len) * np.cos(sp_ang)
        sy2 = cy + (r_rim + sp_len) * np.sin(sp_ang)
        
        py5.stroke(120, 225, 255, 210)
        py5.stroke_weight(1.2)
        py5.line(sx1, sy1, sx2, sy2)
        
        # Apical hyaline jewel bead
        py5.fill(220, 248, 255)
        py5.no_stroke()
        py5.circle(sx2, sy2, 3.8)
        py5.fill(56, 189, 248, 90)
        py5.circle(sx2, sy2, 9.0)
        
    # 5. Central Nodule & Sternum Rosette
    py5.fill(10, 20, 32)
    py5.stroke(110, 230, 255, 240)
    py5.stroke_weight(2.4)
    py5.circle(cx, cy, tier_radii[0] * 2.0)
    
    # Multi-tier central star rosette
    for rosette_tier in [56.0, 34.0]:
        num_petals = 12
        py5.begin_shape()
        for pt in range(num_petals * 2 + 1):
            p_a = pt * (np.pi / num_petals) + 0.08 * np.sin(t_cycle + rosette_tier * 0.1)
            rad = rosette_tier if (pt % 2 == 0) else (rosette_tier * 0.44)
            vx = cx + rad * np.cos(p_a)
            vy = cy + rad * np.sin(p_a)
            py5.vertex(vx, vy)
        py5.fill(250, 210, 75, 210) # Imperial gold silica core
        py5.stroke(255, 245, 180)
        py5.stroke_weight(1.5)
        py5.end_shape(py5.CLOSE)
        
    # Central pyrenoid bead
    py5.fill(255, 255, 255)
    py5.no_stroke()
    py5.circle(cx, cy, 14.0)
    py5.fill(56, 189, 248, 120)
    py5.circle(cx, cy, 26.0)
    
    # 6. Technical Confocal Microscopy Markings
    py5.stroke(65, 130, 175, 170)
    py5.stroke_weight(1.0)
    py5.line(80, HEIGHT - 70, 360, HEIGHT - 70)
    for tm in range(80, 380, 28):
        py5.line(tm, HEIGHT - 70, tm, HEIGHT - 82)
        
    # Objective angle & polar indicator in top right
    ind_cx = WIDTH - 90
    ind_cy = 90
    py5.no_fill()
    py5.stroke(50, 100, 145, 160)
    py5.stroke_weight(1.0)
    py5.circle(ind_cx, ind_cy, 68.0)
    py5.line(ind_cx - 34, ind_cy, ind_cx + 34, ind_cy)
    py5.line(ind_cx, ind_cy - 34, ind_cx, ind_cy + 34)
    py5.stroke(56, 189, 248, 220)
    py5.stroke_weight(1.8)
    nd_x = ind_cx + 30.0 * np.cos(t_cycle * RNG_CHIRALITY)
    nd_y = ind_cy + 30.0 * np.sin(t_cycle * RNG_CHIRALITY)
    py5.line(ind_cx, ind_cy, nd_x, nd_y)
    py5.fill(56, 189, 248)
    py5.no_stroke()
    py5.circle(nd_x, nd_y, 4.2)

def draw():
    print(f"[{WORK_NAME}] Starting 4K render: {TOTAL_FRAMES} frames @ Retina 4K (3840x2160)...")
    start_time = time.time()
    
    for f in range(TOTAL_FRAMES):
        f_start = time.time()
        render_frame_batched(f)
        
        frame_file = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        py5.save_frame(frame_file)
        
        # Save preview at midpoint (frame 360)
        if f == TOTAL_FRAMES // 2:
            py5.save_frame(PREVIEW_PATH)
            print(f"[{WORK_NAME}] Saved preview frame {f} -> {PREVIEW_PATH}")
            
        f_elapsed = time.time() - f_start
        if (f + 1) % 60 == 0 or f == 0 or f == TOTAL_FRAMES - 1:
            fps_est = (f + 1) / (time.time() - start_time)
            remaining = (TOTAL_FRAMES - (f + 1)) / max(fps_est, 0.001)
            print(f"[{WORK_NAME}] Frame {f+1:03d}/{TOTAL_FRAMES} ({f_elapsed:.3f}s/f, ~{fps_est:.2f} fps, {remaining:.1f}s remaining)")
            
    total_time = time.time() - start_time
    print(f"[{WORK_NAME}] Render completed in {total_time:.1f}s ({total_time/TOTAL_FRAMES:.3f}s/frame)")
    
    # Compile MP4 via FFmpeg at full 4K (3840x2160)
    print(f"[{WORK_NAME}] Encoding 4K 60fps MP4 via FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        OUTPUT_MP4
    ]
    res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg error: {res.stderr}")
        raise RuntimeError("FFmpeg encoding failed")
        
    mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
    print(f"[{WORK_NAME}] Output MP4 generated: {OUTPUT_MP4} ({mp4_size_mb:.2f} MB)")
    
    # Cleanup frames directory
    print(f"[{WORK_NAME}] Cleaning up temporary frames directory...")
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
    print(f"[{WORK_NAME}] Cleanup complete. Done!")
    
    # Explicitly exit JVM process to prevent hanging
    os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
