"""
Kinetic Auxetic Kirigami Metamaterial Tessellation
4K (3840x2160) 60fps 720 frames (12.0s seamless loop)

Autonomous generative media artwork exploring rotating rigid unit metamaterials
(Grima & Evans kinematics) rendered as handcrafted Echizen washi paper facets
with debossed geometric reliefs, contact drop shadows, and an illuminated
amber-gold substrate revealed through opening voids.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

# Artwork specifications
WORK_NAME = "kinetic_auxetic_kirigami_metamaterial_tessellation_2d"
WIDTH = 1920
HEIGHT = 1080
TOTAL_FRAMES = 720
FPS = 60
THETA_MAX = np.radians(38.0)

# Paths
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "frames")
PREVIEW_PATH = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")

# Global generation state (coordinates scaled for 1920x1080 logical / 3840x2160 Retina)
L_BASE = 56.0
H_BASE = L_BASE * 0.5
SQ_CORNERS = np.array([
    [-H_BASE, -H_BASE],
    [H_BASE, -H_BASE],
    [H_BASE, H_BASE],
    [-H_BASE, H_BASE]
], dtype=np.float64)

# Dynamic seed variation for unique aesthetic tone
RNG_STUD_JITTER = float(np.random.uniform(0.94, 1.06))

def setup():
    py5.size(WIDTH, HEIGHT)
    py5.no_loop()
    os.makedirs(FRAMES_DIR, exist_ok=True)

def render_frame_batched(frame_idx: int):
    tau = frame_idx / TOTAL_FRAMES
    
    # Smooth C1 harmonic angle: 0 at t=0 and t=T, max at t=T/2
    theta = THETA_MAX * 0.5 * (1.0 - np.cos(2.0 * np.pi * tau))
    
    # Center and basis vectors
    cx, cy = WIDTH * 0.5, HEIGHT * 0.5
    scale = 2.0 * H_BASE * np.cos(theta)
    u_vec = scale * np.array([1.0, 1.0])
    v_vec = scale * np.array([1.0, -1.0])
    
    # 1. Base Ground
    py5.background(14, 16, 22)  # Obsidian slate
    
    # 2. Back-illuminated radiant amber / cinnabar core
    glow_pulse = 0.65 + 0.35 * (np.sin(np.pi * tau) ** 2)
    py5.no_stroke()
    for r_step in range(24, 0, -2):
        rad = r_step * 55.0 * glow_pulse
        frac = 1.0 - (r_step / 24.0)
        r_col = int(235 * frac + 170 * (1 - frac))
        g_col = int(175 * frac + 35 * (1 - frac))
        b_col = int(35 * frac + 10 * (1 - frac))
        alpha = int((10 + 20 * frac) * glow_pulse)
        py5.fill(r_col, g_col, b_col, alpha)
        py5.circle(cx, cy, rad * 2.0)
        
    # Gather quads
    quads_even = []
    quads_odd = []
    centers_even = []
    centers_odd = []
    
    nu, nv = 24, 24
    for u in range(-nu, nu + 1):
        for v in range(-nv, nv + 1):
            center = np.array([cx, cy]) + u * u_vec + v * v_vec
            if -120 <= center[0] <= WIDTH + 120 and -120 <= center[1] <= HEIGHT + 120:
                sign = 1 if (u + v) % 2 == 0 else -1
                phi = sign * theta
                c_phi, s_phi = np.cos(phi), np.sin(phi)
                R = np.array([[c_phi, -s_phi], [s_phi, c_phi]])
                pts = (SQ_CORNERS @ R.T) + center
                if (u + v) % 2 == 0:
                    quads_even.append(pts)
                    centers_even.append(center)
                else:
                    quads_odd.append(pts)
                    centers_odd.append(center)
                    
    q_even = np.array(quads_even, dtype=np.float32)  # (N_even, 4, 2)
    q_odd = np.array(quads_odd, dtype=np.float32)    # (N_odd, 4, 2)
    c_even = np.array(centers_even, dtype=np.float32)[:, np.newaxis, :]
    c_odd = np.array(centers_odd, dtype=np.float32)[:, np.newaxis, :]
    
    # Inset geometry for debossed box relief
    in_even_1 = q_even * 0.74 + c_even * 0.26
    in_odd_1 = q_odd * 0.74 + c_odd * 0.26
    
    in_even_2 = q_even * 0.48 + c_even * 0.52
    in_odd_2 = q_odd * 0.48 + c_odd * 0.52
    
    # 3. Drop Shadows (Batched)
    # Broad ambient shadow
    py5.fill(8, 10, 15, 110)
    py5.no_stroke()
    py5.begin_shape(py5.QUADS)
    for q in q_even:
        py5.vertex(q[0, 0] + 7.0, q[0, 1] + 11.0)
        py5.vertex(q[1, 0] + 7.0, q[1, 1] + 11.0)
        py5.vertex(q[2, 0] + 7.0, q[2, 1] + 11.0)
        py5.vertex(q[3, 0] + 7.0, q[3, 1] + 11.0)
    for q in q_odd:
        py5.vertex(q[0, 0] + 7.0, q[0, 1] + 11.0)
        py5.vertex(q[1, 0] + 7.0, q[1, 1] + 11.0)
        py5.vertex(q[2, 0] + 7.0, q[2, 1] + 11.0)
        py5.vertex(q[3, 0] + 7.0, q[3, 1] + 11.0)
    py5.end_shape()
    
    # Tight contact shadow
    py5.fill(6, 8, 12, 175)
    py5.begin_shape(py5.QUADS)
    for q in q_even:
        py5.vertex(q[0, 0] + 3.0, q[0, 1] + 4.5)
        py5.vertex(q[1, 0] + 3.0, q[1, 1] + 4.5)
        py5.vertex(q[2, 0] + 3.0, q[2, 1] + 4.5)
        py5.vertex(q[3, 0] + 3.0, q[3, 1] + 4.5)
    for q in q_odd:
        py5.vertex(q[0, 0] + 3.0, q[0, 1] + 4.5)
        py5.vertex(q[1, 0] + 3.0, q[1, 1] + 4.5)
        py5.vertex(q[2, 0] + 3.0, q[2, 1] + 4.5)
        py5.vertex(q[3, 0] + 3.0, q[3, 1] + 4.5)
    py5.end_shape()
    
    # 4. Facets (Batched)
    # Even: Echizen mulberry bone white
    py5.fill(250, 247, 241)
    py5.stroke(145, 132, 118)
    py5.stroke_weight(1.4)
    py5.begin_shape(py5.QUADS)
    for q in q_even:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()
    
    # Odd: Unbleached linen flaxen washi
    py5.fill(242, 236, 226)
    py5.begin_shape(py5.QUADS)
    for q in q_odd:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()
    
    # Outer debossed groove
    py5.fill(235, 230, 220)
    py5.stroke(185, 175, 160)
    py5.stroke_weight(1.0)
    py5.begin_shape(py5.QUADS)
    for q in in_even_1:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    for q in in_odd_1:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()
    
    # Inner fine gold sashiko accent
    py5.fill(245, 242, 235)
    py5.stroke(212, 175, 55, 190)
    py5.stroke_weight(0.7)
    py5.begin_shape(py5.QUADS)
    for q in in_even_2:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    for q in in_odd_2:
        py5.vertex(q[0, 0], q[0, 1])
        py5.vertex(q[1, 0], q[1, 1])
        py5.vertex(q[2, 0], q[2, 1])
        py5.vertex(q[3, 0], q[3, 1])
    py5.end_shape()
    
    # Central burnished gold studs
    py5.fill(220, 170, 36, 235)
    py5.no_stroke()
    for c in centers_even:
        py5.circle(c[0], c[1], 3.8 * RNG_STUD_JITTER)
    for c in centers_odd:
        py5.circle(c[0], c[1], 3.8 * RNG_STUD_JITTER)
        
    # Hinge Rivets (at even quad vertices)
    py5.fill(228, 180, 50)
    py5.stroke(80, 60, 25, 170)
    py5.stroke_weight(0.8)
    for q in q_even:
        for p in q:
            py5.circle(p[0], p[1], 3.2)

def draw():
    print(f"[{WORK_NAME}] Starting 4K render: {TOTAL_FRAMES} frames @ Retina 4K (3840x2160)...")
    start_time = time.time()
    
    for f in range(TOTAL_FRAMES):
        f_start = time.time()
        render_frame_batched(f)
        
        frame_file = os.path.join(FRAMES_DIR, f"frame_{f:04d}.png")
        py5.save_frame(frame_file)
        
        # Save preview at midpoint (maximum auxetic opening)
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
    
    # Exit JVM process cleanly on macOS
    os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
