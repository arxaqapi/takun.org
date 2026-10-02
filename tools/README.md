# Physarum art generator

`gen_physarum.py` grows the site's art with a slime-mould (physarum) agent
simulation, after [bleuje's explanation](https://bleuje.com/physarum-explanation/)
of Jeff Jones' model and Sage Jenson's "36 points" extension:

- `art/hero.png` is the header band. Every tag used on the site gets its own
  region, and the regions blend at the seams.
- `art/<slug>.png` is one **fingerprint** per publication, grown from its tags.

## Usage

```bash
uv run tools/gen_physarum.py   # deps (numpy, pillow) are declared inline
python tools/build.py          # refresh the Publications HTML
```

A full run takes about 3 min. Output is deterministic: seeds come from the slug and tags.

Everything is **supersampled**. The simulation runs at `RES` (3) times the
reference grid (336 px per thumbnail, 2240×600 for the hero), then it's
downsampled with Lanczos to `THUMB_PX` (224) and `HERO_PX` (1680×450). That
keeps the filaments thin and crisp at any pixel density.

## The model

Each agent senses the trail map at three points (left, ahead, right), turns
toward the strongest, moves, and deposits `sqrt(count)` per pixel. The map is
then partially blurred (3×3) and decays. Sensor distance, sensor angle, rotation
angle and move distance each depend on the trail value `x` under the agent:
`base + amp * x**exp`. One full parameter set is a `Point`.

## Tags = species, mixed spatially

Each tag in `TAGS` is a `Point` plus an initial layout (`uniform`, `disc` or
`seed`). For a paper with several tags, every tag gets a smooth noise-shaped
**territory**, and runs as its own **species**, after Sage Jenson's
multi-species physarum. Each species has its own population and trail map. It
spawns and deposits in proportion to its territory, and it also senses the
other species' trails a little (`couple`, 0.3), so neighbouring organisms meet
and intertwine at the borders.

- The first tag claims the most ground. Each later tag gets `falloff` (0.25)
  times less, and is drawn at `emphasis` (0.7) times the weight.
- Each species is shown at the same contrast inside its own territory, so soft
  organisms aren't drowned out by bright, tight lines.
- Reordering tags changes which one dominates.

Blending the parameters themselves (bleuje's point mixing) was tried first. At
high resolution, almost every blend settled into the same generic mesh, so the
tags stopped reading as distinct.

| tag               | organism                                              |
|-------------------|-------------------------------------------------------|
| `speech`          | silky streams drifting horizontally (waveform-ish)    |
| `longform`        | long, slow, smoky sweeping filaments (high inertia)   |
| `self-supervised` | thick coral labyrinth: sensors reach and splay further in dense trail |
| `benchmark`       | stable polygonal mesh (classic reticular network)     |
| `evolution`       | veins branching out from a few colonies               |
| `analogy`         | mirrored veins (trail folded onto its reflection)     |
| `child`           | scattered beads and short dashes                      |

## Adding a tag

Add an entry to `TAGS`. You don't need new code:

```python
"cross-lingual": dict(
    point=Point(sd=(6, 0, 1), sa=(30, 20, 1), ra=(25, 0, 1), md=(1, 0, 1),
                inertia=0.4, decay=0.9, diffuse=0.3),
    init="uniform",
),
```

Unknown tags raise an error that lists the valid ones. Useful knobs:

- `sd` (sensor distance) sets the feature scale. It's measured in pixels on the 112 px reference grid.
- `sa > ra` gives static meshes. `ra > sa` gives restless, contracting forms.
- `inertia` smooths paths into long curves. `level` biases headings toward horizontal.
- `decay` and `diffuse` set how long trails persist and how soft they look.
- `mirror` sets bilateral symmetry. `respawn` sends agents back to their starting layout.

## Output

PNG ink on transparent paper. The alpha channel holds the toned trail density,
so the CSS background shows through and dark mode inverts it with a filter.
