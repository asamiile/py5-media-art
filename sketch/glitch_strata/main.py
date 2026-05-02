import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE)
    py5.background(20, 20, 25)
    py5.no_loop()

def draw():
    h, w = SIZE[1], SIZE[0]
    
    # Load pixels as numpy array for heavy manipulation
    py5.load_np_pixels()
    h_px, w_px = py5.np_pixels.shape[:2]
    
    # 1. Base Stratification
    num_strata = 24
    y_coords = np.sort(np.random.randint(0, h_px, num_strata))
    y_coords = np.concatenate([[0], y_coords, [h_px]])
    
    # Palette
    colors = [
        [30, 30, 35],    # Charcoal
        [100, 100, 110], # Steel
        [0, 255, 180],   # Neon Mint
        [255, 0, 150],   # Electric Magenta
        [0, 150, 255],   # Cyber Blue
        [255, 255, 0]    # Warning Yellow
    ]
    
    print(f"Generating digital corruption at {w_px}x{h_px} pixels...")

    for i in range(len(y_coords) - 1):
        y_start = y_coords[i]
        y_end = y_coords[i+1]
        stratum_h = y_end - y_start
        if stratum_h <= 0: continue
        
        # Decide corruption style for this stratum
        style = py5.random(1)
        
        # Select primary colors for this stratum
        c_idx1 = int(py5.random(len(colors)))
        c_idx2 = int(py5.random(len(colors)))
        c1 = np.array(colors[c_idx1])
        c2 = np.array(colors[c_idx2])
        
        if style < 0.4:
            # Pattern: Noisy Gradient
            noise_scale = py5.random(0.01, 0.1)
            for y in range(y_start, y_end):
                t = (y - y_start) / stratum_h
                base_col = c1 * (1 - t) + c2 * t
                # Horizontal tear displacement
                offset = int(py5.os_noise(y * noise_scale, 0.0) * (w_px // 10))
                row = np.tile(base_col, (w_px, 1))
                # Add horizontal noise
                row_noise = np.random.normal(0, 5, (w_px, 3))
                row = np.clip(row + row_noise, 0, 255)
                # Shift row
                row = np.roll(row, offset, axis=0)
                py5.np_pixels[y, :, :3] = row.astype(np.uint8)
                
        elif style < 0.7:
            # Pattern: Digital Blocks
            block_w = int(py5.random(w_px // 100, w_px // 10))
            for x in range(0, w_px, block_w):
                if py5.random(1) > 0.3:
                    col = c1 if py5.random(1) > 0.5 else c2
                    # Randomly corrupt block color
                    if py5.random(1) > 0.8:
                        col = np.array([255, 255, 255])
                    actual_block_w = min(block_w, w_px - x)
                    py5.np_pixels[y_start:y_end, x:x+actual_block_w, :3] = col.astype(np.uint8)
                else:
                    actual_block_w = min(block_w, w_px - x)
                    py5.np_pixels[y_start:y_end, x:x+actual_block_w, :3] = colors[0]
                    
        else:
            # Pattern: High-freq jitter
            for y in range(y_start, y_end):
                offset = int(py5.random(-w_px//4, w_px//4))
                col = c1 if py5.random(1) > 0.2 else np.array([255, 255, 255])
                row = np.tile(col, (w_px, 1))
                # Modular corruption
                if py5.random(1) > 0.9:
                    row = (row * 1.5) % 255
                row = np.roll(row, offset, axis=0)
                py5.np_pixels[y, :, :3] = row.astype(np.uint8)

    # 2. Global Corruptions
    # Thin vertical "data spikes"
    for _ in range(12):
        x = int(py5.random(w_px))
        spike_w = int(py5.random(1, w_px // 200))
        col = np.array(colors[int(py5.random(2, len(colors)))])
        actual_spike_w = min(spike_w, w_px - x)
        py5.np_pixels[:, x:x+actual_spike_w, :3] = col.astype(np.uint8)
        
    # Scanline overlay
    for y in range(0, h_px, 3):
        py5.np_pixels[y, :, :3] = (py5.np_pixels[y, :, :3] * 0.8).astype(np.uint8)


    py5.update_np_pixels()
    
    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
