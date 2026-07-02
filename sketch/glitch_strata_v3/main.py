import sys
from pathlib import Path
import subprocess
import numpy as np
import py5

# Resolve project root and append to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes
from lib.safety import apply_anti_flicker_filter

# Sketch Directory and Naming Conventions
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"

# Animation parameters
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"

# Size parameters
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Pre-defined base coordinates for strata (static reference)
NUM_STRATA = 28
np.random.seed(42)  # Seed only the initial random division structure, keep dynamic variations unseeded
BASE_Y = np.sort(np.random.rand(NUM_STRATA))
np.random.seed(None)  # Reset seed for unseeded variations in run-time

def setup():
    py5.size(*SIZE)
    py5.background(10, 10, 12)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)
    print(f"[{WORK_NAME}] Initialized. Rendering {TOTAL_FRAMES} frames at {SIZE[0]}x{SIZE[1]}...")

def draw():
    frame = py5.frame_count
    t_val = frame / FPS

    # Load pixels as numpy array for heavy manipulation
    py5.load_np_pixels()
    h_px, w_px = py5.np_pixels.shape[:2]

    # Dynamic color palette (Obsidian, Golds, Amethysts, Magentas, Cobalts, Steel)
    palette = [
        np.array([8, 8, 10]),       # 0: Obsidian
        np.array([218, 165, 32]),   # 1: Goldenrod / Deep Gold
        np.array([255, 223, 0]),    # 2: Bright Gold
        np.array([123, 44, 191]),   # 3: Royal Amethyst
        np.array([219, 39, 119]),   # 4: Cyber Magenta
        np.array([37, 99, 235]),    # 5: Cobalt Blue
        np.array([160, 165, 170]),  # 6: Steel/Silver
        np.array([255, 239, 204]),  # 7: Pale Amber
        np.array([30, 30, 36])      # 8: Dark Shadow
    ]

    # 1. Update Strata boundaries with slow harmonic wiggling
    y_coords = np.zeros(NUM_STRATA + 2, dtype=np.int32)
    y_coords[0] = 0
    y_coords[-1] = h_px
    for i in range(NUM_STRATA):
        # Wiggle based on time and index
        wiggle = 0.02 * np.sin(t_val * 1.5 + i * 0.8) * h_px
        pos = int(BASE_Y[i] * h_px + wiggle)
        y_coords[i+1] = np.clip(pos, 0, h_px)
    y_coords = np.sort(y_coords)

    # 2. Render Stratum Tapestry
    for i in range(len(y_coords) - 1):
        y_start = y_coords[i]
        y_end = y_coords[i+1]
        stratum_h = y_end - y_start
        if stratum_h <= 0:
            continue

        # Deterministic style/seed index based on stratum index
        style_val = (np.sin(i * 12.3) + 1.0) * 0.5
        
        # Color rotation / shift based on time
        c_shift = (frame // 12 + i) % len(palette)
        c_idx1 = int((style_val * len(palette) + c_shift) % len(palette))
        c_idx2 = int((style_val * 7.9 + c_shift * 2.3) % len(palette))
        
        # Ensure we don't always pick black as dominant color for strata
        if c_idx1 == 0 and style_val < 0.8:
            c_idx1 = 2
        
        c1 = palette[c_idx1].copy()
        c2 = palette[c_idx2].copy()

        # Dynamic color pulsing
        pulse1 = 0.5 + 0.5 * np.sin(t_val * 2.0 + i)
        pulse2 = 0.5 + 0.5 * np.cos(t_val * 1.7 + i * 1.3)
        
        # Inject vivid HSB shifts over time (adds "more color")
        c1[0] = int(np.clip(c1[0] + 30 * np.sin(t_val * 3.0), 0, 255))
        c1[1] = int(np.clip(c1[1] + 30 * np.cos(t_val * 2.5), 0, 255))
        c2[2] = int(np.clip(c2[2] + 40 * np.sin(t_val * 2.0), 0, 255))

        if style_val < 0.35:
            # Pattern 1: Noisy Gradient & Horizontal Tearing
            noise_scale = 0.05 + 0.03 * np.sin(i * 0.5)
            for y in range(y_start, y_end):
                t = (y - y_start) / stratum_h
                base_col = c1 * (1 - t) + c2 * t
                
                # Time-varying horizontal tear displacement
                noise_val = py5.os_noise(y * noise_scale, t_val * 1.2)
                offset = int((noise_val - 0.5) * (w_px // 6))
                
                row = np.tile(base_col, (w_px, 1))
                # Add horizontal high-frequency noise
                row_noise = np.random.normal(0, 4 * pulse1, (w_px, 3))
                row = np.clip(row + row_noise, 0, 255)
                # Shift row
                row = np.roll(row, offset, axis=0)
                py5.np_pixels[y, :, :3] = row.astype(np.uint8)

        elif style_val < 0.7:
            # Pattern 2: Dynamic Digital Blocks with blocky shift
            block_w = int(20 + 60 * style_val)
            # Make block pattern slide horizontally over time
            x_shift = int(t_val * 120 * (1.0 if i % 2 == 0 else -1.0))
            
            for x in range(0, w_px, block_w):
                # Pseudo-random choice per block, animated
                choice = py5.os_noise(x * 0.01 + x_shift * 0.005, i * 0.5)
                
                if choice > 0.4:
                    col = c1 if choice > 0.65 else c2
                    # Random luxury accents (magenta, bright gold, white/silver)
                    if choice > 0.85:
                        col = palette[2]  # Bright Gold
                    elif choice > 0.93:
                        col = palette[4]  # Cyber Magenta
                    elif choice > 0.97:
                        col = palette[6]  # Steel/Silver
                    
                    actual_block_w = min(block_w, w_px - x)
                    target_x = (x + x_shift) % w_px
                    
                    # Split block drawing for wrap-around
                    if target_x + actual_block_w <= w_px:
                        py5.np_pixels[y_start:y_end, target_x:target_x+actual_block_w, :3] = col.astype(np.uint8)
                    else:
                        w1 = w_px - target_x
                        w2 = actual_block_w - w1
                        py5.np_pixels[y_start:y_end, target_x:, :3] = col.astype(np.uint8)
                        py5.np_pixels[y_start:y_end, :w2, :3] = col.astype(np.uint8)
                else:
                    actual_block_w = min(block_w, w_px - x)
                    target_x = (x + x_shift) % w_px
                    col = palette[0]  # Obsidian base
                    if target_x + actual_block_w <= w_px:
                        py5.np_pixels[y_start:y_end, target_x:target_x+actual_block_w, :3] = col.astype(np.uint8)
                    else:
                        w1 = w_px - target_x
                        w2 = actual_block_w - w1
                        py5.np_pixels[y_start:y_end, target_x:, :3] = col.astype(np.uint8)
                        py5.np_pixels[y_start:y_end, :w2, :3] = col.astype(np.uint8)

        else:
            # Pattern 3: High-frequency Shiver & Jitter
            for y in range(y_start, y_end):
                # High freq shivering displacement
                offset = int(np.sin(y * 0.2 + t_val * 45) * (w_px // 20) * pulse2)
                col = c1 if py5.os_noise(y * 0.05, t_val) > 0.3 else palette[5]  # Cobalt highlight
                
                row = np.tile(col, (w_px, 1))
                # Stochastic modular color inversion
                if py5.os_noise(t_val * 5, y * 0.1) > 0.88:
                    row = (255 - row) % 255
                    
                row = np.roll(row, offset, axis=0)
                py5.np_pixels[y, :, :3] = row.astype(np.uint8)

    # 3. Post-Process advanced glitch overlays
    
    # Tracking Error: Large horizontal slice tears randomly
    if py5.os_noise(t_val * 8, 42) > 0.75:
        slice_y = int(py5.os_noise(t_val * 3.5, 12) * h_px)
        slice_h = int(20 + 100 * py5.os_noise(t_val * 9.2, 5))
        slice_y_end = min(slice_y + slice_h, h_px)
        slice_shift = int((py5.os_noise(t_val * 15, 8) - 0.5) * (w_px // 2.5))
        py5.np_pixels[slice_y:slice_y_end, :, :3] = np.roll(
            py5.np_pixels[slice_y:slice_y_end, :, :3], slice_shift, axis=1
        )
        # Tint tracking slice with cyber magenta or cobalt
        tint = palette[4] if py5.os_noise(t_val * 20, 0) > 0.5 else palette[3]
        py5.np_pixels[slice_y:slice_y_end, :, :3] = (
            py5.np_pixels[slice_y:slice_y_end, :, :3] * 0.6 + tint * 0.4
        ).astype(np.uint8)

    # Dynamic Thin Vertical "Data Spikes"
    num_spikes = 12 + int(8 * np.sin(t_val * 4.0))
    for s in range(num_spikes):
        x_base = int(py5.os_noise(s * 15.3, t_val * 0.4) * w_px)
        spike_w = int(1 + 3 * py5.os_noise(s * 9.8, t_val * 3.0))
        col_idx = int((s + frame // 30) % len(palette))
        if col_idx == 0:
            col_idx = 1
        col = palette[col_idx]
        
        actual_spike_w = min(spike_w, w_px - x_base)
        if actual_spike_w > 0:
            py5.np_pixels[:, x_base:x_base+actual_spike_w, :3] = col.astype(np.uint8)

    # Chromatic Aberration / Vectorized RGB Channel Split (Ultimate Glitch Feel)
    # Splits the red and blue channels horizontally based on motion/time
    split_mag = int(12 * py5.os_noise(t_val * 6.5, 7.8) * np.sin(t_val * 4.5))
    if abs(split_mag) > 1:
        py5.np_pixels[:, :, 0] = np.roll(py5.np_pixels[:, :, 0], split_mag, axis=1)   # Red channel
        py5.np_pixels[:, :, 2] = np.roll(py5.np_pixels[:, :, 2], -split_mag, axis=1)  # Blue channel

    # Moving scanlines (retro analogue tracking)
    scan_y = int((t_val * 240) % h_px)
    for y in range(0, h_px, 3):
        weight = 0.82 if abs(y - scan_y) < 150 else 0.92
        py5.np_pixels[y, :, :3] = (py5.np_pixels[y, :, :3] * weight).astype(np.uint8)

    # Voltage drop: random periodic dark frames
    if py5.os_noise(t_val * 2.0, 99) > 0.94:
        py5.np_pixels[:, :, :3] = (py5.np_pixels[:, :, :3] * 0.4).astype(np.uint8)

    py5.update_np_pixels()

    # Save sequential frames for ffmpeg
    apply_anti_flicker_filter(0.5)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Auto-termination and video assembly
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"\n[{WORK_NAME}] Finished frame rendering. Compiling video with ffmpeg...")
        
        # 1. Assemble MP4 video
        video_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "8000k",
            str(video_path),
        ], check=True)
        print(f"[{WORK_NAME}] Successfully compiled: {video_path}")
        
        # 2. Extract Middle Frame as standard Preview Image
        mid_frame_num = TOTAL_FRAMES // 2
        mid_frame_path = FRAMES_DIR / f"frame-{mid_frame_num:04d}.png"
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        subprocess.run(["cp", str(mid_frame_path), str(preview_path)], check=True)
        print(f"[{WORK_NAME}] Saved preview frame {mid_frame_num} to {preview_path}")
        
        # 3. Clean up frames directory to save storage
        print(f"[{WORK_NAME}] Cleaning up raw frame files...")
        for frame_file in FRAMES_DIR.glob("frame-*.png"):
            frame_file.unlink()
        FRAMES_DIR.rmdir()
        print(f"[{WORK_NAME}] Cleanup complete.")

if __name__ == "__main__":
    py5.run_sketch()
