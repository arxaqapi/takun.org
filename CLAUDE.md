# takun.org

Personal academic site for Tarek Kunze (ML research engineer, child speech /
long-form audio). One static page — no framework, no build server; deploy =
copy the folder. `archive/` (gitignored) is the old Zola site; ignore it.

## Commands

```bash
uv run tools/gen_physarum.py                         # regenerate all art -> art/ (~3 min)
python3 tools/build.py                               # render publications into index.html
python3 tools/build.py --check                       # exit 1 if index.html is stale
uv run tools/bibconvert.py -f assets/publications.toml   # toml -> bib export
uv run tools/bibconvert.py -f assets/publications.bib    # bib -> toml import
```

Scripts declare their deps inline (PEP 723) — run them with `uv run`, don't add
a requirements file. `build.py` is stdlib only. Preview: the `site` config in
`.claude/launch.json` (`python3 -m http.server 8765`).

## Layout & data flow

- `assets/publications.toml` — **single source of truth** for papers (bib fields
  + `tags`, `code`, `preprint`, `[publication.materials]`). File order = page order.
- `assets/publications.bib` — an export; edit the toml, then re-export.
- `tools/build.py` — injects `<article>`s into `index.html` between the
  `PUBLICATIONS:START/END` markers (idempotent; never hand-edit inside them).
  Also holds author config: `ME`, `ME_ALIASES` (bolded), `AUTHOR_SITES`
  (co-author links), `LINK_ORDER`.
- `tools/gen_physarum.py` — writes `art/hero.png` and `art/<slug>.png` per paper.
  Imports `slugify` / `load_publications` from `build.py`; `slugify` is defined
  only there — never duplicate it. Slugs are always derived from titles.
- `assets/app.css` — all styling (tokens on `:root`, dark mode, responsive, print).
  Dark mode = token overrides only, in two blocks kept in sync: system dark
  (`:root:not([data-theme="light"])`) and the footer toggle's pin
  (`:root[data-theme="dark"]`, saved in `localStorage.theme`). Put any new
  dark-mode difference in a token, not a separate rule.

Adding a paper: add a `[[publication]]` block with `tags`, run the generator,
then `build.py`.

## Art generator (gen_physarum.py)

Physarum agent simulation after https://bleuje.com/physarum-explanation/
(Jones' model + Jenson's trail-dependent parameters). `tools/README.md` has the
user-facing docs and the tag table. Key facts:

- A tag in `TAGS` is data: `Point(...)` (sd/sa/ra/md as `base + amp * x**exp`,
  plus inertia, level, decay, diffuse, mirror, …) + `init` (`uniform`/`disc`/`seed`).
  New tags need no new code; unknown tags raise with the valid list.
- **Mixing = species.** Each of a paper's tags gets a rank-equalised noise
  territory (`territories_for`: softmax, `falloff=0.25`, so the first tag leads
  ~50/30/20) and runs as its own population + trail map, spawning/depositing by
  territory and sensing others' trails at `couple=0.3`. Output = each species
  normalised to its own contrast, weighted `emphasis**i`. Parameter blending
  (bleuje's point mixing) was tried and dropped: blends collapse into a generic mesh.
- **Supersampled.** `Point` distances are pixels on the `SIZE=112` grid;
  simulation runs at `RES=3` (thumbs 336², hero 2240×600, `scale` multiplies
  SD/MD), then Lanczos-downsampled to `THUMB_PX=224` / `HERO_PX=(1680, 450)`.
  Changing RES changes the dynamics (the 3×3 blur covers less) — retune tags.
- Hero = every tag on the site (`falloff=0.9`, `cells=6`). `mirror` uses a
  symmetric mask, so only the area around the analogy territory is mirrored.
- Output is RGBA: ink colour with the toned trail as **alpha** on transparent
  paper. Dark mode inverts it via `--art-filter` on `.hero-band` / `.paper-thumb img`.
  Measure ink from alpha, never luminance. No `image-rendering: pixelated`.

Verifying art changes: parameters act non-linearly, so render contact sheets
(each tag alone at RES over a few seeds; every fingerprint at full size and at
44 px) into the scratchpad and look at them. When touching mixing, check each
paper's territory shares inside the round crop. Then run `build.py --check`.

## Conventions

- Owner values: single source of truth, no unnecessary deps, simple
  single-file tools, organic over mechanical, extensibility without code.
  Confirm scope before large additions.
- Aesthetic: quiet field notebook — warm paper, serif body, mono labels,
  one muted oxblood accent (`--accent`), minimal bold, no heavy chrome.
- Asset paths stay relative so `index.html` works opened from disk.
- Copy is about child-speech research: keep it factual and professional.
- After changing generator behaviour, update `tools/README.md` and this file.
