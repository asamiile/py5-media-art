import py5

def setup():
    py5.size(800, 600)
    print("Size set")
    py5.pixel_density(1)
    py5.pixel_density(1)
    print("Pixel density set")

def draw():
    print("Draw frame", py5.frame_count)
    py5.background(0)
    py5.exit_sketch()

py5.run_sketch()
