# Magnetostatic B-field of a current-carrying wire — Ansys Maxwell 3D via PyAEDT

A minimal, **working** PyAEDT 1.4 example that drives Ansys Electronics Desktop
**Student** 2025 R2 from Python: it builds a copper wire, excites it with 5 A,
solves a magnetostatic setup, and exports |B| along a radial line to CSV.

The script is short. Getting it to run on the *Student* edition was not — this
repo documents every failure and its fix, because most of them produce error
messages that point nowhere near the actual cause.

> **If you landed here from a search for**
> `Failed to start new AEDT gRPC session on port ...` **with the Student
> version — go straight to [The gRPC bug](#the-grpc-bug-the-one-that-actually-blocks-you).**

---

## What it computes

A copper cylinder (r = 2 mm, L = 50 mm) along Z, carrying 5 A, inside a vacuum
region. |B| is sampled along a line from r = 3 mm to r = 20 mm in the wire's
midplane.

| r | Solver | Analytic (finite segment) | Infinite-wire formula |
|---|--------|---------------------------|-----------------------|
| 3 mm | 327 µT | 332 µT | 333 µT |
| 20 mm | 36 µT | 39 µT | 50 µT ❌ |

The analytic check must use the **finite** segment form on the midplane:

```
B = μ₀·I·L / (2·π·r·√(L² + 4r²))
```

The familiar `B = μ₀I / (2πr)` only holds while `r ≪ L`. With a 50 mm wire it
already over-predicts by ~28 % at r = 20 mm. That is physics, not a solver
error — do not "fix" the model to chase it.

Sample output is committed at [`results/B_Field_Data.csv`](results/B_Field_Data.csv)
(1001 points, semicolon-separated).

---

## Requirements

| | |
|---|---|
| Ansys Electronics Desktop | **Student** 2025 R2 (build 2025.2.4) |
| Install path (this machine) | `G:\Program Files\ANSYS Inc\ANSYS Student\v252\AnsysEM` |
| Python | 3.12 (3.12.10 tested) |
| PyAEDT | 1.4.0 |

PyAEDT locates the install through the `ANSYSEMSV_ROOT252` environment variable,
which the Student installer sets for you. Verify it before debugging anything
else:

```powershell
$env:ANSYSEMSV_ROOT252
# G:\Program Files\ANSYS Inc\ANSYS Student\v252\AnsysEM
```

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
python magnetic_field_wire.py
```

Expected tail:

```
PyAEDT INFO: Design setup Setup1 solved correctly in 0.0h 0.0m 10.0s
Simulation complete. B-field data exported to: ...\B_Field_Data.csv
```

AEDT launches in graphical mode (`non_graphical=False`). The Student edition is
single-instance: if a session is already open, PyAEDT attaches to it rather than
starting a second one.

The script is **idempotent** — it deletes and recreates the wire and region and
reuses an existing `Setup1`, so you can re-run it against the same project
without tripping over stale objects.

---

## The gRPC bug (the one that actually blocks you)

### Symptom

```
PyAEDT INFO: New AEDT session is starting on gRPC port 58101.
PyAEDT ERROR: Failed to start on gRPC port: 58101.
PyAEDT INFO: New AEDT session is starting on gRPC port 58541.
Exception: Failed to start new AEDT gRPC session on port 58541 on machine 127.0.0.1.
```

Meanwhile AEDT windows keep piling up on screen, and `batch.log` cheerfully
reports the server *did* start.

### Diagnosis

AEDT is fine. It launched, and it is listening:

```
> Get-CimInstance Win32_Process -Filter "Name='ansysedtsv.exe'" | Select CommandLine
"G:\...\ansysedtsv.exe" -grpcsrv 58101

> netstat -ano | findstr 58101
TCP    127.0.0.1:58101    0.0.0.0:0    LISTENING    48372
```

PyAEDT simply cannot see it. In
`ansys/aedt/core/generic/general_methods.py:1341`:

```python
def is_grpc_session_active(port, machine=None):
    ...
    return True if port in active_sessions().values() else False
```

`active_sessions()` is called **without `student_version=True`**, so it scans
only for `ansysedt.exe` and never for `ansysedtsv.exe`. On this machine:

```python
>>> active_sessions()
{}                                    # what PyAEDT looks at
>>> active_sessions(student_version=True)
{48372: 58101, 18936: -1, 3716: -1}   # reality
```

So `launch_aedt()`'s readiness loop never breaks, burns the full
`settings.desktop_launch_timeout`, and reports failure. PyAEDT then retries on a
*new* port — but AEDT is single-instance, so the retry just attaches to the
already-running app and never opens that port. Hence the second failure, and the
orphaned AEDT windows.

### Fix

Three lines at the top of the script, before constructing `Maxwell3d`:

```python
import ansys.aedt.core.desktop as _desktop
from ansys.aedt.core.generic.general_methods import active_sessions

def _is_grpc_session_active(port, machine=None):
    return port in active_sessions(student_version=True).values()

_desktop.is_grpc_session_active = _is_grpc_session_active
```

`desktop.py` imports the symbol at module level, so patching it on the module
covers both `launch_aedt()` and `Desktop._validate_port()`.

### What does *not* fix it

A widely-copied "solution" is to force the insecure transport:

```python
os.environ["PYAEDT_USE_PRE_GRPC_ARGS"] = "True"
settings.grpc_secure_mode = False
settings.grpc_local = False
```

This is unrelated to the failure and makes things worse — it abandons the
Windows-native WNUA transport that is the default on Windows. Verified on this
machine: the launch fails identically with and without those lines. Delete them.

---

## Every other thing that breaks

Full evidence and reproduction for each is in
[`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

| # | Error | Cause | Fix |
|---|-------|-------|-----|
| 1 | `Failed to start new AEDT gRPC session` | PyAEDT 1.4.0 ignores `ansysedtsv.exe` | monkeypatch above |
| 2 | `'Maxwell3d' object has no attribute 'AXIS'` | `app.AXIS` removed in 1.x | `from ansys.aedt.core.generic.constants import Axis` → `Axis.Z` |
| 3 | `create_region()` ignores padding | `pad_percent` renamed | `pad_value=[...]`, `pad_type="Percentage Offset"` |
| 4 | `Illegal external terminal 'I_5A'` | wire floats inside the region | Z padding **must be 0** so the end faces sit on the boundary |
| 5 | `Verify conduction path 'Path1'` | only one current terminal | second terminal on the opposite face, `swap_direction=True` |
| 6 | `'Fields' object has no attribute 'export_to_csv'` | removed in 1.x | `plot.get_solution_data().export_data_to_csv(path)` |

Two of these (#4, #5) are **modelling** errors, not API errors: magnetostatic
current excitations are *external terminals*, so a conduction path needs two of
them and both must reach the problem boundary.

### Reading the real error

`analyze_setup()` returning `False` tells you nothing. The solver message is in
AEDT's message window:

```python
for m in m3d.odesktop.GetMessages("Wire_B_Field", "Wire_B_Field", 0):
    print(m)
```

That is how #4 and #5 were identified. Always check this before guessing.

---

## Cleaning up orphaned sessions

Failed launches leave `ansysedtsv.exe` running. They hold a license and block
the next run:

```powershell
Get-Process ansysedtsv -ErrorAction SilentlyContinue | Select Id, StartTime
Stop-Process -Name ansysedtsv
```

---

## Layout

```
magnetic_field_wire.py     the example, documented inline
requirements.txt           pinned, verified versions
results/B_Field_Data.csv   sample solver output
docs/TROUBLESHOOTING.md    full diagnosis of each failure
```
