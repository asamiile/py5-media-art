# Brush-Up Proposals

Each entry applies the Artist SKILL.md guidelines (theme-first, color design)
to works that have received user feedback. Use this file when implementing v2.

---

## lissajous_web
**Feedback:** "You may draw abstract lines that mimic the shape of an object."

**Theme:** "The memory of a form" — lines that almost, but not quite, resolve into a recognizable silhouette.

**Visual impression (3 sec):** A dark canvas with luminous gold curves that suggest a bird in flight or a wave curling over. The shape is readable but never literal.

**Palette (4 colors):**
- Background: `#09090f` near-black with cold undertone
- Primary line: `#c8a96e` warm gold, low opacity layering
- Secondary line: `#7e9bb5` steel blue, even lower opacity
- Accent glow: `#fff4e0` off-white for the densest intersections only

**Key changes:**
- Reduce frequency-ratio set to 4–6 pairs chosen specifically to trace a silhouette outline (e.g., bird: ratios near 3:2, 5:4 cluster along horizontal axis)
- Remove rainbow coloring; draw all curves in gold with varying alpha by overlap density
- Accumulate pixel brightness so intersections naturally brighten — no explicit glow code needed
- Add a faint vignette to push the eye toward the center form

---

## truchet_tiles
**Feedback:** "I'd like to see other patterns as well."

**Theme:** "Woven fabric at microscale" — a textile-like surface where the repeat unit is just complex enough to lose the grid.

**Visual impression (3 sec):** Dense, flat-looking surface in muted linen tones that reveals increasing complexity on closer inspection. No single element dominates.

**Palette (3 colors):**
- Background tile A: `#d6cfc4` warm linen
- Background tile B: `#3d3530` deep espresso brown
- Arc stroke: `#8a7f74` mid-tone gray-beige (same for all arcs — structure through geometry, not color)

**Key changes:**
- Add a third tile orientation: full diagonal line (not arc) for variety
- Use 4-color Truchet (Smith, 1987) — each tile can carry one of 4 orientations including diagonals and crosses
- Tile size: reduce to 40×40 px for denser weave
- Monochrome palette — contrast comes entirely from tile geometry, not color

---

## contour_field
**Feedback:** "I want to watch animation."

**Theme:** "Terrain breathing" — a landscape that inhales and exhales, its ridges slowly shifting like sand dunes or clouds.

**Visual impression (3 sec):** Slow, meditative motion. Contour lines drift and fold. The landscape feels geological — ancient, patient.

**Palette (5 colors):**
- Deep valley: `#0e1520` near-black navy
- Lower elevation: `#2a4055` dark slate blue
- Mid elevation: `#5c7a6a` muted sage green
- Upper elevation: `#a08c6e` warm sandstone
- Peak: `#e8dcc8` pale bone white

**Key changes:**
- Template B (animation), 8 sec, 30 fps
- Use 3D noise field: `noise(x, y, t)` where `t` advances slowly each frame
- The "z" slice moves through the noise volume — contours shift organically
- Keep the sharp band-coloring from v1; add 1-pixel dark border between bands
- No random seed — each run is a different landscape in motion

---

## cellular_automaton
**Feedback:** "I'd like to see other colors and patterns as well."

**Theme:** "Crystal lattice forming" — not the Sierpinski triangle but a different rule that grows outward like ice crystals from a seed.

**Visual impression (3 sec):** Precise geometric growth radiating from a dark center. Metallic, cold, exact.

**Palette (3 colors):**
- Background (dead cell): `#050810` near-black
- Active cell: `#b8d4e8` pale ice blue
- Recent cell (just activated): `#e8f4ff` near-white with slight blue

**Key changes:**
- Switch rule: try **Rule 110** (Turing-complete, produces aperiodic complex patterns) or a 2D **Highlife** rule
- Color dead cells as pure black; encode recency with brightness (recent = white, old = ice blue, very old = dim)
- Remove the generation-gradient hue shift; instead use luminance only (monochrome with temperature)
- Run more generations to fill the canvas with structure

---

## modulo_circles
**Feedback:** "I'd like to see other color patterns as well."

**Theme:** "Resonance frequencies" — each multiplier is a different harmonic, visualized as its own color voice in a chord.

**Visual impression (3 sec):** A dark disc containing overlapping geometric families in 3 complementary colors. Mathematical but emotionally warm.

**Palette (3 colors + background):**
- Background: `#0a0a12` near-black
- Low multipliers (M=2,3): `#c4785a` burnt sienna / rust
- Mid multipliers (M=5,7): `#5a8ca8` steel blue
- High multipliers (M=13,51): `#a8c87a` sage green
- (All at alpha 30–50 for layering)

**Key changes:**
- Replace per-multiplier rainbow hue with the 3-family grouping above
- Vary line weight by multiplier: M=2,3 → weight 1.2; M=5,7 → weight 0.8; M=13,51 → weight 0.4
- Add a faint outer ring (circle border) in dark gray to frame the composition
- Reduce alpha slightly to let overlaps build naturally

---

## lsystem_tree
**Feedback:** "When creating natural objects, the goal is to reproduce natural phenomena."

**Theme:** "A single tree in winter light" — not a fractal diagram but a tree that looks like it was painted from observation.

**Visual impression (3 sec):** Asymmetric, wind-shaped silhouette against a pale sky. Looks observed, not generated.

**Palette (5 colors):**
- Sky: `#d6dde8` pale cold gray-blue gradient (top) to `#eae8e0` warm white (horizon)
- Trunk/main branches: `#2d2318` very dark brown
- Secondary branches: `#4a3828` mid dark brown
- Fine twigs: `#6b5848` lighter brown-gray
- Background haze: `#c8cdd4` soft atmospheric gray

**Key changes:**
- Strong stochastic variation: branch angle jitter ±25° each fork (not ±5°)
- Branch count: 2 at lower levels, 1 or 2 randomly at upper levels (trees do not branch symmetrically)
- Add a slight wind lean: left branches grow slightly shorter and more horizontal than right
- Use thick-to-thin tapering aggressively (trunk: 12px → twig: 0.5px)
- No bright leaf colors — bare winter tree, focus on silhouette structure

---

## voronoi_cells
**Feedback:** "I'd like it to be a little more abstract."

**Theme:** "Shattered glass, still" — Voronoi cells as a cold, geometric fragmentation with no organic warmth.

**Visual impression (3 sec):** A dark plane cracked into irregular polygons, like a windshield on a winter morning. The eye follows the border network, not the cells.

**Palette (4 colors):**
- Background: `#08080e` near-black
- Cell interior: `#121a22` very dark navy (almost invisible against background)
- Border lines: `#3d6070` cold steel blue (the main visual element)
- Highlight border (1-2 cells): `#a8c8d8` pale ice blue accent

**Key changes:**
- Make cell borders the subject, not the fill — thin (1px) bright lines on dark fill
- Remove the center-glow gradient from v1; all cells flat and dark
- Add Delaunay triangulation lines as a second overlay at 20% alpha
- Choose 2–3 cells randomly to receive the pale ice-blue border as accent
- No earth-tone palette; pure cold geometry

---

## flow_field
**Feedback:** "It would be even better if it were a little more abstract."

**Theme:** "Signal degrading" — a transmission losing coherence. Structured at first, dissolving into noise at the edges.

**Visual impression (3 sec):** Dark field. Dense, thin lines converging toward a faint attractor region at center, then dispersing chaotically at the periphery. Like radio interference.

**Palette (3 colors):**
- Background: `#030308` near-black
- Main stream (high-density): `#28c4a8` electric teal (very thin, high alpha)
- Dispersed particle (low-density): `#7a3040` deep crimson (sparse, visible only at edges)
- (No warm golds or yellows)

**Key changes:**
- Increase particle count to 150k; reduce trail alpha to 8–12 so density is the only visible signal
- Remove the sine/cosine multi-frequency field; replace with a field that has one strong center attractor and random perturbation increasing with radius
- Color by local density: high-density regions → teal; low-density → dark crimson
- No log-scale tone mapping — let the center genuinely blow out to near-white while edges are near-black

---

## wave_interference
**Feedback:** "It's too blurry."

**Theme:** "Precision instrument" — an interference pattern as if measured in a physics laboratory. Exact, sharp, no anti-aliasing softness.

**Visual impression (3 sec):** High-contrast grid-like pattern of sharp nodes. Feels technical, almost like an X-ray or oscilloscope readout.

**Palette (3 colors):**
- Background / destructive: `#03050a` near-black
- Weak constructive: `#1a3a4a` dark teal
- Strong constructive (peak): `#e0f0ff` cold near-white

**Key changes:**
- Replace the analytical computation with a 1-bit threshold render: pixel is either ON (bright) or OFF (dark) — hard edges, no gradient
- Reduce wave sources to 5 (from 9) for clearer readable pattern
- Use `np.where(interference > threshold, bright_color, dark_color)` — binary rendering
- Add a subtle grid overlay at low alpha to reinforce the "measurement" aesthetic

---

## clifford_attractor
**Feedback:** "I'd like to see other patterns as well."

**Theme:** "Dust settling" — another strange attractor family, rendered as if fine particles fell onto the canvas and came to rest.

**Visual impression (3 sec):** A dim canvas with an intricate skeletal structure emerging from accumulated density. Organic yet precise.

**Palette (3 colors):**
- Background: `#06060a` near-black
- Low density: `#1e2030` very dim blue-gray
- High density: `#d4c4a0` warm sand / pale parchment

**Key changes:**
- Switch attractor: try **Duffing attractor**, **Tinkerbell map**, or **Peter de Jong attractor** — each gives a radically different shape family
- Keep the log-scale density accumulation from v1 — it works well
- Replace amber on black with parchment-on-black: warm neutral at high density, cold dark blue at low density
- Render at 5M points for fine grain

---

## fourier_epicycles
**Feedback:** "The use of color is monotonous, so consider an artistic color scheme."

**Theme:** "Clockwork orrery" — nested gears of an astronomical instrument tracing a planetary path.

**Visual impression (3 sec):** Brass mechanical arms against a dark background. The traced curve builds up in a single accent color, not a rainbow.

**Palette (4 colors):**
- Background: `#07080e` near-black
- Epicycle circles (rings): `#2a2010` very dark bronze (barely visible)
- Epicycle arms: `#8a6a30` dark brass
- Traced curve — recent: `#e8c870` warm gold
- Traced curve — old: `#3a3020` very dark brown (fade to background)

**Key changes:**
- Single color for the trail (gold → dark brown as age increases), not a rainbow sweep
- Make epicycle circles and arms much more visible as design elements (thicker, brighter brass)
- Reduce N_CHAINS to 1 — the single-mechanism clarity is more elegant
- Add tiny dot at each arm joint point (brass rivet aesthetic)

---

## reaction_diffusion
**Feedback:** "It would be good if the patterns didn't overlap."

**Theme:** "Isolated organisms" — distinct, separate cellular forms with clear dark territory between them.

**Visual impression (3 sec):** Scattered islands of complex texture on a dark sea. Each island is self-contained. Biological but cold.

**Palette (4 colors):**
- Background (low B): `#080c10` near-black
- Transition zone: `#1a3030` dark teal
- Structure (high A): `#c8d8b8` pale sage green
- Core of structure: `#f0f4e8` near-white

**Key changes:**
- Adjust Gray-Scott parameters toward the **"spots" regime**: lower F (feed rate ~0.035), higher k (kill rate ~0.064) — produces isolated spots instead of connected labyrinths
- Initialize with scattered small circular seeds rather than random noise — controls where patterns form
- Run for fewer steps (1000 instead of 2000) to catch the isolated-spot stage before they merge
- Replace warm coral tones with cold sage/mint — colder palette reads as more isolated and precise
