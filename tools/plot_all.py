"""
Regenerate every figure in docs/images/.

    python tools/plot_all.py

Figures that depend on a parameter study print a skip line until the matching
script in studies/ has been run in AEDT.
"""
import runpy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SCRIPTS = (
    "plot_isometric.py",
    "plot_geometry.py",
    "plot_theory.py",
    "plot_simulation.py",
    "plot_theory_vs_simulation.py",
    "plot_region_sizes.py",
    "plot_mesh_study.py",
    "plot_padding_study.py",
)

for script in SCRIPTS:
    runpy.run_path(os.path.join(HERE, script), run_name="__main__")
