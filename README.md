# Magnetostatics from scratch — a current-carrying wire in Ansys Maxwell 3D

One conductor, one current, one field. This repo takes the simplest problem in
magnetostatics all the way through a real finite-element solver, driven from
Python with PyAEDT, and then asks the two questions every FEA result has to
survive:

- does it match the theory?
- and how much of what I'm seeing is *the physics* versus *my discretisation
  and my boundary*?

Each of those gets its own script, its own data, and its own figure.

| | |
|---|---|
| [1. The model](#1-the-model) | what gets built, and why the region is shaped that way |
| [2. The theory](#2-the-theory) | Ampère's law inside and outside the conductor |
| [3. The simulation](#3-the-simulation) | what the solver returns |
| [4. Theory vs simulation](#4-theory-vs-simulation) | the validation, with a residual |
| [5. Effect of mesh refinement](#5-effect-of-mesh-refinement) | numerical error you can shrink |
| [6. Effect of the region padding](#6-effect-of-the-region-padding) | boundary error you can shrink |
| [Running it](#running-it) | setup, commands, files |

---

## 1. The model

A copper cylinder, r = 2 mm, L = 50 mm, along **Z**, carrying **5 A**, sitting
in a vacuum region. |B| is sampled along a straight line in the wire's
midplane, from r = 3 mm out to r = 20 mm.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/isometric-dark.png">
  <img src="docs/images/isometric.png" alt="Isometric view of the model: copper cylinder spanning the full height of the vacuum region box, current terminals on the top and bottom boundary faces, a circular B field line around the wire, and the radial extraction line">
</picture>

That is a schematic, drawn from the same numbers the script uses. For the real
thing — AEDT's own isometric viewport — run:

```powershell
python studies/capture_model_image.py     # needs AEDT, solves nothing
```

<!-- figure appears here once the capture has been run:
<picture>
  <img src="docs/images/aedt_model.png" alt="Isometric screenshot of the model in the Ansys Electronics Desktop viewport">
</picture>
-->

The same thing from two orthogonal directions, with dimensions and the field
direction marked:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/geometry-dark.png">
  <img src="docs/images/geometry.png" alt="Left: XZ side view of the model to scale, with the wire, vacuum region, the two current terminals on the region boundary and the extraction line. Right: XY view down the wire, showing circular B field lines around the current and the extraction line crossing them at 90 degrees.">
</picture>

| | |
|---|---|
| Solution type | Magnetostatic |
| Conductor | cylinder along Z, r = 2 mm, L = 50 mm, centered at the origin |
| Material | copper |
| Region | vacuum, `pad_value = [500, 500, 500, 500, 0, 0]` %, `pad_type = "Percentage Offset"` |
| Excitation | `I_in` 5 A on the +Z end face; `I_out` 5 A on the −Z end face, `swap_direction=True` |
| Setup | `Setup1`, `MaximumPasses = 5` |
| Extraction | polyline (3, 0, 0) → (20, 0, 0) mm |

The right-hand view is the one to keep in your head: **B is azimuthal**. It
circles the current, it has no radial or axial component here, and the
extraction line is radial — so it cuts those circles at 90° and every sample is
pure B_φ. That is why a single scalar |B| versus r is the whole answer.

Two things in there are worth understanding rather than copying:

**The ±Z padding is 0.** A magnetostatic current excitation is an *external
terminal* — the face it sits on has to be on the outer boundary of the problem,
because that is where the current is understood to come from and go to. Pad the
region in Z and the wire floats inside it; both terminals are then illegal and
the solve stops.

**There are two current terminals, not one.** Current has to enter somewhere and
leave somewhere. A conduction path with a single terminal has nowhere to send
the 5 A, and the solver refuses it. `I_out` is the same 5 A with
`swap_direction=True`.

Both of those are modelling facts about magnetostatics, not quirks of the API.

---

## 2. The theory

Before looking at any solver output, know what the answer should be. Everything
on this figure comes from Ampère's law and Biot–Savart — no simulation:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/theory-dark.png">
  <img src="docs/images/theory.png" alt="Left: |B| rising linearly inside the conductor and falling as 1/r outside. Right: the ratio of finite-segment to infinite-wire field versus radius">
</picture>

**Inside the conductor** (r < a), a circular Ampèrian loop encloses only the
fraction (r/a)² of the total current, so

```
B = μ₀·I·r / (2π·a²)          rising linearly from 0 on the axis
```

**Outside** (r > a) the loop encloses all of it:

```
B = μ₀·I / (2π·r)             falling as 1/r
```

so |B| peaks exactly at the conductor surface — 500 µT here — and there is no
field maximum anywhere else to look for.

**But the wire is only 50 mm long.** The 1/r law is the infinite-wire limit. For
a straight segment of length L, on its midplane, Biot–Savart gives

```
B = μ₀·I·L / (2π·r·√(L² + 4r²))
```

which is the infinite result multiplied by `L / √(L² + 4r²)` — the right-hand
panel above. At r = 3 mm that factor is 99 %, so the textbook formula is fine.
At r = 20 mm it is 78 %: the infinite formula over-predicts by 28 %. **That gap
is physics, not solver error.** Comparing a finite model against the infinite
formula and "fixing" the model to close the gap is the classic first mistake.

---

## 3. The simulation

What Maxwell 3D actually returns along the extraction line:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/simulation-dark.png">
  <img src="docs/images/simulation.png" alt="Left: solver |B| versus radius. Right: the same data log-log against a 1/r guide line">
</picture>

327 µT at r = 3 mm down to 36 µT at r = 20 mm. The log–log panel is the useful
one: a pure 1/r field is a straight line of slope −1 there, and the solver curve
starts at about −1.1 and steepens to −1.5. It is decaying **faster** than 1/r,
which is exactly what section 2 predicts for a finite wire.

Raw data: [`results/B_Field_Data.csv`](results/B_Field_Data.csv), 1001 points,
semicolon-separated.

---

## 4. Theory vs simulation

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/theory_vs_simulation-dark.png">
  <img src="docs/images/theory_vs_simulation.png" alt="Solver, finite-segment theory and infinite-wire theory versus radius, with the solver-minus-theory residual below">
</picture>

| r | Solver | Theory (finite segment) | Infinite-wire formula |
|---|--------|-------------------------|-----------------------|
| 3 mm | 327 µT | 332 µT | 333 µT |
| 20 mm | 36 µT | 39 µT | 50 µT ❌ |

Always plot the residual, not just the overlay — two curves on a log axis look
like they agree long after they stop agreeing. Here the solver sits within a few
percent of the finite-segment theory across the sweep and drifts to about −7 %
at the far end.

That drift is the interesting part, and it is *not* physics. Sections 5 and 6
separate the two numerical causes.

---

## 5. Effect of mesh refinement

> Run [`studies/study_mesh.py`](studies/study_mesh.py) in AEDT to produce this
> figure — it needs the solver, so it is not committed.

FEA solves the field on a mesh of tetrahedra. Where the mesh is coarse relative
to how fast the field is changing, the answer is wrong — and at large r the
elements are big and |B| is small, which is why the residual in section 4 grows
outward.

The study solves the identical geometry and excitation with 1, 2, 3, 5 and 8
adaptive passes. Nothing physical changes between the cases; only the
discretisation does. So any movement in the answer is numerical error, and when
the answer *stops* moving you are mesh-converged.

```powershell
python studies/study_mesh.py        # ~5 solves, one design each
python tools/plot_mesh_study.py     # -> docs/images/mesh_study.png
```

<!-- figure appears here once the study has been run:
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/mesh_study-dark.png">
  <img src="docs/images/mesh_study.png" alt="|B| curves at increasing adaptive-pass counts, and the error at r = 20 mm flattening as the mesh refines">
</picture>
-->

Note that adaptive refinement is driven by the solver's own error estimate, so
`MaximumPasses` alone doesn't guarantee a finer mesh — AEDT stops early once it
thinks it has converged. The study pins `MinimumPasses` and tightens
`PercentError` so each case really does get the mesh its pass count implies.

---

## 6. Effect of the region padding

> Run [`studies/study_padding.py`](studies/study_padding.py) in AEDT to produce
> this figure.

You cannot mesh infinity. The region is where free space gets truncated, and its
outer face carries a boundary condition. Put that face close and you are no
longer solving "a wire in free space" — you are solving "a wire in a box", and
the field nearest the wall is the most wrong.

The study sweeps the ±X/±Y padding over 500, 750, 1000, 2000 and 4000 %, putting
the wall at 22, 32, 42, 82 and 162 mm from the axis, with the mesh settings held
fixed. Those five regions, to scale — no solver needed to draw them:

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/region_sizes-dark.png">
  <img src="docs/images/region_sizes.png" alt="Left: XY footprints of the five region sizes as nested squares around the wire and extraction line. Right: XZ profiles at the same scale, showing that only the side walls move while the top and bottom faces stay put.">
</picture>

Note what does *not* change: the ±Z faces. Only the side walls move, because the
terminals have to stay on the top and bottom boundary. And note the price — the
4000 % region is 54× the volume of the 500 % one, and all of it gets meshed and
solved. When the answer stops depending on where the wall is, the region is big
enough; anything past that is compute you spent for nothing.

```powershell
python studies/study_padding.py        # ~5 solves, one design each
python tools/plot_padding_study.py     # -> docs/images/padding_study.png
```

<!-- figure appears here once the study has been run:
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/images/padding_study-dark.png">
  <img src="docs/images/padding_study.png" alt="|B| curves at increasing region sizes, and the error at r = 20 mm flattening as the boundary moves away">
</picture>
-->

Nothing below 500 % is usable here, and that is its own lesson: the region wall
would land at 18 mm while the extraction line runs out to 20 mm. Sampling a
field outside the solution domain doesn't give you a bad answer, it gives you a
meaningless one. **Size the region around what you intend to measure, not just
around the geometry.**

The ±Z padding stays 0 in every case — see section 1.

---

## Running it

| | |
|---|---|
| Ansys Electronics Desktop | **Student** 2025 R2 (build 2025.2.4) |
| Python | 3.12 (3.12.10 tested) |
| PyAEDT | 1.4.0 |

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

python magnetic_field_wire.py          # the main solve, exports the CSV
```

Expected tail:

```
PyAEDT INFO: Design setup Setup1 solved correctly in 0.0h 0.0m 10.0s
Simulation complete. B-field data exported to: ...\B_Field_Data.csv
```

The figures are generated separately and need no AEDT at all — they read the
committed CSVs:

```powershell
python -m pip install -r requirements-plot.txt
python tools/plot_all.py               # every figure; skips studies with no data
```

### Layout

```
magnetic_field_wire.py            the main example, documented inline
studies/common.py                 shared model builder — all AEDT-side scripts
studies/capture_model_image.py    exports AEDT's own isometric viewport image
studies/study_mesh.py             sweeps adaptive passes      -> results/mesh/
studies/study_padding.py          sweeps region padding       -> results/padding/
tools/vizstyle.py                 shared plot style + the analytic formulas
tools/plot_isometric.py           §1  the model in 3D
tools/plot_geometry.py            §1  the model, XZ and XY views
tools/plot_theory.py              §2  analytic only
tools/plot_simulation.py          §3  solver only
tools/plot_theory_vs_simulation.py §4  the validation
tools/plot_mesh_study.py          §5  mesh convergence
tools/plot_region_sizes.py        §6  the five region sizes, to scale
tools/plot_padding_study.py       §6  boundary convergence
tools/plot_all.py                 all of the above
results/B_Field_Data.csv          sample solver output (committed)
docs/images/                      figures, light + dark variants
docs/TROUBLESHOOTING.md           every failure hit while building this, and its fix
```

### If it won't launch

The script opens with a three-line monkeypatch of `is_grpc_session_active()`.
PyAEDT 1.4.0 scans for `ansysedt.exe` only, never `ansysedtsv.exe`, so on the
Student build it cannot see the gRPC server it just started and fails with
`Failed to start new AEDT gRPC session on port ...`. Keep those lines. That and
every other failure — illegal external terminals, conduction paths, the 1.x API
renames — is diagnosed in
[`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).
