"""
Magnetostatic B-field of a straight current-carrying wire (Ansys Maxwell 3D).
PyAEDT 1.4.x API (ansys.aedt.core namespace), Ansys Electronics Desktop Student 2025 R2.
"""
import os
import ansys.aedt.core.desktop as _desktop
from ansys.aedt.core import Maxwell3d
from ansys.aedt.core.generic.constants import Axis
from ansys.aedt.core.generic.general_methods import active_sessions
# ----------------------------------------------------------------------
# 0. Workaround for PyAEDT 1.4.0 + Student version.
#    is_grpc_session_active() calls active_sessions() without
#    student_version=True, so it only scans for ansysedt.exe and never
#    sees ansysedtsv.exe. The gRPC server does come up, PyAEDT just never
#    notices: it waits out desktop_launch_timeout and then raises
#    "Failed to start new AEDT gRPC session on port ...".
# ----------------------------------------------------------------------
def _is_grpc_session_active(port, machine=None):
    return port in active_sessions(student_version=True).values()

_desktop.is_grpc_session_active = _is_grpc_session_active

# ----------------------------------------------------------------------
# 1. Launch Maxwell 3D
#    version must match your installed Electronics Desktop Student build.
# ----------------------------------------------------------------------
m3d = Maxwell3d(
    project="Wire_B_Field",
    design="Wire_B_Field",
    version="2025.2",
    solution_type="Magnetostatic",
    non_graphical=False,
    student_version=True,
)

m3d.modeler.model_units = "mm"

# ----------------------------------------------------------------------
# 2. Parameters
# ----------------------------------------------------------------------
current_amps = 5
wire_radius = 2.0   # mm
wire_length = 50.0  # mm

# ----------------------------------------------------------------------
# 3. Geometry: copper wire along Z, centered at the origin
#    1.x renames: cs_axis -> orientation, position -> origin, matname -> material
# ----------------------------------------------------------------------
if "Copper_Wire" in m3d.modeler.object_names:
    m3d.modeler.delete("Copper_Wire")

wire = m3d.modeler.create_cylinder(
    orientation=Axis.Z,
    origin=[0, 0, -wire_length / 2],
    radius=wire_radius,
    height=wire_length,
    name="Copper_Wire",
    material="copper",
)

# Vacuum region, given as absolute face positions [+X, -X, +Y, -Y, +Z, -Z].
#
# NOT "Percentage Offset". A percentage- or offset-padded Region is parametric:
# it tracks the model bounding box and re-evaluates whenever the model changes.
# Extraction_Line below runs out to x = 20 mm, so with percentage padding the
# region silently grows from 44 x 44 x 50 mm to 242 x 44 x 50 mm, off-centre in
# X, the moment that line exists. "Absolute Position" pins the walls and the
# geometry stops depending on what else is in the design, or on whether this is
# the first run. Verified: with Absolute Position the region bounding box is
# unchanged after adding the polyline; with Percentage or Absolute Offset it is
# not.
#
# The +/-Z faces MUST sit on the wire end faces. Magnetostatic current
# terminals are external terminals: pad in Z and the wire floats inside the
# region, and the solver aborts with "Illegal external terminal 'I_5A': An
# external terminal must border the edge of the problem region".
if "Region" in m3d.modeler.object_names:
    m3d.modeler.delete("Region")
# 100 mm, i.e. 5x the outermost sampled radius. Measured, not guessed: with the
# wall at 22 mm the field at r = 20 mm comes out 21 % high because the boundary
# squeezes the flux; it is within 0.5 % by 42 mm. See studies/study_padding.py.
region_half = 100.0
m3d.modeler.create_region(
    pad_value=[
        region_half, -region_half,          # +X, -X
        region_half, -region_half,          # +Y, -Y
        wire_length / 2, -wire_length / 2,  # +Z, -Z: flush with the end faces
    ],
    pad_type="Absolute Position",
)

# The sampling line, created here rather than at post-processing time. Adding
# geometry after analyze_setup() leaves the solution stale and the field report
# comes back empty ("Solution Data failed to load"). It is safe to create it up
# front now only because the region above is pinned and no longer grows to
# swallow it.
if "Extraction_Line" not in m3d.modeler.line_names:
    m3d.modeler.create_polyline(
        points=[[3, 0, 0], [20, 0, 0]],
        name="Extraction_Line",
    )

# ----------------------------------------------------------------------
# 4. Excitation: 5 A along the solid conductor.
#    Magnetostatic needs TWO external current terminals per conduction path
#    (in and out), otherwise the solver aborts with "Verify conduction path
#    'Path1': ... at least two external current excitations should be
#    specified." One face injects, the other returns (swap_direction=True).
# ----------------------------------------------------------------------
m3d.assign_current(
    assignment=[wire.top_face_z.id],
    amplitude=current_amps,
    solid=True,
    name="I_in",
)
m3d.assign_current(
    assignment=[wire.bottom_face_z.id],
    amplitude=current_amps,
    solid=True,
    swap_direction=True,
    name="I_out",
)
# ----------------------------------------------------------------------
# 5. Solve
# ----------------------------------------------------------------------
if "Setup1" in m3d.setup_names:
    setup = m3d.get_setup("Setup1")
else:
    setup = m3d.create_setup(name="Setup1")
setup.props["MaximumPasses"] = 5
setup.update()

if not m3d.analyze_setup("Setup1"):
    raise RuntimeError("Setup1 failed to solve. Check the AEDT message window.")

# ----------------------------------------------------------------------
# 6. Post-processing: B along a radial line from r = 3 mm to r = 20 mm
#
#    Compare against the INFINITE wire law:
#
#        B = mu0*I / (2*pi*r)      ->  333 uT at r = 3 mm, 50 uT at r = 20 mm
#
#    Not the finite-segment form. Both current terminals sit ON the region
#    boundary, so the current enters and leaves the problem domain rather than
#    stopping in free space: there are no segment ends for the field to fall
#    off around, and the model is an infinitely long wire. Measured at 5
#    adaptive passes with the wall at 100 mm, the solver lands within ~2 % of
#    the infinite law from r = 8 mm out.
#
#    The finite-segment form mu0*I*L/(2*pi*r*sqrt(L^2+4r^2)) describes an
#    isolated 50 mm current segment floating in free space. That is a different
#    problem, and it is 22 % low at r = 20 mm here.
# ----------------------------------------------------------------------
plot = m3d.post.create_report(
    expressions="Mag_B",
    primary_sweep_variable="Distance",
    setup_sweep_name="Setup1 : LastAdaptive",
    context="Extraction_Line",
    report_category="Fields",
)
# export_to_csv() is gone in 1.x. export_table_to_file() only dumps marker/
# legend tables, so pull the trace data itself instead.
csv_path = os.path.join(m3d.working_directory, "B_Field_Data.csv")
plot.get_solution_data().export_data_to_csv(csv_path)
print(f"Simulation complete. B-field data exported to: {csv_path}")
# m3d.release_desktop(close_projects=True, close_desktop=True)
