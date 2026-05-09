from pathlib import Path
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# グリッドの解像度（100x100 = 1万ポリゴン）
# 高速化とディテールのバランス
RES = 100

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 10, 15) # Deep Charcoal
    
    # カメラ設定
    py5.camera(SIZE[0]*0.8, -SIZE[1]*0.6, SIZE[0]*0.8, 0, 0, 0, 0, 1, 0)
    
    # ライティング（真珠のような光沢）
    py5.ambient_light(40, 40, 60)
    py5.point_light(255, 255, 255, 500, -800, 500)
    py5.specular(255, 255, 255)
    py5.shininess(20.0)

    # 圧縮パラメータ（時間経過で座屈が激しくなる）
    progress = py5.frame_count / TOTAL_FRAMES
    compression = py5.remap(progress, 0, 1, 0, 1)
    
    # メッシュ描画
    w = SIZE[0] * 1.5
    h = SIZE[1] * 1.5
    step_w = w / RES
    step_h = h / RES
    
    py5.begin_shape(py5.QUADS)
    for i in range(RES - 1):
        for j in range(RES - 1):
            x0 = -w/2 + i * step_w
            z0 = -h/2 + j * step_h
            x1 = x0 + step_w
            z1 = z0 + step_h
            
            # 座標計算（高速化のため一括計算したいが、py5のループ内では個別に行う）
            # 座屈ノイズ（複数の周波数を重ねる）
            def get_height(x, z):
                amp = 150 * compression
                # 基底のうねり
                v = py5.os_noise(x * 0.002, z * 0.002, py5.frame_count * 0.01)
                # 高周波の座屈（シワ）
                v += 0.4 * py5.os_noise(x * 0.01, z * 0.01, py5.frame_count * 0.02) * compression
                return v * amp

            y00 = get_height(x0, z0)
            y10 = get_height(x1, z0)
            y11 = get_height(x1, z1)
            y01 = get_height(x0, z1)
            
            # 色の計算（法線に基づいた干渉色）
            # 近似的な法線勾配で色を変化させる
            diff = abs(y00 - y10) + abs(y00 - y01)
            hue_offset = py5.remap(diff, 0, 20, 0, 60)
            
            py5.fill(220 + hue_offset, 200, 230 + hue_offset) # Pearl base
            py5.vertex(x0, y00, z0)
            py5.vertex(x1, y10, z0)
            
            # 尾根の部分にシアンの発光
            if diff > 10 * compression:
                py5.fill(200, 255, 255, 150) # Cyan accent
            
            py5.vertex(x1, y11, z1)
            py5.vertex(x0, y01, z1)
    py5.end_shape()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count % 100 == 0:
        print(f"Progress: {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        print("Exporting video...")
        py5.exit_sketch()
        subprocess.run(["ffmpeg", "-y", "-r", "60", "-i", str(FRAMES_DIR / "frame-%04d.png"),
                       "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-preset", "faster",
                       str(SKETCH_DIR / f"{WORK_NAME}.mp4")], check=True)
        subprocess.run(["cp", str(FRAMES_DIR / f"frame-{TOTAL_FRAMES//2:04d}.png"), 
                       str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        print("Done.")

py5.run_sketch()
