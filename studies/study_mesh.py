"""
Study A -- how much does the mesh matter?

    python studies/study_mesh.py            # needs AEDT
    python tools/plot_mesh_study.py         # then the figure

Solves the same wire with 1, 2, 3, 5 and 8 adaptive passes, each in its own
design, and exports |B| along Extraction_Line for every case to
results/mesh/passes_<n>.csv.

The physics is fixed; only the discretisation changes. That makes this the
cleanest way to see the difference between "the solver is wrong" and "my mesh
is too coarse" -- the answer should walk monotonically toward the analytic
curve and then stop moving. When it stops moving, you are converged.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common

PASSES = (1, 2, 3, 5, 8)
OUT = os.path.join(common.RESULTS, "mesh")


def main():
    for passes in PASSES:
        print(f"[mesh] {passes} adaptive pass(es)")
        m3d = common.open_design(f"mesh_p{passes:02d}")
        try:
            common.build_model(m3d, pad_xy=500)
            common.make_setup(m3d, passes=passes)
            common.solve(m3d)

            csv_path = os.path.join(OUT, f"passes_{passes:02d}.csv")
            common.export_b_line(m3d, csv_path)
            elements = common.mesh_element_count(m3d)
            common.write_meta(csv_path, passes=passes, elements=elements,
                              pad_xy=500)
            where = os.path.relpath(csv_path, common.REPO)
            print(f"    -> {where}"
                  + (f"  ({elements} elements)" if elements else ""))
        finally:
            m3d.save_project()

    print("done -- now run: python tools/plot_mesh_study.py")


if __name__ == "__main__":
    main()
