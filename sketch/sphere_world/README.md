# sphere_world

**Theme**: "Distant world" — a planet observed from afar; orthographic ray-sphere rendering with fractional Brownian motion surface texture and atmospheric limb glow

**Technique**: Analytic ray-sphere intersection, surface normals, Lambertian shading, 7-octave fBm terrain noise, atmospheric scattering approximation at limb

**Description**: Each pixel casts an orthographic ray at the sphere; hit pixels compute a 3D surface normal and evaluate 7 octaves of sine/cosine fBm to get a terrain height. Height maps to a 6-stop elevation palette (ocean deep → coastal → lowlands → highlands → mountain rust → snow peaks). Lambertian shading with an ambient term models the illuminated hemisphere. A Gaussian falloff at the limb creates the atmospheric blue halo; a second term adds the faint glow in surrounding space. Stars are deterministically scattered in the dark background.

**Palette**:
- Space: `#020308` deep black
- Atmosphere: `#3c8cc8` blue-cyan
- Ocean: `#3c5a3c` deep green
- Coastal: `#50823a` sage
- Plains: `#8ca064` muted ochre-green
- Highlands: `#a08250` warm ochre
- Mountains: `#783232` rust
- Snow: `#dcd7d2` pale gray-white

**Preview**: `preview.png`
