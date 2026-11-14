"""
Diversity & anti-bias analysis and validation for py5 media art sketches.

Provides two core capabilities:
1. ``generate_plan_prescription()``: Parses ``sketch/WORKS.md`` and recent sketches
   to diagnose portfolio clustering (naming ruts, genre repetition, background
   binary traps, layout monoculture, frame-count lock-in, renderer/shader
   under-utilization, and overused subject tokens) and emits a deterministic
   5-axis diversity prescription for the next work.
2. ``check_sketch_diversity(work_name)``: Audits ``sketch/<work_name>/main.py``
   against anti-bias rules before review/commit, blocking infographic flank-card
   dashboards, canvas typography (``py5.text``), ``kinetic_*_2d`` naming ruts,
   subject duplication, and dark-medallion-on-light-background loopholes.
"""

from __future__ import annotations

import ast
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKS_MD_PATH = PROJECT_ROOT / "sketch" / "WORKS.md"
SKETCH_ROOT = PROJECT_ROOT / "sketch"

GENRE_TAXONOMY: list[tuple[str, str]] = [
    (
        "Organic / Morphogenesis",
        "Biological growth, Physarum slime mold, reaction-diffusion, differential line growth, mycelium networks, cellular morphogenesis, floral branching.",
    ),
    (
        "Architectural / Brutalism / Geometric",
        "Constructivism, spatial subdivision, brutalist reliefs, isometric/axonometric mega-structures, kinetic modular facades, De Stijl / Bauhaus planes.",
    ),
    (
        "Signal / Glitch / Digital Artifacts",
        "Analog scanline modulation, moiré interferometry, phase distortion, bitplane weaving, feedback buffers, raster displacement.",
    ),
    (
        "Atmospheric / Painterly / Color Field",
        "Fluid ink wash, wet pigment diffusion, Rothko-scale color fields, stratified mist/dusk horizons, soft volumetric light.",
    ),
    (
        "Textile / Calligraphy / Procedural Craft",
        "Full-bleed woven matrices, ikat/sashiko threads, calligraphic brush dynamics, procedural hatching, interlocking sashimono/kirigami folds.",
    ),
    (
        "Mathematical / Abstract Topology",
        "Strange attractors, hyperbolic tessellations, geodesic flows, minimal surface ribbons, multi-dimensional phase portraits.",
    ),
    (
        "Physical / Micro-Kinetic",
        "Fluid vortex streets, wave interference, ferrofluid ridges, cymatic nodal fields, magnetic field lines.",
    ),
]

COMPOSITION_ARCHETYPES: list[tuple[str, str]] = [
    (
        "Full-Bleed Continuous Field",
        "Edge-to-edge visual field spanning the entire 3840x2160 canvas with zero borders, frames, or inset viewports.",
    ),
    (
        "Asymmetric Off-Center Tension",
        "Primary structural mass anchored near a golden-ratio or rule-of-thirds focal zone balanced by expansive, textured negative space.",
    ),
    (
        "Stratified Horizon / Diagonal Sweep",
        "Full-width horizontal, sheared, or diagonal strata creating deep atmospheric or topographic perspective across the whole frame.",
    ),
    (
        "Full-Canvas Polyptych / Rhythmic Matrix",
        "Edge-to-edge rhythmic cellular grid or multi-scale spatial subdivision where every cell is pure visual art (zero text or labels).",
    ),
    (
        "Emergent Network / Boundary-to-Interior Growth",
        "Branching filaments, fractures, or fronts nucleating from canvas edges or multiple asymmetrical seeds and colliding in open space.",
    ),
    (
        "3D Sculptural / Volumetric Space (P3D)",
        "True P3D spatial depth with camera perspective, volumetric layers, or lit 3D ribbon/mesh forms floating in uncluttered space.",
    ),
]

MOTION_ARCHETYPES: list[tuple[str, str]] = [
    (
        "Persistent Trail Accumulation & Decay",
        "Offscreen buffer or translucent frame fading where moving elements leave evolving painterly or calligraphic traces over 15-30s.",
    ),
    (
        "Directional Advection & Traveling Wavefronts",
        "Continuous flow fields, shear currents, or propagating wavefronts sweeping across the canvas rather than static in-place oscillation.",
    ),
    (
        "Multi-Act Temporal Evolution",
        "Distinct narrative progression (nucleation -> expansion -> turbulent interaction -> quiet resolution) across 900-1800 frames.",
    ),
    (
        "Poly-Rhythmic Phase Interference",
        "Multiple incommensurable or harmonic spatial waves drifting at different velocities to produce emergent moiré and structural shifts.",
    ),
    (
        "Spatial Camera / Depth Traversal",
        "Smooth parallax, zoom drift, or 3D camera orbit through an evolving multi-layered structure.",
    ),
]

TONAL_FAMILIES: list[tuple[str, str]] = [
    (
        "High-Key Mineral & Washi (Full-Canvas Light)",
        "Warm alabaster, raw linen, or pale sage background (#ede8dc - #e4ebe5) across 100% of the canvas (NO dark central cutouts) with mineral ochre, terracotta, and slate inks.",
    ),
    (
        "Mid-Tone Atmospheric Dusk / Celadon Slate",
        "Muted mid-luminance ground (#2c3840, #3d4e48, or #4a3f39) paired with soft chalk, warm amber, and mist highlights.",
    ),
    (
        "Stark Constructivist High-Contrast",
        "Crisp bone white or carbon black ground with bold graphic blocks in vermilion, ultramarine, or ochre.",
    ),
    (
        "Risograph Overprint Spot Inks",
        "Warm cream or soft grey paper ground with 2-3 translucent overlapping spot-color channels (e.g. fluorescent coral, teal, and deep indigo).",
    ),
    (
        "Deep Nocturnal Monochrome + Single Accent",
        "Deep charcoal/indigo ground with tonal silver/graphite gradations and strictly ONE restrained accent hue.",
    ),
    (
        "Rich Saturated Color Field",
        "Deep ochre, burnt sienna, forest viridian, or Prussian blue background gradient supporting luminous complementary forms.",
    ),
]

STOPWORDS = {
    "kinetic",
    "2d",
    "3d",
    "and",
    "the",
    "of",
    "in",
    "to",
    "with",
    "on",
    "for",
    "by",
    "from",
    "at",
    "an",
    "a",
    "wave",
    "waves",
    "field",
    "fields",
    "flow",
    "flows",
    "motion",
    "art",
    "animation",
    "light",
    "shadow",
    "shadows",
    "mist",
    "veil",
    "drift",
    "pulse",
    "horizon",
    "current",
    "currents",
    "bloom",
    "strata",
    "ridge",
    "ridges",
    "echo",
    "fold",
    "folds",
    "thread",
    "threads",
    "ink",
    "canvas",
    "stone",
    "water",
    "wind",
    "color",
    "grid",
    "matrix",
    "ribbon",
    "ribbons",
    "lattice",
    "spiral",
    "spirals",
}


@dataclass
class WorkEntry:
    name: str
    date: str = ""
    work_type: str = ""
    concept: str = ""
    techniques: str = ""
    palette: str = ""


@dataclass
class AuditReport:
    work_name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, int | float | str | bool] = field(default_factory=dict)


def parse_works_md(works_md_path: Path = WORKS_MD_PATH, limit: int = 60) -> list[WorkEntry]:
    """Parse the most recent ``limit`` entries from ``sketch/WORKS.md``."""
    if not works_md_path.exists():
        return []

    text = works_md_path.read_text(encoding="utf-8", errors="replace")
    entries: list[WorkEntry] = []
    blocks = re.split(r"^##\s+", text, flags=re.MULTILINE)
    for block in blocks[1 : limit + 1]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        name = lines[0].strip()
        entry = WorkEntry(name=name)
        for line in lines[1:]:
            if line.startswith("- **Date**:"):
                entry.date = line.split(":", 1)[1].strip()
            elif line.startswith("- **Type**:"):
                entry.work_type = line.split(":", 1)[1].strip()
            elif line.startswith("- **Concept**:"):
                entry.concept = line.split(":", 1)[1].strip()
            elif line.startswith("- **Techniques**:"):
                entry.techniques = line.split(":", 1)[1].strip()
            elif line.startswith("- **Palette**:"):
                entry.palette = line.split(":", 1)[1].strip()
        entries.append(entry)
    return entries


def infer_genre(entry: WorkEntry) -> str:
    """Infer which of the 7 Genre Taxonomy categories a work belongs to."""
    sketch_main = SKETCH_ROOT / entry.name / "main.py"
    if sketch_main.exists():
        head = "\n".join(sketch_main.read_text(encoding="utf-8", errors="replace").splitlines()[:15])
        for genre_name, _ in GENRE_TAXONOMY:
            if genre_name.lower() in head.lower():
                return genre_name

    blob = f"{entry.name} {entry.concept} {entry.techniques}".lower()
    keyword_map = [
        (
            "Organic / Morphogenesis",
            ("zooid", "siphonophor", "ctenophor", "foraminifer", "coccolith", "radiolaria", "diatom", "lichen", "medusa", "morphogenesis", "bioluminescen", "physarum", "mycelium", "coral", "cellular"),
        ),
        (
            "Architectural / Brutalism / Geometric",
            ("muqarnas", "vault", "stereotomy", "vauban", "citadel", "bastion", "guastavino", "nervi", "frei_otto", "brutalist", "cantilever", "constructivist", "architectur", "cupola"),
        ),
        (
            "Signal / Glitch / Digital Artifacts",
            ("nipkow", "television", "ferrite", "magnetic_core", "rutt_etra", "cathode_ray", "raster", "scan_disc", "video_feedback", "glitch", "bitplane", "moire"),
        ),
        (
            "Atmospheric / Painterly / Color Field",
            ("parhelia", "brocken", "fogbow", "nacreous", "stratospheric", "haboku", "sansui", "ink_wash", "chromatography", "ebru", "suminagashi", "marbling", "auroral", "color_field"),
        ),
        (
            "Textile / Calligraphy / Procedural Craft",
            ("bobbin_lace", "torchon", "jacquard", "brocade", "loom", "kumihimo", "kumiko", "kirigami", "mizuhiki", "girih", "guilloche", "tourbillon", "escapement", "horolog"),
        ),
        (
            "Mathematical / Abstract Topology",
            ("seifert", "milnor", "torus_knot", "trefoil", "costa_minimal", "weierstrass", "boy_surface", "quasicrystal", "hopf_fibration", "poincare", "topolog"),
        ),
        (
            "Physical / Micro-Kinetic",
            ("birefringence", "petrographic", "kerr_black_hole", "conical_refraction", "three_body", "ferrofluid", "caustics", "quantum", "vortex", "plasma", "soliton", "mhd"),
        ),
    ]
    for genre_name, kw_list in keyword_map:
        if any(kw in blob for kw in kw_list):
            return genre_name
    return "Physical / Micro-Kinetic"


def extract_subject_tokens(name: str) -> set[str]:
    """Extract meaningful domain tokens from a snake_case work name."""
    parts = [p.lower() for p in name.split("_") if p]
    return {p for p in parts if p not in STOPWORDS and len(p) >= 4}


def generate_plan_prescription(recent_count: int = 20) -> str:
    """
    Analyze recent works in ``sketch/WORKS.md`` and generate a concrete anti-bias
    prescription for the next artwork.
    """
    entries = parse_works_md(limit=max(recent_count, 35))
    recent = entries[:recent_count]

    last_3_genres = [infer_genre(e) for e in recent[:3]]
    allowed_genres = [g for g in GENRE_TAXONOMY if g[0] not in set(last_3_genres)]
    if not allowed_genres:
        allowed_genres = GENRE_TAXONOMY

    # Count genre frequency across last 14 works to prioritize the least-used allowed genre
    genre_counts = {g[0]: 0 for g in GENRE_TAXONOMY}
    for e in recent[:14]:
        g_name = infer_genre(e)
        genre_counts[g_name] = genre_counts.get(g_name, 0) + 1

    allowed_genres_sorted = sorted(
        allowed_genres,
        key=lambda g: (genre_counts.get(g[0], 0), random.random()),
    )
    recommended_genre = allowed_genres_sorted[0]

    # Analyze naming bias
    kinetic_prefix_count = sum(1 for e in recent if e.name.startswith("kinetic_"))
    suffix_2d_count = sum(1 for e in recent if e.name.endswith("_2d") or e.name.endswith("_3d"))

    # Analyze layout / flank card / shader / P3D bias in recent sketch files
    flank_card_count = 0
    medallion_count = 0
    frame_720_count = 0
    shader_count = 0
    p3d_count = 0
    for e in recent[:12]:
        main_py = SKETCH_ROOT / e.name / "main.py"
        if main_py.exists():
            src = main_py.read_text(encoding="utf-8", errors="replace")
            if "FIG. 01" in src or "draw_flank_card" in src or "flank cards" in e.concept.lower():
                flank_card_count += 1
            if "MEDALLION_R" in src or "medallion" in e.concept.lower():
                medallion_count += 1
            if re.search(r"TOTAL_FRAMES\s*=\s*(?:FPS\s*\*\s*DURATION_SEC|720)", src) and "720" in e.work_type:
                frame_720_count += 1
            if "lib.shaders" in src or "PostFX" in src or "load_shader" in src:
                shader_count += 1
            if "P3D" in src:
                p3d_count += 1
        else:
            if "flank cards" in e.concept.lower() or "apparatuses" in e.concept.lower():
                flank_card_count += 1
            if "medallion" in e.concept.lower():
                medallion_count += 1
            if "720 frames" in e.work_type:
                frame_720_count += 1

    # Collect overused subject tokens from the last 30 works
    banned_tokens: set[str] = set()
    for e in entries[:30]:
        banned_tokens.update(extract_subject_tokens(e.name))

    comp_choice = random.choice(COMPOSITION_ARCHETYPES)
    motion_choice = random.choice(MOTION_ARCHETYPES)
    tonal_choice = random.choice(TONAL_FAMILIES)
    rec_duration = random.randint(15, 26)
    rec_frames = rec_duration * 60

    lines = [
        "# Portfolio Diversity & Anti-Bias Prescription",
        "",
        "## 1. Diagnostic Summary of Recent Works (Last 20 Entries)",
        f"- `kinetic_*` prefix rate: **{kinetic_prefix_count}/{len(recent)}** -> `kinetic_` prefix is **BANNED** for the next work.",
        f"- `*_2d` / `*_3d` suffix rate: **{suffix_2d_count}/{len(recent)}** -> `_2d` / `_3d` suffix is **BANNED** for the next work.",
        f"- Infographic Flank-Card / `FIG. 01..08` layout rate (last 12): **{flank_card_count}/12** -> Telemetry cards, HUDs, charts, and `py5.text()` are **STRICTLY FORBIDDEN**.",
        f"- Central Circular Medallion / Bezel rate (last 12): **{medallion_count}/12** -> Central circular medallions/bezels are **STRICTLY FORBIDDEN**.",
        f"- Fixed 720-frame (12s) lock-in rate (last 12): **{frame_720_count}/12** -> Use a varied duration between **15s and 30s** (recommended: **{rec_duration}s / {rec_frames} frames**).",
        f"- Shader (`PostFX` / `load_shader`) usage (last 12): **{shader_count}/12** | `P3D` usage (last 12): **{p3d_count}/12**.",
        "",
        "## 2. Genre Rotation (Mandatory)",
        f"- Last 3 genres (EXCLUDED): {', '.join(f'`{g}`' for g in last_3_genres)}",
        f"- **Recommended Target Genre**: **{recommended_genre[0]}** — {recommended_genre[1]}",
        "- Other allowed genres: " + ", ".join(f"`{g[0]}`" for g in allowed_genres_sorted[1:]),
        "",
        "## 3. Mandatory Compositional & Visual Direction",
        f"- **Target Composition Archetype**: **{comp_choice[0]}** — {comp_choice[1]}",
        f"- **Target Motion Archetype**: **{motion_choice[0]}** — {motion_choice[1]}",
        f"- **Target Tonal / Palette Family**: **{tonal_choice[0]}** — {tonal_choice[1]}",
        "- **Pure Visual Media Art Rule**: 100% of the 3840x2160 canvas must be pure visual art. Do NOT draw any text (`py5.text`), figure numbers (`FIG. 01`), parameter tables, color swatch legends, historical timelines, museum borders, or compass bezels.",
        "- **No Historical-Treatise Framing**: Frame the concept around visual perception, spatial tension, material texture, or emergent motion — NOT a textbook diagram of a historical patent or scientific monograph.",
        "",
        "## 4. Naming & Subject Restrictions",
        "- **Work Name Format**: Choose a concise, evocative **2 to 4 word** `snake_case` name (e.g., `vermilion_basalt_faults`, `sashiko_indigo_drift`, `mist_catenary_veil`).",
        "- **Forbidden Name Affixes**: Do NOT start with `kinetic_` and do NOT end with `_2d` or `_3d`.",
        "- **Recently Used Subject Tokens (DO NOT REPEAT)**:",
        "  " + ", ".join(sorted(banned_tokens)[:65]),
    ]
    return "\n".join(lines)


def check_sketch_diversity(work_name: str) -> AuditReport:
    """
    Validate ``sketch/<work_name>/main.py`` against portfolio anti-bias rules.
    Returns an ``AuditReport`` with ``passed=False`` if any hard bias rule is violated.
    """
    report = AuditReport(work_name=work_name, passed=True)
    sketch_dir = SKETCH_ROOT / work_name
    main_py = sketch_dir / "main.py"

    # 1. Check work_name rules
    words = [w for w in work_name.split("_") if w]
    report.metrics["word_count"] = len(words)

    if work_name.startswith("kinetic_"):
        report.errors.append(
            f"Naming bias: '{work_name}' starts with 'kinetic_'. The 'kinetic_' prefix is banned to break the naming monoculture; use a 2-4 word evocative snake_case name."
        )
    if work_name.endswith("_2d") or work_name.endswith("_3d"):
        report.errors.append(
            f"Naming bias: '{work_name}' ends with '_2d' or '_3d'. Dimension suffixes are banned; use a clean 2-4 word snake_case name."
        )
    if len(words) > 5:
        report.errors.append(
            f"Naming bias: '{work_name}' has {len(words)} words. Work names must be concise (2 to 4 words, max 5) rather than long technical jargon chains."
        )

    # Check specific subject token overlap against recent works in WORKS.md (excluding work_name itself)
    entries = [e for e in parse_works_md(limit=35) if e.name != work_name]
    candidate_tokens = extract_subject_tokens(work_name)
    for past in entries[:25]:
        past_tokens = extract_subject_tokens(past.name)
        overlap = candidate_tokens & past_tokens
        if overlap:
            report.errors.append(
                f"Subject clustering: '{work_name}' repeats domain token(s) {sorted(overlap)} from recent work '{past.name}'."
            )
            break

    if not main_py.exists():
        report.errors.append(f"Missing sketch file: {main_py}")
        report.passed = False
        return report

    src = main_py.read_text(encoding="utf-8", errors="replace")

    # 2. Check for banned infographic / telemetry / flank-card / medallion patterns
    text_call_count = len(re.findall(r"\b(?:py5|canvas|g)\.text\s*\(", src))
    report.metrics["text_calls"] = text_call_count
    if text_call_count > 0:
        report.errors.append(
            f"Infographic / HUD bias: found {text_call_count} `.text(...)` call(s) in main.py. Media art canvases must be 100% pure visual art with zero text, titles, HUDs, or telemetry labels drawn on the frame."
        )

    banned_identifiers = [
        (r"FIG\.\s*0[1-9]", "FIG. 01..08 figure labels"),
        (r"\bdraw_flank_card\b|\bdraw_card_box\b|\bdraw_light_card_frame\b", "flank telemetry card helpers"),
        (r"\bMEDALLION_R\b|\bdraw_stereographic_bezel\b|\bdraw_sky_dome_compass_bezel\b", "central medallion/compass bezel template"),
        (r"\bdraw_archival_border_and_typography\b|\bdraw_frame_border_and_header\b", "museum border & header banner template"),
    ]
    for pattern, label in banned_identifiers:
        if re.search(pattern, src):
            report.errors.append(
                f"Template lock-in: found '{label}' in main.py. The 'Central Medallion + 4 Flank Cards / Museum Codex' template is strictly prohibited; use a full-bleed 3840x2160 visual composition."
            )

    # 3. Check for fixed 720-frame / 12-second monoculture
    if re.search(r"^\s*DURATION_SEC\s*=\s*(?:10|11|12|13|14)(?:\.0)?\b", src, flags=re.MULTILINE) or re.search(
        r"^\s*TOTAL_FRAMES\s*=\s*720\b", src, flags=re.MULTILINE
    ):
        report.errors.append(
            "Temporal lock-in: DURATION_SEC=12 / TOTAL_FRAMES=720 is banned because recent works were locked to 720 frames. Use a duration between 15 and 30 seconds (900-1800 frames)."
        )

    # 4. Check for the #060912 / #f6f2e8 background binary & dark-basin-on-light-background loophole
    if re.search(r"\(\s*6\s*,\s*9\s*,\s*1[289]\s*\)", src) or "#060912" in src.lower():
        report.errors.append(
            "Palette lock-in: exact obsidian background (6, 9, 18) / #060912 is overused across recent works. Choose a fresh tonal ground."
        )
    if re.search(r"\(\s*24[456]\s*,\s*24[12]\s*,\s*23[024]\s*\)", src) and re.search(
        r"\b(?:ABYSS_BG|VAULT_BG|PILLOW_BG)\b", src
    ):
        report.errors.append(
            "Background inversion loophole: placing a dark abyssal/vault cutout basin on top of a light vellum background violates true light-background composition."
        )

    # 5. AST check for syntax validity
    try:
        ast.parse(src, filename=str(main_py))
    except SyntaxError as exc:
        report.errors.append(f"SyntaxError in {main_py}: {exc}")

    report.passed = len(report.errors) == 0
    return report
