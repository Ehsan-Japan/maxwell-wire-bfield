# Troubleshooting log

Every failure hit while getting `magnetic_field_wire.py` to run, in the order it
surfaced, with the evidence used to diagnose it.

Environment: Windows 11 Pro 26200 · AEDT Student 2025 R2 (2025.2.4, build
2025-11-06) · Python 3.12.10 · PyAEDT 1.4.0 · install at
`G:\Program Files\ANSYS Inc\ANSYS Student\v252\AnsysEM`.

---

## 1. `Failed to start new AEDT gRPC session on port 58541 on machine 127.0.0.1`

**Where:** `desktop.py:3308`, raised out of `Maxwell3d.__init__`.

### Observed

```
PyAEDT INFO: AEDT version 2025.2SV Student.
PyAEDT INFO: New AEDT session is starting on gRPC port 58101.
PyAEDT INFO: Launching AEDT server with gRPC transport mode: TransportMode.INSECURE
PyAEDT ERROR: Failed to start on gRPC port: 58101.
PyAEDT INFO: New AEDT session is starting on gRPC port 58541.
Exception: Failed to start new AEDT gRPC session on port 58541 on machine 127.0.0.1.
```

Followed by:

```
Exception ignored in: <function Desktop.__del__>
AttributeError: 'Desktop' object has no attribute '_Desktop__close_on_exit'
```

That trailing `AttributeError` is noise — `__del__` runs on a `Desktop` whose
`__init__` never completed. It is a symptom, not a cause.

### Evidence that AEDT was fine

AEDT's own `batch.log` after a "failed" run:

```
Ansys Electronics Desktop Student Version 2025.2.4
Starting Batch Run: 2:07:24 AM  Aug 28, 2026
[info] gRPC server started on port 58101 of local host.
```

Processes still alive, and the port genuinely listening:

```
> Get-CimInstance Win32_Process -Filter "Name='ansysedtsv.exe'" | Select ProcessId,CommandLine
48372   "G:\...\ansysedtsv.exe" -grpcsrv 58101
18936   "G:\...\ansysedtsv.exe" -grpcsrv 58101

> netstat -ano | findstr LISTENING | findstr 58101
TCP    127.0.0.1:58101    0.0.0.0:0    LISTENING    48372
```

### Root cause

`launch_aedt()` (`desktop.py:306`) polls readiness with:

```python
timeout = settings.desktop_launch_timeout
while timeout > 0:
    if is_grpc_session_active(port, host):
        break
    timeout -= 1
    time.sleep(1)
```

and `is_grpc_session_active` (`generic/general_methods.py:1341`) ends with:

```python
return True if port in active_sessions().values() else False
```

`active_sessions()` defaults to `student_version=False`, so it enumerates
`ansysedt.exe` only. Confirmed directly:

```python
>>> from ansys.aedt.core.generic.general_methods import active_sessions, is_grpc_session_active
>>> active_sessions()
{}
>>> active_sessions(student_version=True)
{48372: 58101, 18936: -1, 3716: -1}
>>> is_grpc_session_active(58101, '127.0.0.1')
False
```

Consequences chain:

1. The poll loop never breaks → full `desktop_launch_timeout` elapses.
2. `launch_aedt()` returns `(False, 0)`.
3. `Desktop.__init_grpc` retries with a fresh port from `_find_free_port()`.
4. AEDT is single-instance: the second `ansysedtsv.exe` hands off to the running
   app and exits without opening the new port.
5. Second failure → exception.

The same function backs `Desktop._validate_port()` (`desktop.py:3097`), so even
an explicit `port=58101, new_desktop=False` is overridden:

```
PyAEDT WARNING: No active AEDT gRPC session found on port 58101. Opening a new AEDT session.
Exception: Failed to start new AEDT gRPC session on port 57447 ...
```

### Fix, and proof it works

```python
import ansys.aedt.core.desktop as _desktop
from ansys.aedt.core.generic.general_methods import active_sessions

def _is_grpc_session_active(port, machine=None):
    return port in active_sessions(student_version=True).values()

_desktop.is_grpc_session_active = _is_grpc_session_active
```

```
PyAEDT INFO: Found active AEDT gRPC session on port 58101.
PyAEDT INFO: Connected to AEDT gRPC session on port 58101.
CONNECTED OK -> Probe | Project2
```

### Ruled out

The script originally carried:

```python
os.environ["PYAEDT_USE_PRE_GRPC_ARGS"] = "True"
settings.grpc_secure_mode = False
settings.grpc_local = False
```

Removing them changes nothing about the failure — a clean-default launch fails
identically. They *do* change the transport: with defaults
(`grpc_secure_mode=True`, `grpc_local=True`) `_get_grpcsrv_args()` selects
`TransportMode.WNUA` on Windows; setting `grpc_secure_mode=False` forces
`TransportMode.INSECURE`. WNUA is the supported local path on Windows, so the
lines were deleted.

Also ruled out: a too-short `desktop_launch_timeout`. Raising it does not help,
because the detector never returns `True` regardless of how long you wait.

### Upstream

PyAEDT 1.4.0. `is_grpc_session_active()` needs to propagate a `student_version`
flag (or probe both executables). Until then the monkeypatch is required for any
Student-edition automation.

---

## 2. `AttributeError: 'Maxwell3d' object has no attribute 'AXIS'`

```python
wire = m3d.modeler.create_cylinder(orientation=m3d.AXIS.Z, ...)
```

The `app.AXIS` / `app.PLANE` shortcuts are gone in the 1.x `ansys.aedt.core`
namespace. The enum moved:

```python
from ansys.aedt.core.generic.constants import Axis
...
orientation=Axis.Z
```

`Axis.Z` is `2`. The string `"Z"` also works.

Note: `list(Axis)` raises `TypeError: expected 1 argument, got 0` — the class has
a custom `__getitem__`. Do not iterate it while exploring; just use `Axis.X` /
`Axis.Y` / `Axis.Z`.

---

## 3. `create_region(pad_percent=...)` silently wrong

Signature in 1.4.0:

```python
Modeler3D.create_region(self, pad_value=300, pad_type='Percentage Offset',
                        name='Region', **kwarg)
```

`pad_percent` was absorbed by `**kwarg` and ignored. Use:

```python
m3d.modeler.create_region(
    pad_value=[500, 500, 500, 500, 0, 0],
    pad_type="Percentage Offset",
)
```

Order is `[+X, -X, +Y, -Y, +Z, -Z]`.

---

## 4. `Illegal external terminal 'I_5A'`

`analyze_setup()` returned `False` with only `PyAEDT ERROR: Error in Solving
Setup Setup1` — useless. The real message came from the AEDT message window:

```python
for m in m3d.odesktop.GetMessages("Wire_B_Field", "Wire_B_Field", 0):
    print(m)
```

```
[error] Illegal external terminal 'I_5A': An external terminal must border the
edge of the problem region and coincides with the surface of a 3D object.
[error] Simulation completed with execution error on server: Local Machine.
```

**Cause:** the region was padded 10 % in ±Z, so the wire's end faces floated
inside the vacuum region. A magnetostatic current excitation is an *external
terminal* — it must lie on the problem boundary.

**Fix:** zero the Z padding so the end faces are coincident with the region
boundary:

```python
pad_value=[500, 500, 500, 500, 0, 0]
```

Radial padding stays large (500 %) so the far field is not clipped.

---

## 5. `Verify conduction path 'Path1'`

```
[error] Verify conduction path 'Path1': For any conduction path that has current
excitation(s) specified, at least two external current excitations should be
specified.
```

One terminal defines no path. Current must enter and leave:

```python
m3d.assign_current(assignment=[wire.top_face_z.id],    amplitude=5, solid=True, name="I_in")
m3d.assign_current(assignment=[wire.bottom_face_z.id], amplitude=5, solid=True,
                   swap_direction=True, name="I_out")
```

`swap_direction=True` reverses the normal on the return face. After this the
setup solved in ~10 s.

---

## 6. `'Fields' object has no attribute 'export_to_csv'`

`export_to_csv()` no longer exists on report objects. The near-miss is
`export_table_to_file`, but it is not the right call:

```python
CommonReport.export_table_to_file(plot_name, output_file, table_type='Marker')
```

It exports **marker/legend tables**, not trace data, and takes two positional
arguments. Calling it with one gives:

```
TypeError: CommonReport.export_table_to_file() missing 1 required positional argument: 'output_file'
```

For the actual curve, go through the solution data:

```python
plot.get_solution_data().export_data_to_csv(csv_path)
```

Output is semicolon-separated:

```
Distance [mm];Mag_B (Real) [tesla];Mag_B (Imag) [tesla]
0.0;0.00032748503745731364;0.0
```

`PostProcessor3D.export_report_to_csv(project_dir, plot_name, ...)` is the
alternative if you want AEDT to write the file itself.

---

## 7. `setup.props` changes that never take effect

```python
setup.props["MaximumPasses"] = 5
```

mutates the local dict only. Push it to AEDT:

```python
setup.update()
```

Without this the solve silently uses the default adaptive pass count.

---

## 8. Physics: the analytic check in the original comments was wrong

The script claimed 333 µT at r = 3 mm and 50 µT at r = 20 mm from
`B = mu0*I/(2*pi*r)`. The solver gave 327 µT and 36 µT, and the solver is
right — that formula is for an *infinite* wire.

Finite segment of length `L`, evaluated on the midplane:

```
B = mu0*I*L / (2*pi*r*sqrt(L^2 + 4*r^2))
```

| r | Finite-segment analytic | Solver | Infinite-wire |
|---|---|---|---|
| 3 mm | 332 µT | 327 µT | 333 µT |
| 20 mm | 39 µT | 36 µT | 50 µT |

Agreement is ~1.5 % at r = 3 mm and ~8 % at r = 20 mm (mesh density at the far
edge of the extraction line). The comment block was corrected rather than the
model.

---

## Housekeeping

Failed launches leave AEDT processes running; they hold a Student license and
interfere with the next attempt.

```powershell
Get-Process ansysedtsv -ErrorAction SilentlyContinue | Select Id, StartTime
Stop-Process -Name ansysedtsv
```

`batch.log` in the working directory accumulates one block per launch and is the
first place to look when a session misbehaves. It is gitignored.
