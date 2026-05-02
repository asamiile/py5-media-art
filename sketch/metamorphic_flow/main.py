import py5
import numpy as np
from pathlib import Path

# Constants
SIZE = (1920, 1080)  # Preview resolution
# SIZE = (3840, 2160)  # High resolution for final output
OUTPUT_DIR = Path(__file__).parent

def setup():
    py5.size(*SIZE)
    py5.background(10)
    py5.no_loop()

def draw():
    # Load pixels as numpy array
    py5.load_np_pixels()
    
    # Grid coordinates
    h, w = py5.np_pixels.shape[:2]
    y, x = np.ogrid[:h, :w]
    xf = x.astype(float) / w
    yf = y.astype(float) / h
    
    # Scale factors
    scale = 3.0
    warp_strength = 0.6
    
    print("Generating geological strata...")
    
    def get_noise_field(octaves=4, freq=2.0):
        field = np.zeros((h, w))
        f = freq
        a = 1.0
        for _ in range(octaves):
            # Use sine/cosine sum for fast "noise"
            phase = py5.random(1000)
            angle = py5.random(py5.TWO_PI)
            cx, cy = np.cos(angle), np.sin(angle)
            field += a * np.sin((xf * cx + yf * cy) * f * 10 + phase)
            f *= 2.1
            a *= 0.5
        return field

    # Generate domain warping fields
    g1 = get_noise_field(octaves=4, freq=1.2)
    
    # Main value field with warped coordinates
    # v = f(p + g(p))
    val = get_noise_field(octaves=8, freq=0.5) + warp_strength * g1
    
    # Normalize
    val = (val - val.min()) / (val.max() - val.min())
    
    # Color mapping (Geological palette)
    # Obsidian, Slate, Sienna, Ochre, Gold
    palette = [
        (10, 12, 15),    # Deeper Obsidian
        (35, 45, 60),    # Slate Blue
        (130, 70, 50),   # Warm Sienna
        (190, 140, 50),  # Bright Ochre
        (210, 170, 70),  # Pyrite Gold
        (230, 225, 210)  # Quartz White
    ]
    
    # Interpolate colors
    pixels = np.zeros((h, w, 3))
    num_colors = len(palette)
    for i in range(num_colors - 1):
        c1 = np.array(palette[i])
        c2 = np.array(palette[i+1])
        mask = (val >= i/(num_colors-1)) & (val < (i+1)/(num_colors-1))
        t = (val[mask] - i/(num_colors-1)) * (num_colors - 1)
        pixels[mask] = c1 + t[:, np.newaxis] * (c2 - c1)
    
    # Handle the very last edge
    pixels[val >= 1.0] = np.array(palette[-1])
    
    # Add high-frequency "veins" - Softened
    veins = get_noise_field(octaves=3, freq=15.0)
    veins = np.abs(veins)
    vein_mask = veins > 2.0
    # Blend veins more naturally
    pixels[vein_mask] = pixels[vein_mask] * 0.7 + np.array([255, 255, 240]) * 0.3
    
    # Add subtle stone grain
    grain = np.random.normal(0, 5, (h, w, 3))
    pixels = np.clip(pixels + grain, 0, 255)
    
    # Apply to screen
    py5.np_pixels[:, :, :3] = pixels.astype(np.uint8)
    py5.update_np_pixels()
    
    # Save preview
    py5.save_frame(str(OUTPUT_DIR / "preview.png"))
    print(f"Saved preview to {OUTPUT_DIR / 'preview.png'}")

if __name__ == "__main__":
    py5.run_sketch()
