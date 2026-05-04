import py5
import numpy as np
from pathlib import Path

# Configuration
WIDTH, HEIGHT = 1080, 1080 # Square for better focus
FPS = 60
DURATION = 10
TOTAL_FRAMES = DURATION * FPS

class MetabolicGrowth:
    def __init__(self):
        self.t = 0
        self.sentence = "F"
        self.rules = {"F": "F[+F]F[-F][&F][^F]"} 
        self.length = 25 # Larger
        self.angle = py5.radians(22)
        
        # Generate L-System
        for _ in range(5): # Deeper
            self.generate()
            
    def generate(self):
        next_sentence = ""
        for char in self.sentence:
            next_sentence += self.rules.get(char, char)
        self.sentence = next_sentence

    def draw_grid(self):
        py5.stroke(200, 80, 40, 50)
        py5.stroke_weight(1)
        grid_size = 2000
        steps = 20
        for i in range(-steps, steps + 1):
            py5.line(i * grid_size/steps, 0, -grid_size, i * grid_size/steps, 0, grid_size)
            py5.line(-grid_size, 0, i * grid_size/steps, grid_size, 0, i * grid_size/steps)

    def render(self):
        py5.push_matrix()
        py5.translate(WIDTH // 2, HEIGHT * 0.9, -800)
        
        # Draw base grid
        py5.push_matrix()
        py5.translate(0, 50, 0)
        self.draw_grid()
        py5.pop_matrix()

        # Slow rotation
        py5.rotate_y(self.t * 0.3)
        
        stack_depth = 0
        max_depth = 5
        for char in self.sentence:
            if char == "F":
                # Branch
                weight = py5.remap(stack_depth, 0, max_depth, 6, 0.5)
                py5.stroke_weight(weight)
                
                # Glowing branch
                hue = (240 + stack_depth * 20) % 360
                py5.stroke(hue, 70, 100, 200)
                
                # Dynamic length (sway)
                l = self.length + py5.sin(self.t + stack_depth * 0.5) * 5
                py5.line(0, 0, 0, 0, -l, 0)
                py5.translate(0, -l, 0)
                
            elif char == "+": py5.rotate_z(self.angle + py5.sin(self.t) * 0.1)
            elif char == "-": py5.rotate_z(-self.angle - py5.sin(self.t) * 0.1)
            elif char == "&": py5.rotate_x(self.angle + py5.cos(self.t) * 0.1)
            elif char == "^": py5.rotate_x(-self.angle - py5.cos(self.t) * 0.1)
            elif char == "[": 
                py5.push_matrix()
                stack_depth += 1
            elif char == "]": 
                # Draw "bloom" at terminal nodes
                if stack_depth >= 4:
                    hue = (280 + py5.sin(self.t + stack_depth) * 40) % 360
                    py5.no_stroke()
                    py5.fill(hue, 80, 100, 150)
                    py5.push_matrix()
                    py5.sphere(3)
                    py5.pop_matrix()
                
                py5.pop_matrix()
                stack_depth -= 1
        
        py5.pop_matrix()

    def update(self):
        self.t += 0.02

sketch_obj = MetabolicGrowth()
frames_path = Path(__file__).parent / "frames"

def setup():
    py5.size(WIDTH, HEIGHT, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.frame_rate(FPS)
    py5.sphere_detail(8) # Optimization for complex trees

def draw():
    py5.background(240, 100, 5) # Deep night sky
    
    # Lighting
    py5.ambient_light(50, 50, 50)
    py5.directional_light(0, 0, 100, 0, 0, -1)
    py5.point_light(300, 50, 100, WIDTH/2, HEIGHT/2, 200)
    
    sketch_obj.update()
    sketch_obj.render()
    
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
