# HANDOFF — takun.org personal academic website

This document is written for **another LLM** picking up this project. It explains
what the site is, how every piece fits together, the design decisions and their
rationale, how to make common changes safely, and the sharp edges to avoid. Read
it fully before editing. When you finish a task, keep this file up to date.

---

## 0. TL;DR / orientation

- It's a **single static HTML page** (`index.html`) for Tarek Kunze, an ML
  research engineer working on child speech / long-form audio. No framework, no
  build server. Deploy = copy the folder to any static host.
- Aesthetic: **1-bit dithered ("riso"/field-notebook) art on warm paper**, warm
  serif + mono, one muted oxblood accent. Inspired by slightknack.dev,
  deuxfleurs.fr, jzhao.xyz.
- Two generated things: a **hero landscape band** and a **unique dithered
  "fingerprint" thumbnail per publication**, both produced by
  `tools/gen_dither.py` using organic value-noise textures.
- Publications are data in **`publications.toml`** (the single source of truth).
  `tools/build.py` renders them into `index.html` between marker comments.
- A **compositional tag system** drives the fingerprints: a "tag" is a *recipe*
  (data) combining reusable base **elements** + **modifiers**. Adding a tag =
  adding a recipe, not code.
- `tools/bibconvert.py` converts `publications.toml` <-> `publications.bib`
  (transparent round-trip), so the `.bib` is just an export.

If you do nothing else, run this to confirm a healthy tree:

```bash
pip install -r tools/requirements.txt
python tools/gen_dither.py     # regenerate all art -> dither/
python tools/build.py          # regenerate the Publications HTML in index.html
python tools/build.py --check  # exits 0 if index.html is in sync
```

---

## 1. Repository layout

```
index.html                 the whole site (one page). Publications section is generated.
app.css                    all styling (light + dark, responsive, print).
publications.toml          SOURCE OF TRUTH for publications (bib fields + tags + links).
publications.bib           EXPORT, regenerated from the toml. Do not treat as source.
robots.txt, favicon.ico    static assets.
*.svg / *.png (root)       social icons (GitHub, ORCID, Google Scholar).
dither/                    GENERATED art. hero.png + one <slug>.png per publication.
tools/
  build.py                 toml -> index.html (stdlib only; no third-party deps).
  gen_dither.py            generates dither/*.png (needs numpy, scipy, pillow).
  bibconvert.py            toml <-> bib converter (needs bibtexparser, tomli-w).
  authors.py               who is "me" (bold) + co-author website links.
  requirements.txt         python deps for the generators/converters.
  README.md                user-facing docs (workflow). THIS FILE is the deep dive.
```

Everything the visitor sees is `index.html` + `app.css` + `dither/` + the icons.
The `tools/` and `publications.*` files are authoring machinery.

---

## 2. Data flow (how a change propagates)

```
publications.toml ──► build.py ──► index.html (Publications section, between markers)
        │
        └──► gen_dither.py ──► dither/<slug>.png   (slug = slugify(title))
                                dither/hero.png

authors.py ──► build.py (author display: initials, bold "me", co-author links)

publications.toml ◄──► bibconvert.py ◄──► publications.bib   (export / import)
```

Key invariant: **the slug is derived from the title** by `slugify()`, defined
once in `build.py`. `gen_dither.py` imports and calls it as `build.slugify(...)`,
so there is a single definition and the two cannot drift. `build.py` writes
`<img src="dither/<slug>.png">`; `gen_dither.py` writes that same file. There is
no stored slug — it is always recomputed from the title.

`gen_dither.py` imports the publication list from `build.py`
(`build.load_publications()` + `build.slugify`) so the paper set lives in ONE
place. There's a hardcoded fallback list inside `gen_dither.py` used only if
`build.py`/tomllib can't be imported — **if you add/rename papers, the fallback
goes stale; that's fine as long as the normal import path works, but don't rely
on the fallback.**

---

## 3. publications.toml — the schema

Each publication is one `[[publication]]` block. Order in the file == order on
the page (newest first). Example (all fields shown):

```toml
[[publication]]
key = "kunze25_interspeech"        # bibtex citation key (unique id)
type = "inproceedings"             # bibtex entry type
title = "Challenges in Automated Processing of Speech from Child Wearables: ..."
authors = ["Tarek Kunze", "Marianne Métais", "..."]   # "First Last" order
year = 2025
booktitle = "Interspeech 2025"     # or journal / publisher / address / ...
pages = "2845--2849"
doi = "10.21437/Interspeech.2025-1962"
issn = "2958-1796"

# website extras (not standard bibtex):
tags = ["speech", "benchmark", "child"]        # drives the dithered thumbnail
preprint = "https://arxiv.org/abs/2506.11074"  # -> "preprint" link
code = "https://github.com/LAAC-LSCP/VTC-IS-25"# -> "code" link

[publication.materials]            # any number of named links
paper = "https://www.isca-archive.org/.../kunze25_interspeech.pdf"
poster = "papers/2025_IS_vtc_poster_interspeech_1962.pdf"
```

### How fields become HTML (see `build.py::render`)
- **Title link** → `doi` if present, else `preprint`, else `#`.
- **Authors** → initials (`Marvin Lavechin` → `M. Lavechin`,
  `Kaveri K. Sheth` → `K. K. Sheth`); the site owner is `<b>`-bold and never
  linked; co-authors in `authors.py::AUTHOR_SITES` become links.
- **Link row** → `code`, `preprint`, then each `[publication.materials]` entry.
  Ordered by `LINK_ORDER = [paper, code, preprint, poster, slides, video]`, then
  any extras. A `preprint` equal to the title link is suppressed (no duplicate).
  If a paper has no links at all, the `<div class="links">` is omitted entirely.
- **`tags`** never render as text; they only pick `dither/<slug>.png`.

### Adding a publication
1. Add a `[[publication]]` block (with `tags`) in the desired page position.
2. `python tools/gen_dither.py` (creates its `dither/<slug>.png`).
3. `python tools/build.py` (updates `index.html`).

---

## 4. build.py — toml → HTML

- Pure standard library on Python 3.11+ (uses `tomllib`). No third-party deps.
- Injects generated `<article>` blocks **between markers** in `index.html`:
  ```
  <!-- PUBLICATIONS:START (generated by tools/build.py — do not edit) -->
  ...
  <!-- PUBLICATIONS:END -->
  ```
  Idempotent: it only rewrites between the markers; everything else in the page
  is left byte-for-byte. First run (no markers) replaces whatever is between
  `<h2>Publications</h2>` and `</section>`.
- `--check` exits non-zero if the page is stale — good for CI / pre-commit.
- Functions worth knowing: `slugify` (imported by gen_dither as
  `build.slugify` — single definition, don't duplicate it), `initials`,
  `format_authors`, `collect_links`, `render`, `inject`.

**Sharp edge:** `slugify` is defined only here and imported by `gen_dither.py`.
If you change slug rules, gen_dither picks them up automatically via the import —
do not copy the function into gen_dither (that would reintroduce drift risk).

---

## 5. authors.py — author display config

```python
ME = "Tarek Kunze"
ME_ALIASES = ["Tarek Kunze", "T. Kunze"]     # any spelling -> bold, never linked
AUTHOR_SITES = {                              # full name -> URL (rendered as link)
    "Maxime Poli": "https://mpoli.fr/",
}
```
Matching is accent/case-insensitive on the normalized full name. The `.bib`
stores `Last, First`; `build.py` normalizes to `First Last` for lookup. To link a
co-author, add one line to `AUTHOR_SITES`.

---

## 6. bibconvert.py — toml <-> bib (transparent round-trip)

```bash
python tools/bibconvert.py to-bib    # publications.toml -> publications.bib
python tools/bibconvert.py to-toml   # publications.bib  -> publications.toml
```

Design contract (agreed with the site owner):
- The **toml is the source of truth**; the `.bib` is an export for sharing.
- **`preprint` is a plain field**, round-tripped as `preprint = {url}` in bibtex.
  There is NO separate `@misc` arXiv companion entry; the owner adds preprints
  manually as a `preprint` field. `to-toml` maps each bib entry to exactly one
  publication and **preserves .bib file order**.
- Website-only fields (`tags`, `code`, `materials`) don't exist in bibtex, so
  they're omitted from `to-bib`. On `to-toml`, they're **preserved** from an
  existing `publications.toml` matched by `key`, so re-import never wipes them.
- Constants: `BIB_FIELDS` (standard fields + order), `WEBSITE_ONLY`, `TOML_ORDER`.

This file was unified from two earlier scripts (`bib2toml.py` + `toml2bib.py`) to
avoid duplicated field lists. Keep it single.

---

## 7. gen_dither.py — the art generator (the heart of the aesthetic)

Produces `dither/hero.png` and one `dither/<slug>.png` per publication. Needs
`numpy`, `scipy`, `pillow`. Run standalone: `python tools/gen_dither.py`.

### 7.1 Rendering primitives (top of file)
- `SIZE = 56` — base fingerprint resolution; saved at ×2 (112px) via `to_png`.
- `seed_from(*parts)` — deterministic int seed from strings (so art is stable
  across runs but unique per paper/tag). Fingerprints are seeded per (slug, tag).
- `floyd_steinberg(gray)` — 1-bit Floyd–Steinberg dithering; input is a float
  field in [0,1] where higher = more ink. This is what gives the riso look.
- `to_png(bits, path, ink=(31,29,26), scale=2)` — writes an **RGBA PNG with a
  transparent paper** (only ink pixels are opaque). This matters: the CSS paper
  background shows through, and dark mode inverts the art via a CSS filter.

### 7.2 Organic texture helpers (the "grown, not plotted" foundation)
These are why the art looks organic rather than mathematical:
- `_grid(n)` → normalized (x, y) coordinate arrays in [0,1], shape (n, n).
- `_smooth_noise(n, rng, scale)` → value noise = white noise blurred by
  `gaussian_filter(sigma=scale)`. **Signature is (n, rng, scale)** — see the
  guard; passing args out of order is the classic bug (a prior session hit
  `'int' object has no attribute 'standard_normal'` from a swapped call).
- `_fbm(n, rng, octaves, base, persistence)` → fractal Brownian motion (sum of
  value-noise octaves). The natural look of clouds/coastlines/growth.
- `_warp(x, y, n, rng, strength, scale)` → domain warp: nudges coordinates by
  noise so straight things bend (hand-drawn wobble). Returns warped (x, y).
- `_round_mask(n, feather)` → soft circular falloff to seat a token.

### 7.3 THE COMPOSITIONAL TAG SYSTEM (most important section)

A tag is **data, not code**. Three registries:

**ELEMENTS** — base texture generators, each `el_*(n, rng, **params) -> field`
in ~[0,1]:
| element      | look                                             |
|--------------|--------------------------------------------------|
| `blob`       | one soft rounded mass, noise-warbled edge        |
| `cells`      | warped Voronoi (cracked-mud / tissue growth)     |
| `strata`     | flowing horizontal sediment bands                |
| `trace`      | a signal-envelope band (waveform-ish)            |
| `turbulence` | dense marbled churn (fingerprint/oil-on-water)   |
| `lattice`    | hand-drawn wandering grid                        |
| `spots`      | scattered soft dots                              |
| `noise`      | plain fractal cloud (filler)                     |

**MODIFIERS** — `mod_*(field, n, rng, **params) -> field`, applied after
combining layers, in order:
| modifier   | effect                                             |
|------------|----------------------------------------------------|
| `mirror`   | bilateral symmetry + soft central gutter           |
| `bias`     | fade toward a side (before mirroring, etc.)        |
| `vignette` | soft round seating (keeps some edge content)       |
| `warp`     | extra hand-drawn wobble over the whole field       |
| `contrast` | steepen/soften around a pivot (busier/calmer)      |

**TAG_RECIPES** — the actual tags, as data:
```python
"self-supervised": {
    "layers": [("turbulence", {"scale": 9.0, "ridged": True}, 1.0)],
    "blend": "max",                                  # max | add | mul
    "modifiers": [("contrast", {"gain": 0.8, "pivot": 0.5})],
    "density": 0.5,                                  # optional: rescale mean ink
},
```
Recipe schema: `layers` = list of `(element, params, weight)`; `blend` = how
layers combine (`max` default = dominant silhouette; `add`; `mul`); `modifiers`
= ordered list of `(name, params)`; `density` (optional) rescales mean ink toward
a target after everything else.

**Engine:** `build_feel(recipe, n, rng)` runs a recipe → field. `feel_for_tag`
looks up a tag's recipe. `TAG_FEELS` wraps each tag as a callable so the older
`make_fingerprint` loop is unchanged. `TAG_WEIGHT` tunes how strongly each tag
pushes when a paper has several (first tag dominates via max-blend).

### 7.4 Composing a paper's fingerprint
`make_fingerprint(slug, tags)` seeds per (slug, tag), builds each tag's field,
combines with a **max-blend where the first tag anchors the silhouette** and
later tags decay (`0.65 ** i`), applies a gentle circular vignette, dithers, and
saves `dither/<slug>.png`. Densities are clipped (not rescaled) so sparse tags
stay sparse and busy tags stay busy.

### 7.5 The hero band
`make_hero(w=560, h=150, seed=11)` builds the header landscape:
`_hero_profile` makes organic fbm ridgelines (not stacked sines); three layered
ridges (far=high/light, near=low/dark) with noise-textured slopes; a mottled sky
gradient; then a **rectangle-safe domain warp** (the hero is 560×150, not square,
so it does NOT call `mod_warp`, which assumes square `n×n` — it inlines an
equivalent warp). Saved at ×2 → 1120×300, referenced in index.html.

### 7.6 Adding / editing a tag (the common request)
1. To combine existing looks: add an entry to `TAG_RECIPES`. No new code.
   Example new tag:
   ```python
   TAG_RECIPES["cross-lingual"] = {
       "layers": [("cells", {"count": 7, "warp": 0.15}, 1.0)],
       "blend": "max",
       "modifiers": [("bias", {"toward": "left"}),
                     ("mirror", {"axis": "x"}),
                     ("vignette", {"floor": 0.6})],
   }
   ```
2. To invent a genuinely new *look*: add `el_<name>(n, rng, **params)` to
   `ELEMENTS` (return a field in ~[0,1]) or a `mod_<name>` to `MODIFIERS`, then
   reference it from recipes.
3. Regenerate: `python tools/gen_dither.py`.

Unknown tags raise a helpful `ValueError` listing valid ones.

### 7.7 Quality bar (how to verify art changes — you likely can't see images)
A prior session often couldn't render preview images, so it verified
**quantitatively**. Reuse this harness. Targets that held for the current design:
- **Distinctness:** min pairwise pixel-difference between the real fingerprints
  ≈ **0.28–0.32** (anything > ~0.15 is clearly distinguishable). Compute by
  loading each `dither/<slug>.png`, taking the alpha channel > 128 as the ink
  mask, and averaging `|A − B|` over all pairs.
- **Organic-ness (edge isotropy):** with `scipy.ndimage.sobel`, isotropy =
  `sqrt(gx²+gy²).sum() / (|gx|+|gy|).sum()` per field; **0.76–0.94** means edges
  point in all directions (organic). Low values = axis-aligned/mechanical.
- **Density spread:** per-tag mean ink varies (~0.15–0.58), not all clustered.
- **Seed stability:** each tag varies across seeds but keeps its character.

**IMPORTANT — measuring ink from the PNGs:** the art is transparent-paper RGBA.
Do NOT `convert("L")` (that reads every pixel as black → density 1.0 for all, a
trap a prior session fell into). Use the **alpha channel**: `ink = alpha > 128`.

When you can, also save contact sheets to `/mnt/user-data/outputs/`
(`base-elements.png`, `tag-fingerprints.png`) so the human can eyeball them —
that's the judgment the metrics can't fully make.

---

## 8. app.css — the design system

- **Tokens** (`:root`): `--paper #f4f0e6`, `--ink #1f1d1a`, `--accent #8a2f24`
  (muted oxblood — deliberately desaturated so it doesn't read as the AI-default
  terracotta), plus `--paper-2`, `--ink-soft`, `--rule`, `--slate`,
  `--accent-rgb`. Fonts: `--serif` (body), `--mono` (labels/headings/dates).
  `--measure: 40rem` content width.
- **Dark mode** via `@media (prefers-color-scheme: dark)` swapping the tokens.
  Dither art is inverted in dark mode with a CSS `filter` on `.dither-band` and
  `.paper-thumb img` (because the PNGs are ink-on-transparent).
- Headings use a mono face with a printed `#`/`##` prefix via `::before`
  (`h2::before { content: "# " }`) — a terminal/markdown nod.
- `.dither-band` (hero) has `image-rendering: pixelated` and a mask that fades
  its top edge into the paper. `.paper-thumb img` are the 44px fingerprints,
  also pixelated.
- Layout: `.content` is a 2-col grid — a sticky identity rail (`--rail`,
  hero + name + role + socials) and the publication column (`--measure`).
  Papers are grouped by year: `.year-group` = sticky year label in a left
  gutter + the papers. Each paper is thumb + body; venue and links share one
  `.meta` line so entries stay ~4 lines tall (goal: most papers above the fold).
- Breakpoints: ≤52rem → single column, the rail becomes a compact header with
  the hero as a full-bleed 4rem strip (`object-fit: cover`); ≤34rem → year
  labels move above their group, smaller thumbs. Print styles hide art.

Keep formatting restrained: minimal bold, no heavy chrome. The vibe is quiet
field-notebook, not a dashboard.

---

## 9. index.html — the page

Hand-written except the Publications section (between the markers). Structure:
`.content` grid holding `.masthead` (hero `<img>`, `<h1>` name, `.role`,
`.socials` icons) and `<main>` with `<h2>Publications</h2>` and the generated
`<div class="year-group">` blocks (each wraps that year's `<article class="paper">`
entries; `build.py::build_block` groups consecutive same-year papers, so toml
order still decides page order) → `<footer>`. The venue is printed without the
year, since the group label already shows it. Uses KaTeX (CDN) for any math. Asset paths are relative so the page
works opened directly from disk. **Do not hand-edit between the PUBLICATIONS
markers** — run `build.py` instead.

---

## 10. Environment / running things

```bash
pip install -r tools/requirements.txt
# requirements: numpy, scipy, pillow (gen_dither); bibtexparser, tomli-w
# (bibconvert to-toml); tomli only for Python < 3.11. build.py itself is stdlib.
```
- Python 3.11+ assumed (stdlib `tomllib`). numpy 2.x is in use — note
  `array.ptp()` was removed; use `np.ptp(array)` (a prior session fixed one).
- Rendering a page screenshot (when the tool env allows) used Playwright +
  Chromium against `pathlib.Path("index.html").resolve().as_uri()`.
- Packaging for delivery in this environment: copy `flat/` (the working dir) into
  `pkg/takun-site/`, strip `__pycache__`, zip, copy to
  `/mnt/user-data/outputs/`, and present with the file tool. (The working copy
  during development lived at `/home/claude/flat`.)

---

## 11. History & rationale (why things are the way they are)

The project evolved through several deliberate refactors — respect these choices:
1. **Zola → plain HTML.** Originally a Zola static-site tree; flattened to a
   single `index.html` + `gen_dither.py` at the owner's request. No SSG.
2. **Per-paper meta → single source of truth.** Publication data consolidated
   into `publications.toml`; slugs derived from titles (no hand-named files).
3. **bibtex parser removed from build.** `build.py` reads toml directly; a
   separate `bibconvert.py` handles bib<->toml, unified from two scripts to kill
   duplicated field lists.
4. **Preprints simplified.** No auto `@misc` companion matching; `preprint` is a
   plain field the owner maintains. `to-toml` preserves .bib order.
5. **Fingerprints made organic.** Moved from geometric sine/grid feels to
   noise-grown textures (fbm + domain warp) after "these feel artificial".
6. **Tag system made compositional.** Bespoke `feel_<tag>` functions replaced by
   `ELEMENTS` + `MODIFIERS` + `TAG_RECIPES` so new tags are pure data — the
   owner wanted to add tags in the future without writing code.
7. **Hero made organic** to match the fingerprints (fbm ridgelines + warp).

Guiding principles the owner has shown: **single source of truth; transparent /
round-trippable data; no unnecessary dependencies; simple, single-file tools;
organic over mechanical; extensibility without code.**

---

## 12. Gotchas checklist (read before editing)

- [ ] `slugify` is defined once in `build.py` and imported by `gen_dither.py`
      as `build.slugify`. Change it in one place; don't duplicate it.
- [ ] Art PNGs are **transparent-paper RGBA**; measure ink via **alpha**, not
      luminance. `convert("L")` gives density 1.0 for everything (a known trap).
- [ ] `_smooth_noise(n, rng, scale)` — argument ORDER matters; a swapped call
      gives `'int' object has no attribute 'standard_normal'`. Same care for
      `_fbm(n, rng, ...)` and `_warp(x, y, n, rng, ...)`.
- [ ] `mod_warp` assumes a **square** field; the hero is rectangular and inlines
      its own warp. Don't call `mod_warp` on non-square fields.
- [ ] numpy 2.x: use `np.ptp(a)`, not `a.ptp()`.
- [ ] `publications.bib` is an **export** — edit `publications.toml`, then run
      `bibconvert.py to-bib`. Don't treat the `.bib` as source.
- [ ] `build.py` is **idempotent** and only touches text between the PUBLICATIONS
      markers. Never hand-edit inside them.
- [ ] After any art change, regenerate ALL of `dither/` (`gen_dither.py`) and run
      `build.py --check` so slugs and files stay in sync.
- [ ] Child-speech research context: keep copy factual and professional.

---

## 13. Suggested next steps (open ideas, not commitments)

- An "About"/bio section, or a blog/notes area matching the aesthetic.
- Per-tag legend/gallery page rendering `base-elements.png` + tags inline.
- Retina `srcset` for the fingerprints, or an animated/video hero variant.
- A tiny CI check running `build.py --check` on commit.
- More base elements/modifiers (e.g. `flow-field`, `stipple`, `posterize`) to
  widen the tag vocabulary.

Confirm scope with the owner before large additions; they value simplicity.

---

## 14. Definition of done for any change

1. `python tools/gen_dither.py` runs clean (exit 0, 8 files incl. hero).
2. `python tools/build.py && python tools/build.py --check` → "up to date".
3. Every `dither/<slug>.png` referenced in `index.html` exists.
4. If art changed: distinctness/isotropy metrics still in target ranges (§7.7).
5. `bibconvert.py to-bib` still round-trips if you touched toml/bib logic.
6. Update `tools/README.md` (user docs) and THIS file if behavior changed.
```
