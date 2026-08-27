"""
Shared model builder for the parameter studies.

Both studies rebuild the same wire as magnetic_field_wire.py, but each case
goes into its **own design** inside one project, so the cases are independent:
a fresh mesh, a fresh solve, no state carried over from the previous run.

Nothing here is imported by the plotting scripts -- run these only where AEDT
is installed.
"""
import json
import os
import re

import ansys.aedt.core.desktop as _desktop
from ansys.aedt.core import Maxwell3d
from ansys.aedt.core.generic.constants import Axis
from ansys.aedt.core.generic.general_methods import active_sessions

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")

CURRENT_AMPS = 5
WIRE_RADIUS = 2.0    # mm
WIRE_LENGTH = 50.0   # mm
LINE_START = [3, 0, 0]
LINE_END = [20, 0, 0]

PROJECT = "Wire_B_Field_Studies"
VERSION = "2025.2"


# ----------------------------------------------------------------------
# Student-version gRPC workaround -- see docs/TROUBLESHOOTING.md #1
# ----------------------------------------------------------------------
def _is_grpc_session_active(port, machine=None):
    return port in active_sessions(student_version=True).values()


_desktop.is_grpc_session_active = _is_grpc_session_active


def open_design(design, non_graphical=True):
    """One design per study case."""
    return Maxwell3d(
        project=PROJECT,
        design=design,
        version=VERSION,
        solution_type="Magnetostatic",
        non_graphical=non_graphical,
        student_version=True,
    )


def build_model(m3d, pad_xy=500):
    """
    Copper wire + vacuum region + the two external current terminals.

    pad_xy is the "Percentage Offset" padding applied on +/-X and +/-Y. The
    +/-Z padding is always 0: the wire end faces have to sit on the problem
    boundary or the current terminals are not legal external terminals.
    """
    m3d.modeler.model_units = "mm"

    for name in ("Copper_Wire", "Region"):
        if name in m3d.modeler.object_names:
            m3d.modeler.delete(name)

    wire = m3d.modeler.create_cylinder(
        orientation=Axis.Z,
        origin=[0, 0, -WIRE_LENGTH / 2],
        radius=WIRE_RADIUS,
        height=WIRE_LENGTH,
        name="Copper_Wire",
        material="copper",
    )
    m3d.modeler.create_region(
        pad_value=[pad_xy, pad_xy, pad_xy, pad_xy, 0, 0],
        pad_type="Percentage Offset",
    )

    m3d.assign_current(
        assignment=[wire.top_face_z.id], amplitude=CURRENT_AMPS,
        solid=True, name="I_in",
    )
    m3d.assign_current(
        assignment=[wire.bottom_face_z.id], amplitude=CURRENT_AMPS,
        solid=True, swap_direction=True, name="I_out",
    )

    if "Extraction_Line" not in m3d.modeler.line_names:
        m3d.modeler.create_polyline(
            points=[LINE_START, LINE_END], name="Extraction_Line",
        )
    return wire


def make_setup(m3d, passes, percent_error=0.005, name="Setup1"):
    """
    Force exactly `passes` adaptive passes.

    MinimumPasses pins the floor and the tight PercentError stops AEDT
    declaring convergence early, so each case really does get the mesh its
    pass count implies -- otherwise a 5-pass and an 8-pass run can hand back
    the identical mesh and the study says nothing.
    """
    setup = (m3d.get_setup(name) if name in m3d.setup_names
             else m3d.create_setup(name=name))
    for key, value in (
        ("MaximumPasses", passes),
        ("MinimumPasses", passes),
        ("MinimumConvergedPasses", passes),
        ("PercentError", percent_error),
    ):
        if key in setup.props:
            setup.props[key] = value
    setup.update()
    return setup


def solve(m3d, name="Setup1"):
    if not m3d.analyze_setup(name):
        for message in m3d.odesktop.GetMessages(PROJECT, m3d.design_name, 0):
            print("   ", message)
        raise RuntimeError(f"{m3d.design_name}: {name} failed to solve")


def export_b_line(m3d, csv_path, name="Setup1"):
    """|B| along Extraction_Line -> CSV, same format as the main script."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    report = m3d.post.create_report(
        expressions="Mag_B",
        primary_sweep_variable="Distance",
        setup_sweep_name=f"{name} : LastAdaptive",
        context="Extraction_Line",
        report_category="Fields",
    )
    report.get_solution_data().export_data_to_csv(csv_path)
    return csv_path


def mesh_element_count(m3d, name="Setup1"):
    """
    Total tetrahedra in the final adaptive mesh, or None if AEDT will not say.

    Nice to have, not load-bearing: the plots fall back to the pass count.
    """
    try:
        stats = m3d.export_mesh_stats(name)
        with open(stats, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except Exception as exc:                      # noqa: BLE001 - best effort
        print(f"    (no mesh stats: {exc})")
        return None
    matches = re.findall(r"(\d[\d,]*)\s*$", text, flags=re.MULTILINE)
    numbers = [int(m.replace(",", "")) for m in matches]
    return max(numbers) if numbers else None


def write_meta(csv_path, **fields):
    """Sidecar JSON beside each CSV, so the plots can label the real numbers."""
    with open(os.path.splitext(csv_path)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump(fields, fh, indent=2)
