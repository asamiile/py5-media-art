import py5
import numpy as np

W, H = 1920, 1080
GW, GH = 400, 225
MESH_SCALE_X = 4.0
MESH_SCALE_Y = 2.8

def setup():
    py5.size(W, H, py5.P3D)
    py5.background(0)
    
    # py5.camera(
    #     W/2, -H*0.1, W*0.65,
    #     W/2, H/2, 0,
    #     0, 1, 0
    # )
    
    py5.translate(W/2, H/2, 0)
    py5.rotate_x(0.55) # perspective tilt
    py5.translate(-W/2, -H/2, 0)

    py5.ambient_light(30, 25, 45)
    py5.directional_light(180, 170, 200, 0.3, 0.6, -0.7)

    py5.no_stroke()
    
    center_x = W / 2
    center_y = H / 2

    for row in range(GH - 1):
        py5.begin_shape(py5.QUAD_STRIP)
        for col in range(GW):
            for r in [row, row + 1]:
                x = (col - GW / 2) * MESH_SCALE_X + center_x
                z = (r - GH / 2) * MESH_SCALE_Y
                y_val = center_y 
                
                py5.fill(200, 100, 100, 230)
                py5.vertex(x, y_val, z)
        py5.end_shape()
        
    py5.save_frame("test.png")
    py5.exit_sketch()

py5.run_sketch()
