# ferroelastic_domain_drift

A polarized-material animation where ferroelastic domains drift and lock, leaving amber memories at the moving boundaries. Teal and violet regions brighten under a rotating analyzer, then fade back into graphite.

## Technique

- Continuous phase-field relaxation with pinning noise and slow external bias.
- Domain-wall memory extracted from the field gradient.
- Direct NumPy-to-py5 pixel rendering, encoded as a 10s 4K/60fps MP4.
