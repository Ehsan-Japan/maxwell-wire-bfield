"""
Figure 0 -- the whole model in one isometric view.

    python tools/plot_isometric.py  ->  docs/images/isometric{,-dark}.png

Everything the script builds, in 3D and to scale: the copper cylinder, the
vacuum region wireframe, the two current terminals sitting on the top and
bottom boundary faces, one representative B field line circling the current,
and the radial line |B| is sampled along.

The orthographic projection is deliberate -- with perspective the region box
stops reading as a box, and this figure exists to show proportions.
"""
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from vizstyle import (
    MODES, THEMES, WIRE_RADIUS_MM, R_START_MM, R_END_MM, save,
)

HALF_L = 25.0                                    # wire half-length, mm
X_HALF = WIRE_RADIUS_MM + 5.0 * 2 * WIRE_RADIUS_MM   # region half-width, mm
FIELD_R = 13.0                                   # radius of the drawn field line


def region_box(ax, t):
    """The vacuum region, as a wireframe. Solid faces would hide the wire."""
    x, z = X_HALF, HALF_L
    corners = np.array([
        [-x, -x, -z], [x, -x, -z], [x, x, -z], [-x, x, -z],
        [-x, -x, z], [x, -x, z], [x, x, z], [-x, x, z],
    ])
    edges = [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    for i, j in edges:
        ax.plot(*zip(corners[i], corners[j]), color=t["muted"], lw=0.9,
                alpha=0.65, zorder=1)

    # The +Z boundary face, faintly, so "the end face is ON the boundary" reads.
    top = [[(-x, -x, z), (x, -x, z), (x, x, z), (-x, x, z)]]
    face = Poly3DCollection(top, facecolor=t["grid"], alpha=0.28, lw=0)
    ax.add_collection3d(face)


def wire(ax, t, color):
    u = np.linspace(0, 2 * np.pi, 80)
    z = np.array([-HALF_L, HALF_L])
    uu, zz = np.meshgrid(u, z)
    ax.plot_surface(
        WIRE_RADIUS_MM * np.cos(uu), WIRE_RADIUS_MM * np.sin(uu), zz,
        color=color, alpha=0.85, linewidth=0, shade=False, zorder=3,
    )


def terminals(ax, t, color):
    """The two external current terminals -- filled disks on the end faces."""
    u = np.linspace(0, 2 * np.pi, 60)
    for z in (HALF_L, -HALF_L):
        disk = [list(zip(WIRE_RADIUS_MM * np.cos(u),
                         WIRE_RADIUS_MM * np.sin(u),
                         np.full_like(u, z)))]
        ax.add_collection3d(Poly3DCollection(disk, facecolor=color, lw=0))


def field_line(ax, t):
    """One B field line: a circle around the current, in the midplane."""
    phi = np.linspace(0, 2 * np.pi, 200)
    ax.plot(FIELD_R * np.cos(phi), FIELD_R * np.sin(phi),
            np.zeros_like(phi), color=t["muted"], lw=1.3, ls=(0, (5, 3)),
            zorder=2)
    # Direction arrow, counter-clockwise seen from +Z (right-hand rule).
    a = np.deg2rad(200)
    ax.quiver(FIELD_R * np.cos(a), FIELD_R * np.sin(a), 0,
              -np.sin(a), np.cos(a), 0, length=4.5, color=t["muted"], lw=1.3,
              arrow_length_ratio=0.55)


def figure(mode):
    t = THEMES[mode]
    c_wire, c_term, c_line = t["series"]

    fig = plt.figure(figsize=(7.6, 7.0))
    ax = fig.add_subplot(111, projection="3d", proj_type="ortho")
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    region_box(ax, t)
    field_line(ax, t)
    wire(ax, t, c_wire)
    terminals(ax, t, c_term)

    # Current direction, straight up the conductor.
    ax.quiver(0, 0, -HALF_L + 4, 0, 0, 1, length=2 * HALF_L - 8,
              color=c_term, lw=2.2, arrow_length_ratio=0.09, zorder=4)

    ax.plot([R_START_MM, R_END_MM], [0, 0], [0, 0], color=c_line, lw=2.5,
            zorder=5)
    ax.scatter([R_START_MM, R_END_MM], [0, 0], [0, 0], s=34, color=c_line,
               depthshade=False, zorder=5)

    labels = (
        (0, 0, HALF_L + 7, "I_in — on the +Z boundary face", c_term, "center"),
        (0, 0, -HALF_L - 9, "I_out — on the −Z boundary face", c_term, "center"),
        (-6, -8, 4, "Copper_Wire\n5 A, r = 2 mm, L = 50 mm", t["secondary"], "right"),
        (R_END_MM + 2, 0, 4, "Extraction_Line\nr = 3 → 20 mm", c_line, "left"),
        (0, -FIELD_R - 2, -7, "B field line", t["muted"], "center"),
        (-X_HALF, X_HALF, HALF_L + 4, "Region (vacuum), 44 × 44 × 50 mm",
         t["muted"], "left"),
    )
    for x, y, z, text, color, ha in labels:
        ax.text(x, y, z, text, color=color, fontsize=9, ha=ha, zorder=6)

    ax.set_xlim(-X_HALF, X_HALF)
    ax.set_ylim(-X_HALF, X_HALF)
    ax.set_zlim(-HALF_L, HALF_L)
    ax.set_box_aspect((2 * X_HALF, 2 * X_HALF, 2 * HALF_L))
    ax.view_init(elev=20, azim=-58)

    # A schematic, not a plot: no panes, no ticks, just an axis triad.
    ax.set_axis_off()
    origin = np.array([-X_HALF, -X_HALF, -HALF_L])
    for direction, name in (((1, 0, 0), "x"), ((0, 1, 0), "y"), ((0, 0, 1), "z")):
        d = np.array(direction, dtype=float)
        ax.quiver(*origin, *d, length=11, color=t["secondary"], lw=1.2,
                  arrow_length_ratio=0.25)
        tip = origin + d * 13.5
        ax.text(*tip, name, color=t["secondary"], fontsize=9, ha="center")

    ax.set_title(
        "The model, isometric — 5 A up a 50 mm copper wire in a vacuum region",
        color=t["primary"], fontsize=12, loc="left", pad=6,
    )
    fig.subplots_adjust(left=0.0, right=1.0, top=0.95, bottom=0.0)
    save(fig, "isometric", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
