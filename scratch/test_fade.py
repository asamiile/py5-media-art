import py5
import numpy as np

def setup():
    py5.size(400, 400, py5.P2D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 15)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke(200, 100, 100, 50)
    py5.stroke_weight(5)
    py5.point(200 + 100 * np.cos(py5.frame_count * 0.1), 200 + 100 * np.sin(py5.frame_count * 0.1))
    
    if py5.frame_count == 100:
        py5.save_frame("test.png")
        py5.exit_sketch()

py5.run_sketch()
