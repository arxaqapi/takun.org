#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "numpy>=2.5.1",
#     "pillow>=12.3.0",
# ]
# ///
"""
Generate dithered abstract art for the site.

- hero.png            one wide dithered landscape band for the header
- dither/<slug>.png   one unique dithered "fingerprint" per publication

The fingerprint of each paper is built by COMPOSITING one visual primitive per
TAG. Every tag has its own distinct "feel" (waveform rows, moiré ripples, a
measurement grid, branching growth, mirrored symmetry, soft child-like blobs,
long-form drift...), so two papers with different tags look genuinely different,
while the per-slug seed keeps each individual image unique and stable.

1-bit Floyd-Steinberg dithering, ink on transparent paper (CSS bg shows through;
dark mode inverts in CSS).
"""

from pathlib import Path
import hashlib
import math

import numpy as np
from PIL import Image

from build import slugify, load_publications


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def seed_from(*parts) -> int:
    return int(hashlib.sha256("::".join(parts).encode()).hexdigest(), 16) % (2**32)


def floyd_steinberg(gray: np.ndarray) -> np.ndarray:
    """1-bit Floyd-Steinberg dithering. gray in [0,1] -> {0,1}."""
    g = gray.astype(np.float32).copy()
    h, w = g.shape
    for y in range(h):
        for x in range(w):
            old = g[y, x]
            new = 1.0 if old > 0.5 else 0.0
            g[y, x] = new
            err = old - new
            if x + 1 < w:
                g[y, x + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    g[y + 1, x - 1] += err * 3 / 16
                g[y + 1, x] += err * 5 / 16
                if x + 1 < w:
                    g[y + 1, x + 1] += err * 1 / 16
    return g


def to_png(bits, path, ink=(31, 29, 26), scale=2):
    """bits in {0,1}; 1 = ink. RGBA PNG with transparent paper."""
    h, w = bits.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    m = bits > 0.5
    rgba[m, 0], rgba[m, 1], rgba[m, 2], rgba[m, 3] = ink[0], ink[1], ink[2], 255
    img = Image.fromarray(rgba, "RGBA")
    if scale != 1:
        img = img.resize((w * scale, h * scale), Image.NEAREST)
    img.save(path)


def _grid(n):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    return xx / n, yy / n  # normalized 0..1


# ===========================================================================
# TAG PRIMITIVES
# Each returns a float field in ~[0,1] (higher = more ink after dithering).
# They are designed to be visually distinct so categories read differently.
# `rng` is seeded per (slug, tag) so the same tag varies subtly between papers
# but keeps its characteristic feel.
# ===========================================================================
def feel_speech(n, rng):
    """Horizontal waveform / spectrogram rows: banded, oscillating stripes."""
    x, y = _grid(n)
    rows = rng.integers(5, 8)
    field = np.zeros((n, n), np.float32)
    for _ in range(rows):
        yc = rng.uniform(0, 1)
        thick = rng.uniform(0.03, 0.07)
        freq = rng.uniform(6, 14)
        amp = rng.uniform(0.01, 0.04)
        wob = amp * np.sin(2 * math.pi * freq * x + rng.uniform(0, 6.28))
        band = np.exp(-((y - yc - wob) ** 2) / (2 * thick**2))
        # modulate along x like an envelope of a waveform
        env = 0.55 + 0.45 * np.sin(
            2 * math.pi * rng.uniform(1, 3) * x + rng.uniform(0, 6.28)
        )
        field += band * env
    return field


def feel_longform(n, rng):
    """Long slow horizontal drift: wide low-frequency bands sweeping across."""
    x, y = _grid(n)
    field = np.zeros((n, n), np.float32)
    for _ in range(rng.integers(2, 4)):
        phase = rng.uniform(0, 6.28)
        f = rng.uniform(0.6, 1.4)  # very low freq => "long form"
        slope = rng.uniform(-0.4, 0.4)  # gentle diagonal drift
        field += 0.5 + 0.5 * np.sin(2 * math.pi * f * (x + slope * y) + phase)
    # emphasize horizontal continuity
    field *= 0.6 + 0.4 * (0.5 + 0.5 * np.sin(2 * math.pi * 0.8 * x))
    return field


def feel_self_supervised(n, rng):
    """Dense interfering ripples => moiré / emergent learned structure."""
    x, y = _grid(n)
    field = np.zeros((n, n), np.float32)
    for _ in range(rng.integers(3, 5)):
        sx, sy = rng.uniform(0, 1), rng.uniform(0, 1)
        rr = np.sqrt((x - sx) ** 2 + (y - sy) ** 2)
        wl = rng.uniform(0.05, 0.11)
        field += 0.5 + 0.5 * np.sin(rr / wl * 2 * math.pi + rng.uniform(0, 6.28))
    return field


def feel_benchmark(n, rng):
    """Measurement lattice: crisp grid of rulers / cells."""
    x, y = _grid(n)
    cells = int(rng.integers(4, 6))
    lw = rng.uniform(0.12, 0.20)  # line duty cycle
    gx = (x * cells) % 1.0
    gy = (y * cells) % 1.0
    lines = ((gx < lw) | (gx > 1 - lw) | (gy < lw) | (gy > 1 - lw)).astype(np.float32)
    # checkerboard of alternating cells fills the interior => reads as a table
    check = (np.floor(x * cells).astype(int) + np.floor(y * cells).astype(int)) % 2 == 0
    field = np.maximum(lines, 0.5 * check.astype(np.float32))
    return field


def feel_evolution(n, rng):
    """Branching / cellular growth: Voronoi-like cells with jittered seeds."""
    x, y = _grid(n)
    k = rng.integers(6, 11)
    pts = rng.uniform(0.05, 0.95, size=(k, 2))
    # distance to nearest and 2nd-nearest seed => cell borders glow
    d = np.stack([np.sqrt((x - px) ** 2 + (y - py) ** 2) for px, py in pts], axis=0)
    d.sort(axis=0)
    border = d[1] - d[0]  # small near borders
    edge = 1.0 - np.clip(border / 0.035, 0, 1)  # sharp bright edges => web
    edge = edge**0.6  # thicken the branches
    # faint interior shading toward nearest seed for organic cell bodies
    field = np.maximum(edge, 0.30 * (1 - np.clip(d[0] / 0.35, 0, 1)))
    return field


def feel_analogy(n, rng):
    """Mirrored symmetry (A:B :: C:D): a pattern reflected across an axis."""
    x, y = _grid(n)
    # build a strongly asymmetric base on the LEFT half, then mirror it right
    base = np.zeros((n, n), np.float32)
    for _ in range(int(rng.integers(2, 4))):
        sx, sy = rng.uniform(0.05, 0.4), rng.uniform(0.1, 0.9)
        rr = np.sqrt((x - sx) ** 2 + (y - sy) ** 2)
        base += np.exp(-(rr**2) / (2 * rng.uniform(0.12, 0.2) ** 2))
        base += 0.4 * (0.5 + 0.5 * np.sin(rr / rng.uniform(0.05, 0.09) * 2 * math.pi))
    base = (base - base.min()) / (base.max() - base.min() + 1e-9)
    mirrored = base[:, ::-1]
    field = np.maximum(base, mirrored)  # symmetric across vertical axis
    # clear central seam so the reflection reads as "::"
    seam = np.exp(-((x - 0.5) ** 2) / (2 * 0.018**2))
    field = np.clip(field - 0.9 * seam, 0, None)
    return field


def feel_child(n, rng):
    """Soft, gentle, low-frequency blobs: rounded and calm."""
    x, y = _grid(n)
    field = np.zeros((n, n), np.float32)
    for _ in range(rng.integers(2, 4)):
        cx, cy = rng.uniform(0.25, 0.75), rng.uniform(0.25, 0.75)
        s = rng.uniform(0.14, 0.24)
        field += np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s**2))
    field /= field.max() + 1e-9
    return field**0.8  # gamma => softer falloff


TAG_FEELS = {
    "speech": feel_speech,
    "longform": feel_longform,
    "self-supervised": feel_self_supervised,
    "benchmark": feel_benchmark,
    "evolution": feel_evolution,
    "analogy": feel_analogy,
    "child": feel_child,
}

# How strongly each tag pushes into the mix (first tag dominates the silhouette).
TAG_WEIGHT = {
    "speech": 1.00,
    "longform": 0.95,
    "self-supervised": 1.00,
    "benchmark": 0.85,
    "evolution": 1.00,
    "analogy": 1.00,
    "child": 0.80,
}


# ---------------------------------------------------------------------------
# COMPOSE a fingerprint from a paper's tags
# ---------------------------------------------------------------------------
def make_fingerprint(slug, tags: list[str], size: int, output_path: Path):
    n = size
    x, y = _grid(n)
    acc = np.zeros((n, n), np.float32)
    total_w = 0.0
    for i, tag in enumerate(tags):
        if tag not in TAG_FEELS:
            raise ValueError(
                f"unknown tag {tag!r} on {slug}; known: {sorted(TAG_FEELS)}"
            )
        rng = np.random.default_rng(seed_from(slug, tag, str(i)))
        f = TAG_FEELS[tag](n, rng)
        f = (f - f.min()) / (f.max() - f.min() + 1e-9)
        # first tag anchors the composition; later tags layer in with decay
        w = TAG_WEIGHT[tag] * (0.7**i)
        acc += w * f
        total_w += w
    acc /= total_w + 1e-9

    # circular vignette so the token sits as a tidy glyph
    r = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2)
    vig = np.clip(1.12 - r / 0.60, 0, 1)
    field = np.clip(acc * (0.30 + 0.70 * vig), 0, 1)

    bits = floyd_steinberg(field)
    to_png(bits, output_path / f"{slug}.png")
    return slug


# ---------------------------------------------------------------------------
# HERO landscape band (unchanged concept: layered dithered terrain)
# ---------------------------------------------------------------------------
def _hero_ridge(w, rng, amp, octaves=5):
    xs = np.linspace(0, 1, w)
    y = np.zeros(w)
    for o in range(octaves):
        f = 2**o * rng.uniform(1.5, 2.5)
        a = amp / (1.7**o)
        y += a * np.sin(2 * math.pi * f * xs + rng.uniform(0, 6.28))
    y = (y - y.min()) / (y.max() - y.min() + 1e-9)
    return (y - 0.5) * amp


def make_hero(output_path: Path, w: int = 560, h: int = 150, seed: int = 11):
    rng = np.random.default_rng(seed)
    yy = np.linspace(0, 1, h)[:, None]
    field = 0.15 + 0.85 * (1 - yy[:, 0])
    field = np.tile(field[:, None], (1, w))
    for horizon, amp, dark in [
        (0.42, 0.10, 0.55),
        (0.60, 0.13, 0.72),
        (0.80, 0.16, 0.90),
    ]:
        ridge = horizon + _hero_ridge(w, rng, amp * 2, octaves=10)
        for x in range(w):
            below = yy[:, 0] >= ridge[x]
            depth = np.clip((yy[:, 0] - ridge[x]) / (1 - ridge[x] + 1e-6), 0, 1)
            val = (dark * 0.8) - 0.25 * depth
            field[below, x] = np.minimum(field[below, x], val[below])
    field = np.clip(field, 0, 1)
    to_png(floyd_steinberg(field), output_path / "hero.png")
    print("hero.png", w * 2, "x", h * 2)


if __name__ == "__main__":
    OUT_PATH = Path("dither")
    OUT_PATH.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------------
    # Publications: slug + the tags that shape its fingerprint.
    # Order matches index.html. Add / reorder tags to restyle a fingerprint.
    # Available tags are defined in TAG_FEELS below.
    # ---------------------------------------------------------------------------
    PAPERS = [(slugify(p["title"]), p.get("tags", [])) for p in load_publications()]
    SIZE = 56  # base resolution of a fingerprint (upscaled x2 on save)

    make_hero(output_path=OUT_PATH, seed=2)
    for slug, tags in PAPERS:
        make_fingerprint(slug, tags, SIZE, output_path=OUT_PATH)
        print(f"{slug:26s} <- {', '.join(tags)}")
    print("done ->", OUT_PATH)
