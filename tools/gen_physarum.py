#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "numpy>=2.5.1",
#     "pillow>=12.3.0",
# ]
# ///
"""
Generate the site's art with a physarum (slime-mould) simulation.

- art/hero.png     the wide header band
- art/<slug>.png   one unique "fingerprint" per publication

The simulation follows Jeff Jones' agent model as extended by Sage Jenson
("36 points") and Etienne Jacob / bleuje (https://bleuje.com/physarum-explanation/):

  every agent senses the trail map at three points (left / ahead / right),
  turns toward the strongest one, moves, and deposits; the trail map is then
  blurred (3x3) and decays.

Sensor distance, sensor angle, rotation angle and move distance are not fixed:
each one is  p0 + p1 * x**p2  where x is the trail value under the agent, so a
parameter set (a "point") produces its own speculative organism.

TAGS: every tag is a point (+ an initial layout). A paper's tags are MIXED as
species (Jenson's multi-species physarum): each tag owns a smooth noise-shaped
territory and gets its own population and trail map. A species spawns and
deposits in proportion to its territory, and also senses the other species'
trails a little, so neighbouring organisms meet and intertwine at the seams.
The first tag claims the most ground; later tags decay. Seeds are derived from
(slug, tags) so every image is unique and stable.

The simulation runs at RES x the reference grid and is downsampled on save, so
filaments stay thin and crisp.

Ink on transparent paper (the CSS background shows through; dark mode inverts).
"""

from dataclasses import dataclass
from pathlib import Path
import hashlib
import math

import numpy as np
from PIL import Image

from build import slugify, load_publications

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "art"
SIZE = 112  # reference grid: Point distances are pixels at this size
RES = 3  # supersampling: simulate at SIZE * RES so filaments stay thin and crisp
THUMB_PX = 224  # saved fingerprint size (displayed at 44 CSS px)
HERO_PX = (1680, 450)  # saved hero size; simulated at 2240 x 600
INK = (31, 29, 26)


def seed_from(*parts) -> int:
    return int(hashlib.sha256("::".join(parts).encode()).hexdigest(), 16) % (2**32)


# ===========================================================================
# POINT — one parameter set of the simulation (one species).
# Distances are in pixels at SIZE and get multiplied by the render `scale`.
# ===========================================================================
@dataclass(frozen=True)
class Point:
    # sensor distance / sensor angle (deg) / rotation angle (deg) / move distance
    # each = base + amp * x**exp, x = sensed trail in [0,1]
    sd: tuple = (6.0, 0.0, 1.0)
    sa: tuple = (30.0, 0.0, 1.0)
    ra: tuple = (30.0, 0.0, 1.0)
    md: tuple = (1.0, 0.0, 1.0)
    inertia: float = 0.0  # bleuje's velocity effect: 0 = classic, 1 = smooth
    level: float = 0.0  # heading pulled toward horizontal (0 = isotropic)
    gain: float = 0.4  # sensed-value rescale (bleuje's p15)
    respawn: float = 0.0  # per-step probability an agent restarts
    # trail map
    decay: float = 0.85
    diffuse: float = 0.5  # 0 = sharp trails, 1 = full 3x3 blur every step
    deposit: float = 1.0
    mirror: float = 0.0  # 1 = trail kept left/right symmetric
    agents: float = 1.0  # agents per pixel of territory


# ===========================================================================
# TAGS — one point + an initial layout each. Adding a tag = adding an entry.
#   init: "uniform" | "disc" (facing inward) | "seed" (a few colonies)
# ===========================================================================
TAGS: dict[str, dict] = {
    # flowing horizontal streams, like a waveform smeared through time
    "speech": dict(
        point=Point(
            sd=(4, 0, 1), sa=(20, 0, 1), ra=(12, 0, 1), md=(0.9, 0.6, 1),
            inertia=0.6, level=0.06, decay=0.93, diffuse=0.15, gain=0.25, agents=1.6,
        ),
        init="uniform",
    ),
    # long, slow, sweeping filaments
    "longform": dict(
        point=Point(
            sd=(12, -6, 1), sa=(15, 10, 2), ra=(10, 0, 1), md=(1.2, 0, 1),
            inertia=0.85, level=0.008, decay=0.95, diffuse=0.2, gain=0.2, agents=0.6,
        ),
        init="uniform",
    ),
    # coral-like labyrinth: sensors reach and splay further where the trail is dense
    "self-supervised": dict(
        point=Point(
            sd=(1.5, 3, 1), sa=(15, 75, 1), ra=(60, 0, 1), md=(0.6, 0, 1),
            decay=0.8, diffuse=0.6, gain=0.6, agents=2.0,
        ),
        init="uniform",
    ),
    # a stable polygonal mesh: the reticular network of Jones' model
    "benchmark": dict(
        point=Point(
            sd=(5, 0, 1), sa=(45, 0, 1), ra=(22.5, 0, 1), md=(1.0, 0, 1),
            decay=0.85, diffuse=0.5, gain=0.4,
        ),
        init="uniform",
    ),
    # branching growth spreading out from a few colonies
    "evolution": dict(
        point=Point(
            sd=(10, -6, 0.5), sa=(40, -30, 1), ra=(20, 0, 1), md=(1.5, -1.0, 1),
            inertia=0.3, decay=0.96, diffuse=0.2, gain=0.3, respawn=0.003, agents=0.4,
        ),
        init="seed",
    ),
    # bilateral symmetry (A is to B as C is to D): mirrored veins
    "analogy": dict(
        point=Point(
            sd=(10, -6, 0.5), sa=(40, -30, 1), ra=(20, 0, 1), md=(1.5, -1.0, 1),
            inertia=0.3, decay=0.95, diffuse=0.2, gain=0.3, respawn=0.003,
            mirror=1.0, agents=0.6,
        ),
        init="seed",
    ),
    # scattered soft beads: agents stall where the trail is dense
    "child": dict(
        point=Point(
            sd=(9, -7, 0.5), sa=(70, 0, 1), ra=(50, 0, 1), md=(1.0, -0.95, 0.5),
            decay=0.8, diffuse=1.0, gain=0.3, agents=1.2,
        ),
        init="uniform",
    ),
}


# ===========================================================================
# SIMULATION
# ===========================================================================
def _smooth_noise(h, w, rng, cells):
    """Smooth value noise (bicubic-upsampled random grid), shape (h, w), in [0,1]."""
    gh, gw = max(2, round(cells * h / max(h, w))) + 1, max(2, round(cells * w / max(h, w))) + 1
    grid = Image.fromarray(rng.random((gh, gw)).astype(np.float32), "F")
    a = np.asarray(grid.resize((w, h), Image.BICUBIC), np.float32)
    return (a - a.min()) / (np.ptp(a) + 1e-9)


def _spawn(kind, n, terr, rng):
    """n agents laid out per `kind`, kept with probability ~ territory weight."""
    h, w = terr.shape
    if kind == "seed":  # a few colonies, centred where the territory is strong
        k = int(rng.integers(2, 5)) * max(1, w // h)
        flat = terr.ravel() / terr.sum()
        cy, cx = np.divmod(rng.choice(h * w, k, p=flat), w)
        pick = rng.integers(0, k, n)
        rad = min(h, w) * 0.04 * np.sqrt(rng.random(n))
        th = rng.random(n) * 2 * math.pi  # facing outward
        x, y = cx[pick] + rad * np.cos(th), cy[pick] + rad * np.sin(th)
        return x % w, y % h, th

    xs, ys, ths, got, top = [], [], [], 0, terr.max()
    while got < n:  # rejection sampling against the territory
        m = 2 * (n - got) + 64
        if kind == "uniform":
            x, y = rng.random(m) * w, rng.random(m) * h
            th = rng.random(m) * 2 * math.pi
        elif kind == "disc":
            rad = min(h, w) * 0.42 * np.sqrt(rng.random(m))
            ang = rng.random(m) * 2 * math.pi
            x, y = w / 2 + rad * np.cos(ang), h / 2 + rad * np.sin(ang)
            th = ang + math.pi  # facing inward
        else:
            raise ValueError(f"unknown init {kind!r}")
        keep = rng.random(m) * top < terr[y.astype(int) % h, x.astype(int) % w]
        xs.append(x[keep]), ys.append(y[keep]), ths.append(th[keep])
        got += int(keep.sum())
    cut = lambda parts: np.concatenate(parts)[:n]
    return cut(xs) % w, cut(ys) % h, cut(ths)


def _blur(trails):
    """3x3 box blur of every map in a (k, h, w) stack, wrapping at the edges."""
    a = trails + np.roll(trails, 1, 2) + np.roll(trails, -1, 2)
    return (a + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 9.0


def simulate(points, territories, inits, h, w, rng, steps=360, scale=1.0, couple=0.3, emphasis=0.7):
    """Run one species per point; returns the combined trail map (h, w),
    each species scaled to the same contrast within its territory.

    points       list of Point, one per tag
    territories  list of (h, w) weight maps (sum to 1 per pixel) — where each
                 species lives: it spawns and deposits in proportion to it
    inits        initial layout per species
    couple       how much a species also follows the other species' trails
    emphasis     visual weight of each later species relative to the previous
    """
    k = len(points)
    terr = np.stack(territories).astype(np.float32)
    # trail magnitudes differ with decay/deposit; `norm` brings them to one
    # scale when species sense each other
    norm = np.array([(1 - p.decay) / p.deposit for p in points], np.float32)[:, None, None]
    decay = np.array([p.decay for p in points], np.float32)[:, None, None]
    diffuse = np.array([p.diffuse for p in points], np.float32)[:, None, None]
    deposit = np.stack([p.deposit * t for p, t in zip(points, terr)])
    mirror = np.stack([p.mirror * np.sqrt(t * t[:, ::-1]) / 2 for p, t in zip(points, terr)])

    agents = []
    for p, t, init in zip(points, terr, inits):
        n = max(1, int(p.agents * t.sum()))
        x, y, th = _spawn(init, n, t, rng)
        agents.append([x, y, th, np.cos(th), np.sin(th)])
    trails = np.zeros((k, h, w), np.float32)

    for _ in range(steps):
        total = (trails * norm).sum(0)
        for i, (p, init) in enumerate(zip(points, inits)):
            x, y, th, vx, vy = agents[i]
            n = len(x)
            field = trails[i] + couple * (total - trails[i] * norm[i]) / norm[i]

            def sample(px, py):
                return field[py.astype(np.int64) % h, px.astype(np.int64) % w]

            s = np.minimum(sample(x, y) * p.gain, 1.0)

            def param(t):
                return t[0] + t[1] * s ** t[2]

            sd = param(p.sd) * scale
            sa = np.radians(param(p.sa))
            ra = np.radians(param(p.ra))
            md = np.maximum(param(p.md), 0.05) * scale

            # sense ahead / left / right, then turn toward the strongest
            c = sample(x + sd * np.cos(th), y + sd * np.sin(th))
            l = sample(x + sd * np.cos(th - sa), y + sd * np.sin(th - sa))
            r = sample(x + sd * np.cos(th + sa), y + sd * np.sin(th + sa))
            coin = np.where(rng.random(n) < 0.5, -1.0, 1.0)
            turn = np.where(
                (c >= l) & (c >= r), 0.0,
                np.where((c < l) & (c < r), coin, np.where(l > r, -1.0, 1.0)),
            )
            th = th + turn * ra
            th = th - p.level * np.sin(2 * th)  # settle toward 0 / pi

            # move, optionally smoothed by a velocity (bleuje's inertia)
            dx, dy = np.cos(th), np.sin(th)
            vx, vy = 0.9 * vx + 0.1 * dx, 0.9 * vy + 0.1 * dy
            a = p.inertia
            x = (x + md * ((1 - a) * dx + a * vx)) % w
            y = (y + md * ((1 - a) * dy + a * vy)) % h

            if p.respawn > 0:
                redo = rng.random(n) < p.respawn
                if redo.any():
                    x[redo], y[redo], th[redo] = _spawn(init, int(redo.sum()), terr[i], rng)

            # deposit sqrt(count) per pixel (bleuje), capped, scaled by territory
            idx = (y.astype(np.int64) % h) * w + (x.astype(np.int64) % w)
            count = np.bincount(idx, minlength=h * w).reshape(h, w)
            trails[i] += np.sqrt(np.minimum(count, 16)).astype(np.float32) * deposit[i]
            agents[i] = [x, y, th, vx, vy]

        # partial 3x3 diffusion, decay, then fold onto the mirror image where asked
        trails = (trails + diffuse * (_blur(trails) - trails)) * decay
        trails += mirror * (trails[:, :, ::-1] - trails)

    # give every species the same contrast inside its own territory, so faint
    # organisms (soft labyrinths) are not drowned out by tight bright lines;
    # earlier tags then weigh a little more, as they do in territory
    out = np.zeros((h, w), np.float32)
    for i, (tr, t) in enumerate(zip(trails, terr)):
        home = tr[t > 0.5] if (t > 0.5).any() else tr.ravel()
        out += emphasis**i * tr / (np.percentile(home, 99.5) + 1e-9)
    return out


# ===========================================================================
# MIXING TAGS
# ===========================================================================
def territories_for(tags, h, w, slug, cells=2.0, falloff=0.25, sharp=8.0):
    """One smooth weight map per tag (a softmax over noise fields).

    The first tag claims the most ground, each later one `falloff` times less;
    `sharp` sets how crisp the borders between territories are.
    """
    raw = []
    for i, tag in enumerate(tags):
        rng = np.random.default_rng(seed_from(slug, tag, "territory", str(i)))
        noise = _smooth_noise(h, w, rng, cells)
        noise = np.argsort(np.argsort(noise, axis=None)).reshape(h, w) / noise.size
        raw.append((falloff**i) * np.exp(sharp * noise))  # rank-equalised above, so
        # every draw gives the same shares and only the shapes change
    raw = np.stack(raw)
    return list(raw / raw.sum(axis=0, keepdims=True))


def lookup(tag, slug):
    if tag not in TAGS:
        raise ValueError(f"unknown tag {tag!r} on {slug}; known: {sorted(TAGS)}")
    return TAGS[tag]


# ===========================================================================
# RENDER
# ===========================================================================
def tone(trail, lo=35, hi=99.5, gamma=0.7):
    """Trail map -> ink coverage in [0,1]."""
    a, b = np.percentile(trail, [lo, hi])
    return np.clip((trail - a) / (b - a + 1e-9), 0, 1) ** gamma


def to_png(cover, path, size=None, ink=INK):
    """cover in [0,1] = ink opacity. RGBA PNG on transparent paper.
    `size` (w, h) downsamples the supersampled render (Lanczos) before saving."""
    if size is not None:
        img = Image.fromarray(cover.astype(np.float32), "F").resize(size, Image.LANCZOS)
        cover = np.clip(np.asarray(img), 0, 1)
    h, w = cover.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = ink
    rgba[..., 3] = np.round(cover * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)


def make_fingerprint(slug, tags, out=OUT, steps=360):
    specs = [lookup(t, slug) for t in tags]
    rng = np.random.default_rng(seed_from(slug, *tags))
    n = SIZE * RES
    terr = territories_for(tags, n, n, slug)
    trail = simulate([s["point"] for s in specs], terr, [s["init"] for s in specs], n, n, rng, steps, scale=RES)
    yy, xx = (np.mgrid[0:n, 0:n] + 0.5) / n
    vig = np.clip((0.5 - np.hypot(xx - 0.5, yy - 0.5)) / 0.12, 0, 1)  # soft round token
    to_png(tone(trail) * vig, out / f"{slug}.png", size=(THUMB_PX, THUMB_PX))


def make_hero(tags, out=OUT, seed="hero", steps=420):
    """All of the site's tags, each growing in its own region and blending at the seams."""
    specs = [lookup(t, "hero") for t in tags]
    rng = np.random.default_rng(seed_from(seed))
    w, h = 2240, 600
    terr = territories_for(tags, h, w, seed, cells=6.0, falloff=0.9)
    trail = simulate([s["point"] for s in specs], terr, [s["init"] for s in specs], h, w, rng, steps, scale=3.2)
    to_png(tone(trail, lo=30), out / "hero.png", size=HERO_PX)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    pubs = [(slugify(p["title"]), p.get("tags", [])) for p in load_publications()]
    site_tags = list(dict.fromkeys(t for _, tags in pubs for t in tags))
    make_hero(site_tags)
    print("hero.png <-", ", ".join(site_tags))
    for slug, tags in pubs:
        make_fingerprint(slug, tags)
        print(f"{slug[:40]:40s} <- {', '.join(tags)}")
    print("done ->", OUT)
