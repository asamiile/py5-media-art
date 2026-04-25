from py5 import *

def setup():
    size(400, 400)
    rect_mode(CENTER)

def draw():
    background(240)
    fill(50, 150, 255)
    # マウスの位置に合わせて四角形を描画
    rect(mouse_x, mouse_y, 50, 50)

if __name__ == "__main__":
    run_sketch()