import py5
import numpy as np
from PIL import Image

# Resolution: Preview 1920×1080 | Output 3840×2160
SIZE = (1920, 1080)

def setup():
    py5.size(SIZE[0], SIZE[1], py5.P2D)
    py5.background(8, 8, 26)  # Deep Indigo
    py5.no_loop()

def draw():
    # Grid coordinates
    x = np.linspace(0, SIZE[0], SIZE[0])
    y = np.linspace(0, SIZE[1], SIZE[1])
    X, Y = np.meshgrid(x, y)
    
    # Wave sources (5-8)
    num_sources = 8
    sources = np.random.uniform(0, [SIZE[0], SIZE[1]], (num_sources, 2))
    # Varied frequencies for more complex interference
    frequencies = np.random.uniform(0.02, 0.08, num_sources)
    phases = np.random.uniform(0, 2 * np.pi, num_sources)
    # Varied amplitudes
    amplitudes = np.random.uniform(0.5, 1.5, num_sources)
    
    # Combined field
    field = np.zeros_like(X)
    for i in range(num_sources):
        dist = np.sqrt((X - sources[i, 0])**2 + (Y - sources[i, 1])**2)
        field += amplitudes[i] * np.sin(dist * frequencies[i] + phases[i])
    
    # Normalize field to [0, 1]
    field = (field - field.min()) / (field.max() - field.min())
    
    # Non-linear mapping to create sharp echoes (interference fringes)
    echo1 = np.abs(np.sin(field * 30 * np.pi))
    echo2 = np.abs(np.sin(field * 15 * np.pi + np.pi/4))
    echo_field = (echo1**6 * 0.7 + echo2**10 * 0.3)
    
    # Create RGB buffers
    # Base gradient across the field
    r_base = field * 255
    g_base = (1 - np.abs(field - 0.5) * 2) * 255
    b_base = (1 - field) * 255
    
    # Apply echo field as mask and intensity
    r_buf = (r_base * echo_field).astype(np.uint8)
    g_buf = (g_base * echo_field).astype(np.uint8)
    b_buf = (b_base * echo_field).astype(np.uint8)
    
    # Add background for depth
    bg_r, bg_g, bg_b = 8, 8, 26
    r_buf = np.maximum(r_buf, (bg_r * (1 - echo_field)).astype(np.uint8))
    g_buf = np.maximum(g_buf, (bg_g * (1 - echo_field)).astype(np.uint8))
    b_buf = np.maximum(b_buf, (bg_b * (1 - echo_field)).astype(np.uint8))
    
    # RGB image data
    img_data = np.stack([r_buf, g_buf, b_buf], axis=-1)
    
    # Handle Retina / Pixel Density and 4-channel requirement
    py5.load_np_pixels()
    h, w, c = py5.np_pixels.shape
    
    # Resize to actual pixel dimensions if needed
    if h != SIZE[1] or w != SIZE[0]:
        img = Image.fromarray(img_data)
        img = img.resize((w, h), Image.LANCZOS)
        img_data = np.array(img)
    
    # Add Alpha channel if py5 expects 4 channels
    if c == 4:
        alpha = np.full((h, w, 1), 255, dtype=np.uint8)
        img_data = np.concatenate([img_data, alpha], axis=-1)
    
    py5.np_pixels[:] = img_data
    py5.update_np_pixels()
    
    py5.save("preview.png")
    print("Artwork saved to preview.png")
    py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
