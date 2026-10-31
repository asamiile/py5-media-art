"""
kinetic_rutt_etra_scan_processor_synthesis_2d
Autonomous 4K Media Art Animation (12.0s seamless loop, 720 frames @ 60fps)

Homage to the 1973 Rutt-Etra Video Synthesizer and early video scan processing
art pioneered by Woody & Steina Vasulka and Louise & Bill Etra.
Simulates voltage-controlled vertical deflection of horizontal CRT raster scanlines
into dynamic 3D undulating topographical video landscapes with 3-channel RGB
chromatic aberration, horizontal sync glitch tracking slices, P22 phosphor persistence glow,
NTSC vectorscope constellation monitor, XY audio oscilloscope, and IRE waveform monitors.
Strictly autonomous and anonymous; completely free of author signatures or personal marks.
"""

import os
import shutil
import subprocess
import time
import numpy as np
import py5

WORK_NAME = "kinetic_rutt_etra_scan_processor_synthesis_2d"
SKETCH_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_DIR = os.path.join(SKETCH_DIR, "temp_frames")
OUTPUT_MP4 = os.path.join(SKETCH_DIR, "output.mp4")
PREVIEW_PNG = os.path.join(SKETCH_DIR, f"{WORK_NAME}_p1.png")

TOTAL_FRAMES = 720
FPS = 60
WIDTH, HEIGHT = 3840, 2160
CX, CY = WIDTH // 2, HEIGHT // 2
TAU = 2 * np.pi

# Precomputed 2D meshgrid parameters for ultra-fast vectorized lines
N_LINES = 150
N_SAMPLES = 360

U_VALS = np.linspace(-1.0, 1.0, N_SAMPLES)
V_VALS = np.linspace(-1.0, 1.0, N_LINES)
U_GRID, V_GRID = np.meshgrid(U_VALS, V_VALS)
R_UV = np.sqrt(U_GRID**2 + V_GRID**2)
THETA_UV = np.arctan2(V_GRID, U_GRID)
ENVELOPE = np.exp(-1.6 * (U_GRID**2 + V_GRID**2))

SCALE_W = 1380.0
SCALE_H = 650.0

# Precomputed scope angle arrays
ANGLES_VEC = np.linspace(0, TAU, 240)
ANGLES_LISS = np.linspace(0, TAU, 300)
X_WAVEFORM = np.linspace(CX - 600.0, CX + 600.0, 260)
NORM_W = (X_WAVEFORM - CX) / 600.0
WAVEFORM_ENV = np.exp(-NORM_W**2)

current_frame = 0
start_time = 0.0

def settings():
    py5.size(WIDTH, HEIGHT, py5.P2D)
    py5.smooth(8)

def setup():
    global start_time
    py5.frame_rate(FPS)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    start_time = time.time()
    print(f"[{WORK_NAME}] Starting 4K UHD 60fps rendering ({TOTAL_FRAMES} frames)...")

def draw():
    global current_frame
    
    t_val = current_frame / TOTAL_FRAMES
    
    # CRT Chassis deep phosphor black
    py5.background(4, 6, 9)
    
    # 0. CRT Chassis & Curved Tube Bezel
    py5.stroke(18, 26, 38)
    py5.stroke_weight(3.5)
    py5.no_fill()
    py5.rect_mode(py5.CORNER)
    py5.rect(80, 80, WIDTH - 160, HEIGHT - 160, 64)
    py5.stroke(10, 15, 22)
    py5.rect(60, 60, WIDTH - 120, HEIGHT - 120, 80)
    
    # Faceplate scanline aperture grille
    py5.stroke(12, 18, 28, 80)
    py5.stroke_weight(1.0)
    for y_grille in range(100, HEIGHT - 100, 8):
        py5.line(100, y_grille, WIDTH - 100, y_grille)

    # Graticule crosshairs
    py5.stroke(24, 40, 58, 120)
    py5.stroke_weight(1.5)
    py5.line(CX, 100, CX, HEIGHT - 100)
    py5.line(100, CY, WIDTH - 100, CY)
    for tick in range(-12, 13):
        if tick != 0:
            py5.line(CX - 10, CY + tick * 70, CX + 10, CY + tick * 70)
            py5.line(CX + tick * 110, CY - 10, CX + tick * 110, CY + 10)

    # Telemetry HUD
    py5.fill(35, 210, 235, 200)
    py5.text_size(22)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text("RUTT-ETRA VIDEO SYNTHESIZER 1973", 130, 110)
    py5.text(f"DUAL-RAMP DEFLECTION OSCILLATOR [LOCK: {int(t_val*360)}°]", 130, 144)
    py5.text("Z-AXIS LUMINANCE MODULATION: 4.80 Vpp", 130, 178)
    py5.text_align(py5.RIGHT, py5.TOP)
    py5.text("ANALOG SCAN TOPOGRAPHY • P22 PHOSPHOR", WIDTH - 130, 110)
    py5.text("NTSC COLORBURST 3.579545 MHz", WIDTH - 130, 144)

    # -------------------------------------------------------------
    # 1. 3D Scanline Topography (Vectorized Multi-Channel RGB)
    # -------------------------------------------------------------
    channels = [
        {"col_glow": (245, 50, 80, 30), "col_core": (255, 60, 95, 150), "sw_g": 6.5, "sw_c": 2.2, "dx": 4.0, "dt": 0.012},
        {"col_glow": (30, 100, 255, 30), "col_core": (40, 130, 255, 150), "sw_g": 6.5, "sw_c": 2.2, "dx": -4.0, "dt": -0.012},
        {"col_glow": (30, 240, 120, 50), "col_core": (60, 255, 160, 230), "sw_g": 8.0, "sw_c": 2.6, "dx": 0.0, "dt": 0.0},
    ]
    
    for ch in channels:
        t_ch = t_val + ch["dt"]
        
        # Harmonic video voltage equation
        z1 = np.sin(9.0 * R_UV - 2.0 * TAU * t_ch)
        z2 = np.sin(3.0 * THETA_UV + 6.0 * R_UV - TAU * t_ch)
        z3 = np.cos(3.0 * TAU * U_GRID + TAU * t_ch) * np.sin(2.5 * TAU * V_GRID - TAU * t_ch)
        Z = (0.55 * z1 + 0.35 * z2 + 0.25 * z3) * ENVELOPE * 280.0
        
        # Horizontal sync jitter glitch on specific scanlines
        H_glitch = np.zeros_like(U_GRID)
        glitch_rows = (np.arange(N_LINES) + int(t_val * 60)) % 28 == 0
        H_glitch[glitch_rows, :] = 25.0 * np.sin(np.arange(N_LINES)[glitch_rows, None] * 2.5 + TAU * t_val)
        
        X_pts = CX + (U_GRID * SCALE_W) + ch["dx"] + H_glitch
        Y_pts = CY + (V_GRID * SCALE_H) + 60.0 - Z
        
        # Segment mesh
        x1 = X_pts[:, :-1]
        y1 = Y_pts[:, :-1]
        x2 = X_pts[:, 1:]
        y2 = Y_pts[:, 1:]
        segs = np.stack([x1, y1, x2, y2], axis=-1).reshape(-1, 4)
        
        # Glow pass (phosphor halo)
        py5.stroke(*ch["col_glow"])
        py5.stroke_weight(ch["sw_g"])
        py5.lines(segs)
        
        # Core beam
        py5.stroke(*ch["col_core"])
        py5.stroke_weight(ch["sw_c"])
        py5.lines(segs)

    # -------------------------------------------------------------
    # 2. Left: NTSC Vectorscope
    # -------------------------------------------------------------
    vec_cx, vec_cy = 340, 420
    py5.fill(8, 12, 18, 220)
    py5.stroke(25, 45, 65)
    py5.stroke_weight(3.0)
    py5.ellipse(vec_cx, vec_cy, 320, 320)
    py5.stroke(20, 35, 50, 150)
    py5.stroke_weight(1.5)
    py5.line(vec_cx - 150, vec_cy, vec_cx + 150, vec_cy)
    py5.line(vec_cx, vec_cy - 150, vec_cx, vec_cy + 150)
    for ang_t in [0.1, 0.45, 0.8, 1.2, 1.6, 2.0]:
        py5.ellipse(vec_cx + 105.0 * np.cos(ang_t * np.pi), vec_cy + 105.0 * np.sin(ang_t * np.pi), 18, 18)
    py5.no_fill()
    py5.stroke(40, 240, 140, 190)
    py5.stroke_weight(2.4)
    py5.begin_shape()
    r_vec = 95.0 + 30.0 * np.sin(5.0 * ANGLES_VEC + TAU * t_val)
    for a, r in zip(ANGLES_VEC, r_vec):
        py5.vertex(vec_cx + r * np.cos(a), vec_cy + r * np.sin(a))
    py5.end_shape(py5.CLOSE)
    py5.fill(100, 180, 160)
    py5.text_size(20)
    py5.text_align(py5.CENTER, py5.TOP)
    py5.text("NTSC VECTORSCOPE", vec_cx, vec_cy + 175)

    # -------------------------------------------------------------
    # 3. Right: XY Oscilloscope (Lissajous 3:2)
    # -------------------------------------------------------------
    osc_cx, osc_cy = WIDTH - 340, 420
    py5.fill(8, 12, 18, 220)
    py5.stroke(25, 45, 65)
    py5.stroke_weight(3.0)
    py5.ellipse(osc_cx, osc_cy, 320, 320)
    py5.stroke(20, 35, 50, 150)
    py5.line(osc_cx - 150, osc_cy, osc_cx + 150, osc_cy)
    py5.line(osc_cx, osc_cy - 150, osc_cx, osc_cy + 150)
    for r_o in [55, 110]:
        py5.ellipse(osc_cx, osc_cy, r_o * 2, r_o * 2)
    py5.stroke(255, 255, 255, 230)
    py5.stroke_weight(2.4)
    py5.begin_shape()
    for al in ANGLES_LISS:
        py5.vertex(osc_cx + 115.0 * np.sin(3.0 * al + TAU * t_val),
                   osc_cy + 115.0 * np.sin(2.0 * al))
    py5.end_shape(py5.CLOSE)
    py5.fill(100, 180, 160)
    py5.text("XY OSCILLOSCOPE 3:2", osc_cx, osc_cy + 175)

    # -------------------------------------------------------------
    # 4. Bottom Waveform Monitor (A-Scan Deflection)
    # -------------------------------------------------------------
    wfm_y = HEIGHT - 220
    py5.stroke(20, 35, 50, 120)
    py5.stroke_weight(2.0)
    py5.line(CX - 620, wfm_y, CX + 620, wfm_y)
    py5.stroke(245, 200, 50, 190)
    py5.stroke_weight(2.5)
    py5.no_fill()
    py5.begin_shape()
    for wx, n_w, env_w in zip(X_WAVEFORM, NORM_W, WAVEFORM_ENV):
        wy = wfm_y - 55.0 * np.sin(4.0 * TAU * n_w + TAU * t_val) * env_w
        py5.vertex(wx, wy)
    py5.end_shape()
    py5.fill(180, 160, 80)
    py5.text_size(20)
    py5.text("WAVEFORM MONITOR (IRE 100)", CX, wfm_y + 28)

    # Save current frame
    frame_path = os.path.join(FRAMES_DIR, f"frame_{current_frame:04d}.png")
    py5.save_frame(frame_path)
    
    # Save preview image at frame 180
    if current_frame == 180 or (current_frame == 1 and not os.path.exists(PREVIEW_PNG)):
        py5.save_frame(PREVIEW_PNG)
        print(f"[{WORK_NAME}] Saved preview image: {PREVIEW_PNG}")

    current_frame += 1
    
    if current_frame % 60 == 0 or current_frame == TOTAL_FRAMES:
        elapsed = time.time() - start_time
        fps_calc = current_frame / max(0.1, elapsed)
        eta = (TOTAL_FRAMES - current_frame) / max(0.01, fps_calc)
        print(f"[{WORK_NAME}] Frame {current_frame:03d}/{TOTAL_FRAMES} ({current_frame/TOTAL_FRAMES*100:.1f}%) | Speed: {fps_calc:.2f} fps | ETA: {eta:.1f}s")
    
    if current_frame >= TOTAL_FRAMES:
        finish_and_encode()

def finish_and_encode():
    global start_time
    total_elapsed = time.time() - start_time
    print(f"[{WORK_NAME}] All {TOTAL_FRAMES} frames rendered in {total_elapsed:.1f}s (~{TOTAL_FRAMES/total_elapsed:.2f} fps).")
    print(f"[{WORK_NAME}] Compiling 4K 60fps MP4 with FFmpeg...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        OUTPUT_MP4
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=py5.sys.stderr)
        mp4_size_mb = os.path.getsize(OUTPUT_MP4) / (1024 * 1024)
        print(f"[{WORK_NAME}] Successfully generated output.mp4 ({mp4_size_mb:.2f} MB)")
    except Exception as e:
        print(f"[{WORK_NAME}] Error encoding video: {e}")
    finally:
        if os.path.exists(FRAMES_DIR):
            shutil.rmtree(FRAMES_DIR)
            print(f"[{WORK_NAME}] Cleaned up temporary frames directory.")
            
    print(f"[{WORK_NAME}] Complete!")
    os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
