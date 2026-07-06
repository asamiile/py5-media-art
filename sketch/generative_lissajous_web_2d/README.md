# generative_lissajous_web_2d

**Date**: 2026-07-06
**Type**: Animation (10-30s @ 60fps)

## Concept
A complex 3D-looking web constructed entirely from 2D Lissajous curves that slowly shift their phase and frequency over time. The curves are drawn with low opacity and high iteration counts to create volumetric forms.

## Techniques
Connect points evaluated on parametric Lissajous equations `x = A sin(a*t + p), y = B sin(b*t + q)` where `a, b, p, q` are slowly mutating. Draw fine lines between successive points or across phase shifts to weave a web.

## Palette
Iridescent synth. Deep cyan background with curves transitioning through magenta, yellow, and bright white.
