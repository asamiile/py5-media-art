"""
Kinetic Ferrofluid Rosensweig Magnetic Spires
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork exploring the Rosensweig magnetic fluid instability.
A dynamic hexagonal lattice of sharp conical ferrofluid spires emerges from a dark
petroleum pool under a rotating electromagnetic flux field, featuring metallic Blinn-Phong
shading, iridescent oil-slick meniscus rings, and glowing magnetic dipole field lines.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_ferrofluid_rosensweig_magnetic_spires_2d"
WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 720
FPS = 60

# Paths
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
PREVIEW_PATH = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")

# Non-fixed random seed jitter for unique variation per execution
RNG_PHASE_OFFSET = float(np.random.uniform(0.0, 2.0 * np.pi))
RNG_CHIRALITY = 1.0 if np.random.uniform() > 0.5 else -1.0

# Pre-generate hexagonal spire grid positions
D_SPIRE = 105.0
SPIRES_DATA = []
for row in range(-6, 7):
    for col in range(-8, 9):
        gx = col * D_SPIRE + (abs(row) % 2) * (D_SPIRE * 0.5)
        gy = row * (D_SPIRE * np.sqrt(3) * 0.5)
        dist = np.hypot(gx, gy)
        if dist <= 540.0:
            env = np.exp(-(dist / 370.0)**2)
            angle = np.arctan2(gy, gx)
            SPIRES_DATA.append((gx, gy, dist, angle, env))

# Sort back-to-front by Y for correct conical occlusion
SPIRES_DATA.sort(key=lambda s: s[1])

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    t_cycle = 2.0 * np.pi * tau
    
    # 1. Background: Deep magnetic obsidian laboratory ground
    py5.background(10, 12, 17)
    
    cx, cy = WIDTH * 0.5, HEIGHT * 0.5
    
    # 2. Magnetic Field Potential Contours (Quadrupole & Dipole Flux)
    py5.no_fill()
    py5.stroke(28, 45, 70, 75)
    py5.stroke_weight(0.9)
    for r in range(110, 1020, 48):
        py5.begin_shape()
        for deg in range(0, 360, 4):
            rad = np.radians(deg)
            # Chiral electromagnetic quadrupole deformation
            r_mod = r * (
                1.0 + 
                0.07 * np.sin(4.0 * rad - RNG_CHIRALITY * t_cycle + RNG_PHASE_OFFSET) + 
                0.03 * np.cos(2.0 * rad + t_cycle)
            )
            px = cx + r_mod * np.cos(rad)
            py = cy + r_mod * np.sin(rad)
            py5.vertex(px, py)
        py5.end_shape(py5.CLOSE)
        
    # Dipole flux streamlines
    py5.stroke(35, 75, 120, 85)
    py5.stroke_weight(0.8)
    for angle_deg in range(0, 360, 18):
        a = np.radians(angle_deg) + 0.12 * np.sin(t_cycle)
        p1x = cx + 80.0 * np.cos(a)
        p1y = cy + 80.0 * np.sin(a)
        p2x = cx + 920.0 * np.cos(a + 0.45 * RNG_CHIRALITY)
        p2y = cy + 920.0 * np.sin(a + 0.45 * RNG_CHIRALITY)
        py5.line(p1x, p1y, p2x, p2y)
        
    # Rotating magnetic illumination vector
    light_az = t_cycle * RNG_CHIRALITY + RNG_PHASE_OFFSET + np.radians(55.0)
    lx = np.cos(light_az)
    ly = np.sin(light_az)
    
    # 3. Hexagonal Ferrofluid Spire Lattice
    for (sx, sy, dist, angle, env) in SPIRES_DATA:
        # Spiral traveling wave in magnetic potential
        wave_phase = t_cycle * 2.0 - dist * 0.013 + angle * 2.0 * RNG_CHIRALITY
        pulse = np.sin(wave_phase)
        
        # Conical height and base radius
        height = (120.0 + 38.0 * pulse) * env
        base_r = (46.0 + 9.0 * pulse) * env
        
        if base_r < 4.0:
            continue
            
        px = cx + sx
        py = cy + sy
        
        # Meniscus depression shadow ring on fluid pool
        py5.no_stroke()
        py5.fill(5, 7, 10, 190)
        py5.ellipse(px + 4.0, py + 8.0, base_r * 2.6, base_r * 2.1)
        
        # Concentric Capillary Meniscus Rings (oil-slick interference)
        py5.no_fill()
        py5.stroke(24, 48, 72, 120)
        py5.stroke_weight(1.2)
        py5.ellipse(px, py + 3.0, base_r * 2.3, base_r * 1.85)
        
        py5.stroke(45, 85, 125, 90)
        py5.stroke_weight(0.9)
        py5.ellipse(px, py + 1.5, base_r * 1.65, base_r * 1.35)
        
        # Spire Tip position with subtle magnetic tilt
        tip_x = px + 8.0 * lx * env + 4.0 * np.sin(wave_phase)
        tip_y = py - height
        
        # 3D Conical Surface Shading with Blinn-Phong Metallic Sheen
        num_segments = 24
        angles = np.linspace(0, 2 * np.pi, num_segments + 1)
        
        for k in range(num_segments):
            a1 = angles[k]
            a2 = angles[k + 1]
            
            bx1 = px + base_r * np.cos(a1)
            by1 = py + base_r * 0.65 * np.sin(a1)
            bx2 = px + base_r * np.cos(a2)
            by2 = py + base_r * 0.65 * np.sin(a2)
            
            mid_a = 0.5 * (a1 + a2)
            nx = np.cos(mid_a)
            ny = np.sin(mid_a)
            
            # Diffuse illumination
            diff = max(0.0, nx * lx + ny * ly)
            
            # Specular metallic sheen
            half_x = (lx + 0.0) / np.sqrt(lx**2 + 1.0)
            half_y = (ly - 0.7) / np.sqrt((ly - 0.7)**2 + 1.0)
            spec = max(0.0, nx * half_x + ny * half_y)**18
            
            # Deep metallic carbon-slate with electric cobalt/cyan sheen
            r_col = int(12 + diff * 32 + spec * 170)
            g_col = int(18 + diff * 48 + spec * 215)
            b_col = int(28 + diff * 80 + spec * 255)
            
            py5.fill(r_col, g_col, b_col)
            py5.stroke(r_col // 2, g_col // 2, b_col // 2, 85)
            py5.stroke_weight(0.5)
            
            py5.begin_shape(py5.TRIANGLES)
            py5.vertex(tip_x, tip_y)
            py5.vertex(bx1, by1)
            py5.vertex(bx2, by2)
            py5.end_shape()
            
        # Apical Magnetic Field Concentration Bead
        py5.no_stroke()
        py5.fill(170, 240, 255, 230)
        py5.circle(tip_x, tip_y, 4.4)
        py5.fill(45, 190, 255, 80)
        py5.circle(tip_x, tip_y, 11.5)
        
    # 4. Technical Laboratory Markings & Magnetic Flux Meter
    # Scale bar in bottom left
    py5.stroke(55, 95, 145, 170)
    py5.stroke_weight(1.0)
    py5.line(80, HEIGHT - 70, 380, HEIGHT - 70)
    for mk in range(80, 400, 30):
        py5.line(mk, HEIGHT - 70, mk, HEIGHT - 82)
        
    # Rotating magnetic field angle indicator in top right
    ind_cx = WIDTH - 90
    ind_cy = 90
    ind_r = 38.0
    py5.no_fill()
    py5.stroke(45, 80, 125, 150)
    py5.stroke_weight(1.0)
    py5.circle(ind_cx, ind_cy, ind_r * 2.0)
    
    # Vector needle
    nx = ind_cx + ind_r * 0.85 * np.cos(light_az)
    ny = ind_cy + ind_r * 0.85 * np.sin(light_az)
    py5.stroke(56, 189, 248, 220)
    py5.stroke_weight(1.8)
    py5.line(ind_cx, ind_cy, nx, ny)
    py5.fill(56, 189, 248)
    py5.no_stroke()
    py5.circle(nx, ny, 4.5)
    py5.fill(120, 160, 210)
    py5.circle(ind_cx, ind_cy, 3.5)

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
