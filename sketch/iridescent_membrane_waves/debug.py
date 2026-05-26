import numpy as np

GW, GH = 400, 225
DAMPING = 0.997
WAVE_SPEED = 0.42
SUBSTEPS = 3

u_curr = np.zeros((GH, GW), dtype=np.float64)
u_prev = np.zeros((GH, GW), dtype=np.float64)

yy, xx = np.mgrid[:GH, :GW]
u_curr = 0.15 * np.sin(xx * 0.05) * np.sin(yy * 0.07)
u_prev = u_curr.copy()

for fc in range(60):
    for _ in range(SUBSTEPS):
        lap = (
            np.roll(u_curr, 1, axis=0) + np.roll(u_curr, -1, axis=0) +
            np.roll(u_curr, 1, axis=1) + np.roll(u_curr, -1, axis=1) -
            4.0 * u_curr
        )
        u_next = 2.0 * u_curr - u_prev + WAVE_SPEED * lap
        u_next *= DAMPING
        edge = 15
        fade = np.ones((GH, GW), dtype=np.float64)
        for i in range(edge):
            f = i / edge
            fade[i, :] *= f
            fade[GH - 1 - i, :] *= f
            fade[:, i] *= f
            fade[:, GW - 1 - i] *= f
        u_next *= fade
        u_prev = u_curr.copy()
        u_curr = u_next
print("min:", u_curr.min(), "max:", u_curr.max())
