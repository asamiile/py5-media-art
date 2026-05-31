import py5
import numpy as np

lut = np.zeros(256, dtype=np.int32)

def setup():
    py5.size(200, 200)
    for i in range(256):
        lut[i] = py5.color(i, i, i)

def draw():
    py5.load_np_pixels()
    print("Shape:", py5.np_pixels.shape)
    print("Dtype:", py5.np_pixels.dtype)
    py5.np_pixels[:] = lut[128]
    py5.update_np_pixels()
    py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
