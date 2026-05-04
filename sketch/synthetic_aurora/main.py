import py5
import numpy as np
from pathlib import Path

# Configuration
WIDTH, HEIGHT = 1920, 1080
FPS = 60
DURATION = 10
TOTAL_FRAMES = DURATION * FPS

class SyntheticAurora:
    def __init__(self):
        self.t = 0
        self.num_layers = 15
        self.points_per_layer = 100
        
    def draw_curtain(self, layer_idx, offset_x, color_shift):
        # Calculate noise-driven path for this curtain
        py5.begin_shape()
        py5.no_fill()
        
        # Color based on layer and shift
        hue = (160 + layer_idx * 15 + color_shift) % 360
        py5.stroke(hue, 80, 100, 40)
        py5.stroke_weight(1.5)
        
        for i in range(self.points_per_layer):
            y = py5.remap(i, 0, self.points_per_layer - 1, 100, HEIGHT - 100)
            
            # Noise-driven horizontal displacement
            n = py5.noise(layer_idx * 0.1, i * 0.05, self.t * 0.5)
            x = WIDTH * 0.2 + offset_x + n * 400 * py5.sin(y * 0.002 + self.t)
            
            # Add secondary wave
            x += py5.sin(y * 0.01 + self.t * 2) * 50
            
            py5.vertex(x, y)
        py5.end_shape()

    def draw(self):
        self.t += 0.015
        
        # Starfield
        py5.no_stroke()
        for _ in range(50):
            sx = py5.random(WIDTH)
            sy = py5.random(HEIGHT)
            py5.fill(255, py5.random(50, 150))
            py5.circle(sx, sy, py5.random(1, 2))

        # Render curtains with chromatic aberration
        for j in range(self.num_layers):
            # Red shift
            self.draw_curtain(j, -5, -10)
            # Green/Main
            self.draw_curtain(j, 0, 0)
            # Blue shift
            self.draw_curtain(j, 5, 10)

sketch_obj = SyntheticAurora()
frames_path = Path(__file__).parent / "frames"

def setup():
    py5.size(WIDTH, HEIGHT, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.frame_rate(FPS)
    py5.background(240, 100, 5) # Deep night sky
    frames_path.mkdir(parents=True, exist_ok=True)

def draw():
    # Persistence for glow and movement trails
    py5.fill(240, 100, 5, 15) # Subtle fade
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Additive blending simulation via transparency
    py5.blend_mode(py5.ADD)
    sketch_obj.draw()
    py5.blend_mode(py5.BLEND)
    
    # Save frames
    if py5.frame_count <= TOTAL_FRAMES:
        py5.save_frame(str(frames_path / f"frame_{py5.frame_count:04d}.png"))
        if py5.frame_count == TOTAL_FRAMES // 2:
            py5.save(str(Path(__file__).parent / "preview_p1.png"))
    else:
        # Export video
        input_pattern = str(frames_path / "frame_%04d.png")
        output_video = str(Path(__file__).parent / "output.mp4")
        import subprocess
        cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", input_pattern, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", output_video]
        subprocess.run(cmd, check=True)
        py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
