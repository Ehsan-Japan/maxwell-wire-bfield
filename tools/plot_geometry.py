"""
Figure 1 -- the model.

    python tools/plot_geometry.py  ->  docs/images/geometry{,-dark}.png

XZ cross-section of what magnetic_field_wire.py builds: the copper cylinder,
the vacuum region, the two external current terminals, and the line along which
|B| is sampled. Drawn to scale from the same numbers the script uses.
"""
import matplotlib.pyplot as plt

from vizstyle import MODES, THEMES, WIRE_RADIUS_MM, R_START_MM, R_END_MM, save, style

HALF_L = 25.0                      # wire half-length, mm
# 500 % "Percentage Offset" padding on X is 500 % of the 4 mm bounding box.
X_HALF = WIRE_RADIUS_MM + 5.0 * 2 * WIRE_RADIUS_MM


def figure(mode):
    t = THEMES[mode]
    c_wire, c_term, c_line = t["series"]

    fig, ax = plt.subplots(figsize=(6.2, 6.6))

    # Vacuum region. Note the top and bottom edges touch the wire end faces:
    # the +/-Z padding is 0.
    ax.add_patch(plt.Rectangle(
        (-X_HALF, -HALF_L), 2 * X_HALF, 2 * HALF_L,
        facecolor="none", edgecolor=t["grid"], lw=1.5, zorder=1,
    ))
    ax.annotate(
        "Region (vacuum)\npad = [500, 500, 500, 500, 0, 0] %",
        xy=(-X_HALF + 1.5, HALF_L - 1.5), fontsize=9, color=t["secondary"],
        va="top", zorder=3,
    )

    ax.add_patch(plt.Rectangle(
        (-WIRE_RADIUS_MM, -HALF_L), 2 * WIRE_RADIUS_MM, 2 * HALF_L,
        facecolor=c_wire, alpha=0.25, edgecolor=c_wire, lw=2, zorder=2,
    ))
    ax.annotate(
        "Copper_Wire\nr = 2 mm, L = 50 mm", xy=(3.5, -12), fontsize=9,
        color=t["secondary"], va="center", zorder=3,
    )

    # Both external current terminals sit ON the region boundary -- that is the
    # whole reason the Z padding is 0.
    for z, name, va in ((HALF_L, "I_in  (5 A)", "bottom"),
                        (-HALF_L, "I_out  (5 A)", "top")):
        ax.plot([-WIRE_RADIUS_MM, WIRE_RADIUS_MM], [z, z], color=c_term, lw=5,
                solid_capstyle="butt", zorder=4)
        ax.annotate(
            name, xy=(0, z), xytext=(0, 7 if va == "bottom" else -7),
            textcoords="offset points", ha="center", va=va,
            fontsize=9, color=c_term, zorder=4,
        )
    ax.annotate(
        "", xy=(0, HALF_L - 7), xytext=(0, -HALF_L + 7),
        arrowprops=dict(arrowstyle="-|>", color=c_term, lw=2), zorder=4,
    )

    ax.plot([R_START_MM, R_END_MM], [0, 0], color=c_line, lw=2.5, zorder=5)
    ax.plot([R_START_MM, R_END_MM], [0, 0], "o", ms=7, color=c_line, zorder=5)
    ax.annotate(
        "Extraction_Line\nr = 3 → 20 mm", xy=(11.5, 0), xytext=(0, 9),
        textcoords="offset points", ha="center", va="bottom", fontsize=9,
        color=c_line, zorder=5,
    )

    ax.set_xlim(-X_HALF - 3, X_HALF + 3)
    ax.set_ylim(-HALF_L - 9, HALF_L + 9)
    ax.set_aspect("equal")
    ax.set_xlabel("x  [mm]")
    ax.set_ylabel("z  [mm]")
    ax.set_title(
        "XZ cross-section — the wire end faces sit\n"
        "exactly on the region boundary",
        color=t["primary"], fontsize=12, loc="left", pad=10,
    )
    style(fig, (ax,), t)
    ax.grid(False)
    fig.tight_layout()
    save(fig, "geometry", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
