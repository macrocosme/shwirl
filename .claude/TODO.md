# shwirl TODO

Future work / deferred items. Newest context at top.

## New items (2026-07-08)

- [x] **Python API + Jupyter integration** — done (`shwirl/api.py`, `[notebook]`
      extra, `examples/shwirl_api_demo.ipynb`). Follow-ups:
      - [ ] README + PyPI blurb showcasing the API (screenshot/GIF from the notebook)
      - [ ] Sphinx/API docs page for `shwirl.api`
      - [ ] SoFiA mask/catalog overlay (natural next step on top of the API)
      - [ ] Verify `canvas()` live path with jupyter_rfb actually installed

- [ ] **At release time: convert `DEVELOPMENT_NOTES.md` → `CHANGELOG.md`.** Adopt
      Keep a Changelog format (`[Unreleased]` → versioned section on tag, with
      Added/Changed/Fixed); keep it terse/user-facing (the narrative "why" can go in
      the PR/commit body). Archive `DEVELOPMENT_NOTES.md` to `archive/` afterwards.

- [ ] **Bug: top-down view stops rendering the galaxy.** With the transfer
      function viewed from top to bottom (looking down the line of sight / a
      particular camera orientation), the galaxy is no longer rendered. Likely a
      ray-casting entry/exit or face-culling issue in `render_volume.py`
      (`set_gl_state('translucent', cull_face=False)`, or the near/far ray setup)
      — investigate which orientation triggers it and why the ray returns empty.
- [ ] **Histogram widget + auto-range selection.** Add a data-value histogram
      panel and functions to auto-pick a sensible dynamic range (e.g. percentile
      clip / z-scale / median±k·MADFM) to drive clim and the stretch. Scaffolding
      already exists but is unused: `Canvas3D.histogram()` + `scene.Histogram`
      (`shwirl/shwirl.py`), the commented `# self.histogram(data.ravel())` call,
      and `self.view_histogram` grid slot (row=1, col=0). Wire it to the clim /
      discard-filter controls.
- [ ] **3D galaxy modelling to complement the visualisation.** Fit/overlay a
      kinematic galaxy model alongside the rendered cube. Reference: GBKFIT
      (GPU/CUDA kinematic modelling, fast; developed by a colleague) — look for a
      current/maintained version or equivalent. Keep it simple and user-friendly
      (sensible defaults, minimal parameters exposed). Scope TBD: model overlay
      vs. full in-app fitting.

## SAMI test cube won't load (deferred 2026-07-08)

**Symptom:** `test-data/511867_red_8_Y13SAR1_P005_15T018.fits.gz` fails with
`OSError: Empty or corrupt FITS file`.

**Root cause (diagnosed):** the file is **not FITS** — it's a 339-byte **HTML page**
(`file` reports "HTML document text"; `gzip -t` says "not in gzip format"; first bytes are
`<!DOCTYPE HTML ...`). The download from the SAMI EDR browser
(https://sami-survey.org/edr/browser) saved an HTML error/landing page under a `.fits.gz`
name, not the actual cube. So astropy is correct to reject it; shwirl's error is accurate.

**To do:**
- [ ] Re-download the real cube. The EDR browser page URL is not a direct data link — find the
      actual data/download endpoint (may need the survey's data-access URL or auth). Verify the
      result is real gzip'd FITS: `file X.fits.gz` → "gzip compressed data", `gzip -t X.fits.gz`
      passes, decompressed head begins with `SIMPLE  =`.
- [ ] Re-test loading once a genuine cube is in hand. SAMI cubes are a good stress test for the
      new loader: they're multi-extension (primary flux cube + variance/weight HDUs) and
      ~50×50×2048 — exercises `find_data_hdu` HDU selection and the axis handling.
- [ ] (Enhancement) Detect non-FITS content up front and give a clearer message than "corrupt":
      if the (decompressed) first bytes aren't a FITS `SIMPLE` card / look like `<!DOCTYPE`/HTML,
      say "this looks like an HTML or error page, not a FITS file — re-download". Hook point:
      `shwirl/fits_loader.py::open_fits` / `_friendly`.

## FITS-loading work — not yet committed (2026-07-08)

- [ ] Commit the robust FITS loader + dimension selection + render fixes on
      `macrocosme/modernize` (files: `shwirl/fits_loader.py`, `shwirl/shwirl.py`,
      `shwirl/shaders/render_volume.py`, `shwirl/tests/{test_file_loading,test_render}.py`,
      `.claude/CLAUDE.md`). Exclude the large untracked real cubes in the repo root / `test-data/`.
- [ ] Decide whether `environment.yml` (untracked, not authored by this work) should be tracked.

## Carry-over modernization (from CLAUDE.md)

- [ ] Linux parity check (CI covers import + lint + headless tests; GL render is opt-in).
- [ ] Phase 5: PyPI re-release (bump/tag, build sdist+wheel, publish).
- [ ] Optional: refresh Sphinx docs / readthedocs.
- [ ] Optional: fix the `get_interpolation_fun` dead-code infinite recursion in
      `render_volume.py`.
