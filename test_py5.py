import py5

def setup():
    py5.size(200, 200)
    py5.rect(50, 50, 100, 100)
    py5.save_frame("test_frame.png")
    py5.exit_sketch()

py5.run_sketch()
