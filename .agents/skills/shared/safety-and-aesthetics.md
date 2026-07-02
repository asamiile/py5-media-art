# Safety and Aesthetics Guidelines

These guidelines balance visual safety (health considerations) with the freedom of artistic expression in generative art. These standards are based on findings from **neurophysiology**, **ergonomics**, and **broadcast engineering**.

## 1. Strict Avoidance (Hard Limits for Safety)
Absolute rules to prevent health risks such as "Photosensitive Epilepsy" (compliant with broadcast standards like ITU-R BT.1702).

- **Limit Severe Flashing (Flicker)**:
  Do not create **strong transitions in brightness more than 3 times per second (>3Hz)** (especially transitions between red and black) over an area that covers more than 25% of the screen.
- **High-Contrast Pattern Movement**:
  Avoid scrolling or vibrating high-contrast geometric patterns (like black-and-white stripes) at high speeds across the entire screen.

## 2. Recommended Techniques to Reduce Visual Strain (Strategies for Freedom)
Techniques recommended from the perspectives of ergonomics and cognitive psychology to prevent eye strain and "Visually Induced Motion Sickness". Use these to achieve dynamic expression while adhering to safety standards.

- **Utilize Trails (Motion Blur)**:
  Instead of completely clearing the screen every frame with `background(0)`, paint over the background with translucent black (e.g., `fill(0, 20); rect(0, 0, width, height);`) to leave a trail of movement. This softens the stimulation to the retina.
- **Keep Movement Localized**:
  Instead of violently rotating or vibrating the entire camera (viewport), move only a portion of the screen (like particles or specific geometry) at high speeds to prevent spatial disorientation (motion sickness).
- **Easing and Continuous Changes**:
  Abrupt value jumps frame-by-frame using `random()` create flicker. Connect value changes smoothly using `noise()` or `lerp()` to create organic, eye-friendly movements.
- **Luminance and Saturation Control**:
  Instead of painting large areas with high-saturation, high-luminance colors (like pure red or neon green), use gradients or Bloom effects (additive blending) to suppress luminance peaks while creating rich expressions.
