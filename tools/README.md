# Dithered art generator

Generates the 1-bit Floyd–Steinberg art used on the site:

- `dither/hero.png` — the layered dithered landscape band in the header.
- `dither/<slug>.png` — one **fingerprint** per publication, composed from tags.

## Usage

```bash
pip install pillow numpy
python tools/gen_dither.py
```

Output is written to `../dither/` relative to the script.

## How fingerprints work

Each paper is a `(slug, [tags])` entry in the `PAPERS` list. A fingerprint is
built by compositing one visual primitive per tag, so papers with different tags
look genuinely different, while the per-slug seed keeps each image unique and
stable across runs.

- The **first tag anchors** the composition (dominant silhouette); later tags
  layer in with decreasing weight (`0.7 ** position`).
- Reordering a paper's tags changes which feel dominates.

## Tag feels

Each tag has its own characteristic look (defined in `TAG_FEELS`):

| tag               | feel                                                    |
|-------------------|---------------------------------------------------------|
| `speech`          | horizontal waveform / spectrogram bands                 |
| `longform`        | slow low-frequency horizontal drift                     |
| `self-supervised` | dense interfering ripples (moiré / emergent structure)  |
| `benchmark`       | crisp measurement grid / checkered lattice              |
| `evolution`       | branching Voronoi cellular web                           |
| `analogy`         | mirrored symmetry with a central seam (A:B :: C:D)      |
| `child`           | soft, calm, low-frequency blobs                          |

## Adding a publication

1. Add an entry to `PAPERS`, e.g.
   ```python
   ("my-new-paper", ["speech", "self-supervised"]),
   ```
   (unknown tags raise an error listing the valid ones.)
2. Re-run the script.
3. Reference it in `index.html`:
   ```html
   <div class="paper-thumb">
     <img src="dither/my-new-paper.png" alt="" width="44" height="44" loading="lazy" />
   </div>
   ```

## Adding a new tag feel

Write a `feel_<name>(n, rng) -> np.ndarray` returning a field in ~[0,1]
(higher = more ink), then register it in `TAG_FEELS` and give it a weight in
`TAG_WEIGHT`. Keep it visually distinct from the existing feels.

## Tweaking

- `SIZE` sets fingerprint resolution (upscaled ×2 on save, nearest-neighbour).
- `to_png(..., ink=(r,g,b))` shifts the ink colour. Paper stays transparent so
  the CSS background shows through; dark mode inverts via CSS.
- `make_hero(...)` builds the header band (layered ridgelines + sky gradient).
