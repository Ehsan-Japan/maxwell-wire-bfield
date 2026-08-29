"""
Study B -- how far away does the boundary have to be?

    python studies/study_padding.py         # needs AEDT
    python tools/plot_padding_study.py      # then the figure

Solves the same wire with the region wall at 22, 32, 42, 82 and 162 mm from
the axis, each in its own design, and exports |B| along Extraction_Line to
results/padding/wall_<mm>.csv.

Why this matters: a finite-element model cannot mesh infinity. The region is
where you cut the problem off, and its outer face carries a boundary condition
(the default is a natural/zero-flux one). Put that face close to the conductor
and you are no longer solving "a wire in free space" -- you are solving "a wire
in a box", and the field near the wall is wrong. Push the wall out and the
answer stops depending on where you put it. That last part is the test.

The +/-Z faces stay on the wire end faces in every case: the current terminals
must reach the boundary. This study only moves the walls sideways.

The tightest case here puts the wall at 22 mm, just 2 mm past the last sampled
point -- that is the "too close" end. Going tighter would push the extraction
line outside the region entirely, which returns nonsense rather than a bad
answer.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common

# Distance from the wire axis to the +/-X and +/-Y region walls, in mm.
# 22 mm is the tightest usable value: Extraction_Line runs out to r = 20 mm and
# a sample point outside the region is not a field value at all.
WALLS = (22, 32, 42, 82, 162)
PASSES = 5
OUT = os.path.join(common.RESULTS, "padding")


def main():
    for wall in WALLS:
        print(f"[region] wall at {wall} mm from the axis")
        m3d = common.open_design(f"wall_{wall:04d}")
        try:
            common.build_model(m3d, wall_mm=float(wall))
            common.make_setup(m3d, passes=PASSES)
            common.solve(m3d)

            csv_path = os.path.join(OUT, f"wall_{wall:04d}.csv")
            common.export_b_line(m3d, csv_path)
            common.write_meta(csv_path, wall_mm=wall, passes=PASSES)
            print(f"    -> {os.path.relpath(csv_path, common.REPO)}")
        finally:
            m3d.save_project()

    print("done -- now run: python tools/plot_padding_study.py")


if __name__ == "__main__":
    main()
