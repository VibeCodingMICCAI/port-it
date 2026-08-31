# Port It! — MATLAB → Python

### Same behaviour, new language.

An AI-assisted software migration stand for **Vibe Coding in Medical Imaging:
Responsible LLM-Assisted Programming at MICCAI 2026**.

Your starting point is [`masker.m`](masker.m): a compact MATLAB tool for viewing
2D or 3D medical images and interactively painting a binary mask. Your goal is a
simple, readable, one-file Python version that reproduces its behaviour.

> **Do not improve the tool yet. First reproduce what it actually does.**

## Your challenge

Ask a coding agent to study `masker.m`, implement `masker.py`, test what can be
tested automatically, and report how closely the result matches the source. The
final result should be:

- one self-contained Python application;
- a minimalist, responsive image annotation GUI; and
- a short behavioural-equivalence report that makes any platform adaptations clear.

The repository includes a reference [`masker.py`](masker.py). For a clean attempt,
tell your agent not to inspect it until its first implementation is complete—or
copy `masker.m` into an otherwise empty folder.

## Analyse first, or start with one shot?

For this stand, a short **analysis-first, then iterate** workflow is the better
default. Ask the agent—not the participant—to extract a compact behaviour
inventory, briefly inspect it together, then implement and audit. This keeps the
vibe-coding pace while making assumptions visible. A pure one-shot is an
interesting speed comparison, but silent omissions are more likely; writing a
complete specification yourself would miss the point of asking the agent to read
the source. The prompt below supports both: use it unchanged for one message, or
ask the agent to pause after its inventory for a two-pass run.

## Main prompt

Open the repository in your coding agent and paste this:

```text
Port the local masker.m into a single-file Python application named masker.py.

This is a behavioural migration, not a redesign. Treat the executable MATLAB
code—not its comments and not what you think the app ought to do—as the source of
truth. Read the whole file before editing. First build a behaviour inventory
covering inputs, preprocessing, state, every callback, boundary cases, return
modes, and saving; then implement from that inventory.

Requirements:
- Keep the application self-contained, simple, and readable, using NumPy and
  Matplotlib, with the same minimalist image-first GUI. Do not add panels,
  sliders, menus, annotation classes, or unrelated features.
- Support 2D and 3D intensity images and an optional existing mask. Preserve the
  source's dimensional compatibility rules, empty-mask initialisation, exact
  label cutoff, type conversion, global normalisation, and edge-case behaviour.
- Reproduce the interactions exactly: wheel through slices; left-click/drag to
  paint; right-click/drag to erase; hold s, c, or a while scrolling to change
  brush size, contrast, or mask opacity. Match scroll directions, defaults,
  increments, limits, modifier precedence and key state, boundary behaviour, and
  the circular brush's pixel geometry.
- Preserve the display calculation, random mask colour, guide behaviour, figure
  lifetime, blocking/return modes, and every close/save path.
- Treat continuous-drag responsiveness as part of the behaviour. Use vectorised
  NumPy operations, reuse display artists and state, cache repeated array work
  where useful, and avoid Python loops over pixels or rebuilding the GUI during
  motion events.
- Provide a natural callable Python API and a minimal command-line entry point
  for .npy images and optional masks/output. If Python requires a different file
  format, coordinate convention, or API convention, make it an explicit minimal
  adaptation and document the exact difference. Do not silently substitute new
  behaviour.

Verification is part of the task:
1. Compare masker.py with masker.m callback by callback after implementation.
2. Run syntax checks and deterministic headless tests for all non-visual logic,
   including 2D/3D inputs, singleton dimensions, incompatible shapes, empty and
   existing masks, thresholding, normalisation, brush add/erase, state bounds,
   return shapes, and saving.
3. Fix every unintended mismatch that you find; do not stop merely because the
   window opens or the code compiles.
4. Finish with a concise table whose rows are marked "exact match", "deliberate
   platform adaptation", or "still needs human GUI verification".

The output is one Python file plus that behavioural-equivalence report.
```

## If the first pass needs another look

These follow-up prompts work best in the same agent conversation, where the
source analysis and implementation are still in context.

### Prompt 2 — forensic parity pass

```text
Now perform a forensic parity review. Re-read masker.m from scratch and treat it
as the oracle, even where a comment disagrees with executable code. Map each
input rule, state variable, display calculation, callback branch, bound, return
path, and save path to masker.py. Exercise the Python callbacks with synthetic
2D and 3D arrays and test edge cases. Fix every unintended mismatch without
redesigning the UI. Finish with three lists only: exact matches,
unavoidable/documented Python adaptations, and checks that still require a
person at the GUI.
```

### Prompt 3 — responsiveness pass

```text
Review only the interactive update path. Painting and erasing should remain
responsive on a representative 3D medical image. Check for per-pixel Python
loops, repeated figure or artist construction, unnecessary full-volume work
during mouse motion, avoidable allocations, and excessive synchronous redraws.
Improve efficiency only where the visible MATLAB behaviour remains unchanged,
then explain and test each change.
```

### Prompt 4 — prepare a human test

```text
Test this interactive scientific GUI in two layers. First run headless checks for
validation, thresholding, normalisation, brush footprints, callback state
transitions, bounds, returned shapes, and saving. Then create small synthetic 2D
and 3D inputs and give me exact launch commands plus a five-minute human
acceptance script. Include expected results for wheel direction and boundaries,
click and continuous drag, right-button erase, all modifier-plus-wheel controls,
cursor/brush alignment, closing/return/saving, and responsiveness. Do not claim
end-to-end equivalence until I report those observations; use my observations to
diagnose and repair failures.
```

## Why can 220 lines take a while?

`masker.m` has only about 220 executable lines, but it is a small event-driven
application rather than a simple numerical function. Those lines cover:

- 2D/3D shape handling, empty-mask creation, mask thresholding, and image normalisation;
- slice, brush, contrast, opacity, mouse-button, and key-held state;
- click and continuous-drag painting or erasing with a circular brush;
- bounded wheel actions whose meaning changes while `s`, `c`, or `a` is held;
- additive image/mask rendering and responsive display updates;
- window lifetime, blocking return behaviour, and optional saving on close; and
- edge cases at image borders, slice limits, and parameter limits.

A plausible-looking window can still be a poor port. Give the agent time to read
the whole source, trace its callbacks, construct the GUI, run checks, and compare
the result back against MATLAB. This may take longer than the file size suggests.

## Controls to reproduce

| Input | Behaviour |
|---|---|
| Mouse wheel | Move through slices |
| Left-click or left-drag | Paint mask |
| Right-click or right-drag | Erase mask |
| `s` + wheel | Change brush radius |
| `c` + wheel | Change image contrast |
| `a` + wheel | Change mask opacity |

## Before calling the port equivalent

Ask the agent for evidence for each item rather than accepting a checked box on
faith alone:

- [ ] 2D/3D inputs, singleton dimensions, empty masks, existing masks, and incompatible shapes match MATLAB.
- [ ] Normalisation, thresholding, initial values, increments, bounds, and callback priority match the code.
- [ ] Slice scrolling stops at both volume boundaries and moves in the expected direction.
- [ ] Clicks and held-button drags paint or erase the correct circular footprint, including near borders.
- [ ] `s`, `c`, and `a` modify the right state while held and stop when released.
- [ ] Mask colour, contrast, opacity, guide, window chrome, and overlay calculation have been compared.
- [ ] Repeated drawing remains responsive on a realistically sized volume.
- [ ] Viewing-only, blocking return, closing, saving, HDF5/MAT behaviour, and existing-output handling were traced.
- [ ] Every necessary Python-specific change is documented rather than silently called equivalent.

## How should an interactive port be tested?

This is an open question for the stand. Automated checks can cover array shapes,
thresholding, normalisation, brush footprints, state bounds, callback transitions,
and saved output. They cannot fully answer whether wheel direction feels right on
a particular GUI backend, a held drag produces a continuous stroke, the cursor
matches the edited pixels, or interaction stays responsive.

A practical human-in-the-loop comparison is to open the same synthetic or sample
image in MATLAB and Python side by side, follow the same short interaction script,
and compare the resulting masks as arrays—not only as screenshots. Try slow and
fast drags, both mouse buttons, every modifier, image borders, first/last slices,
and closing with and without an output path.

What would convince you that the interaction is equivalent: a paired screen
recording, an observer checklist, exported-mask comparison, latency measurements,
or some combination of these? Try a method and share what it catches that
code-only tests miss.

## Try it on a real 3D prostate MRI

[`download_sample.py`](download_sample.py) downloads an anonymised, multi-slice
prostate MRI and matching manual label from the
[SPL/NCIGT dataset on Zenodo](https://doi.org/10.5281/zenodo.16396). It verifies
the published checksums and converts the compressed NRRD files into NumPy arrays
with shape `(512, 512, 27)`:

```bash
python download_sample.py
python masker.py sample_data/prostate_mri.npy \
  --output sample_data/my_mask.npy
```

To inspect and edit the supplied prostate contour instead:

```bash
python masker.py sample_data/prostate_mri.npy \
  --mask sample_data/prostate_mask.npy
```

The downloader also writes column-major raw arrays so the original MATLAB and
Python tools can be exercised on the same voxels. The included capture scripts
make this comparison reproducible:

```bash
python capture_python_screenshot.py
matlab -batch "capture_matlab_screenshot"
```

### Python tool on the prostate MRI

![Python Masker showing the supplied prostate mask](docs/images/masker-python.png)

This image was exported from the real `Masker` figure, not mocked up. The MATLAB
capture command writes `docs/images/masker-matlab.png` from the original
`masker.m`; it should be run in a MATLAB environment so that the second image is
an authentic capture rather than a visual reconstruction.

## Reference implementation

The included [`masker.py`](masker.py) is one compact NumPy/Matplotlib outcome. It
uses NumPy `.npy` files for its command-line interface:

```bash
python -m pip install numpy matplotlib
python masker.py image.npy --mask existing-mask.npy --output edited-mask.npy
```

Both options are optional. You can also call it from Python:

```python
import numpy as np
from masker import masker

image = np.load("image.npy")
edited_mask = masker(image)
```

Use the reference after your first attempt as another object to question and
compare—not as proof that every interaction is correct on every GUI backend.
Its `.npy` saving convention is a deliberate Python adaptation; the MATLAB source
has distinct MAT and HDF5 paths.

## Source and acknowledgement

The included [`masker.m`](masker.m) is an unmodified copy of Yipeng Hu's
[Masker source](https://github.com/YipengHu/matlab-common-tools/tree/master/Masker),
written at the UCL Centre for Medical Image Computing in August 2017. The
upstream project is MIT-licensed. This stand repository uses the license in
[`LICENSE`](LICENSE).

The downloaded sample and screenshots containing it are derived from *Annotated
MRI and ultrasound volume images of the prostate* by Fedorov, Nguyen, Tuncali,
and Tempany, licensed
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). The files
are converted from NRRD to NumPy/raw arrays and displayed with Masker. These
sample-derived materials are not covered by this repository's Apache-2.0 license;
see [`docs/images/README.md`](docs/images/README.md).
