import py5

def setup():
    py5.size(200, 200, py5.P2D)
    py5.rect(50, 50, 100, 100)
    py5.save_frame("test_frame_p2d.png")
    py5.exit_sketch()

py5.run_sketch()
