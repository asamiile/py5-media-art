from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FRAME = 60
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Color palette
DEEP_CHARCOAL = (20, 20, 25)
ELECTRIC_BLUE = (0, 150, 255)
WARM_MAGENTA = (255, 50, 150)
BRIGHT_CYAN = (0, 255, 255)
SOFT_PURPLE = (150, 100, 200)
GOLDEN_ORANGE = (255, 165, 0)

# Sound wave parameters
NUM_WAVES = 8
BASE_FREQUENCY = 0.02
HARMONIC_MULTIPLIERS = [1, 2, 3, 4, 5, 6, 8, 10]

np.random.seed(None)


def generate_waveform(x, frequency, amplitude, phase, harmonics):
    """Generate a complex waveform with harmonics."""
    y = 0
    for h in harmonics:
        harmonic_freq = frequency * h
        harmonic_amp = amplitude / h
        y += harmonic_amp * np.sin(harmonic_freq * x + phase)
    return y


def draw_sound_wave(y_offset, frequency, amplitude, phase, color, harmonics, thickness):
    """Draw a single sound wave with harmonics."""
    points = []
    for x in range(0, int(SIZE[0]) + 1, 2):
        wave_y = generate_waveform(x, frequency, amplitude, phase, harmonics)
        points.append((x, y_offset + wave_y))

    if len(points) > 1:
        py5.stroke_weight(thickness)
        py5.stroke(*color, 180)
        py5.no_fill()
        py5.begin_shape()
        for px, py in points:
            py5.vertex(px, py)
        py5.end_shape()


def draw_frequency_bars():
    """Draw frequency spectrum bars at the bottom."""
    num_bars = 64
    bar_width = SIZE[0] / num_bars

    for i in range(num_bars):
        x = i * bar_width
        # Simulate frequency spectrum with noise
        height = np.random.uniform(20, 150) * np.sin(i * 0.1 + np.random.uniform(0, np.pi))

        # Color based on frequency
        freq_ratio = i / num_bars
        if freq_ratio < 0.33:
            color = ELECTRIC_BLUE
        elif freq_ratio < 0.66:
            color = WARM_MAGENTA
        else:
            color = BRIGHT_CYAN

        py5.no_stroke()
        py5.fill(*color, 150)
        py5.rect(x, SIZE[1] - height, bar_width - 2, height)


def draw_circular_waves():
    """Draw circular sound waves radiating from center."""
    center_x, center_y = SIZE[0] / 2, SIZE[1] / 2
    num_circles = 12

    for i in range(num_circles):
        radius = 30 + i * 40
        alpha = int(200 * (1 - i / num_circles))

        # Color variation
        if i % 3 == 0:
            color = ELECTRIC_BLUE
        elif i % 3 == 1:
            color = WARM_MAGENTA
        else:
            color = BRIGHT_CYAN

        py5.no_fill()
        py5.stroke_weight(2)
        py5.stroke(*color, alpha)
        py5.circle(center_x, center_y, radius * 2)


def draw_spectrogram():
    """Draw a spectrogram-style visualization."""
    num_rows = 20
    row_height = SIZE[1] / num_rows

    for row in range(num_rows):
        for col in range(0, int(SIZE[0]), 10):
            # Simulate spectrogram intensity
            intensity = np.random.uniform(0, 1)

            # Color based on intensity
            if intensity > 0.7:
                color = BRIGHT_CYAN
            elif intensity > 0.4:
                color = ELECTRIC_BLUE
            else:
                color = DEEP_CHARCOAL

            alpha = int(intensity * 100)
            py5.no_stroke()
            py5.fill(*color, alpha)
            py5.rect(col, row * row_height, 8, row_height - 1)


def setup():
    py5.size(*SIZE)
    py5.background(*DEEP_CHARCOAL)


def draw():
    # Draw spectrogram background
    draw_spectrogram()

    # Draw circular waves
    draw_circular_waves()

    # Draw horizontal sound waves
    for i in range(NUM_WAVES):
        y_offset = SIZE[1] * 0.3 + i * (SIZE[1] * 0.4 / NUM_WAVES)
        frequency = BASE_FREQUENCY * HARMONIC_MULTIPLIERS[i % len(HARMONIC_MULTIPLIERS)]
        amplitude = np.random.uniform(30, 60)
        phase = np.random.uniform(0, 2 * np.pi)

        # Color variation
        if i % 3 == 0:
            color = ELECTRIC_BLUE
        elif i % 3 == 1:
            color = WARM_MAGENTA
        else:
            color = BRIGHT_CYAN

        harmonics = HARMONIC_MULTIPLIERS[:np.random.randint(2, 5)]
        thickness = np.random.randint(2, 4)

        draw_sound_wave(y_offset, frequency, amplitude, phase, color, harmonics, thickness)

    # Draw frequency bars
    draw_frequency_bars()

    maybe_save_exit_on_frame(PREVIEW_FRAME, SKETCH_DIR)


if __name__ == '__main__':
    py5.run_sketch()
