import py5
def setup():
    py5.size(200, 200, py5.P3D)
def draw():
    py5.background(255)
    py5.box(50)
    py5.load_np_pixels()
    print("pixels loaded", py5.np_pixels.std())
    py5.exit_sketch()
    import os
    os._exit(0)
py5.run_sketch()
