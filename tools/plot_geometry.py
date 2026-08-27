"""
Figure 1 -- the model, from two directions.

    python tools/plot_geometry.py  ->  docs/images/geometry{,-dark}.png

Left  (XZ, side view): what the script builds, to scale. The wire end faces sit
      on the region boundary because magnetostatic current excitations are
      external terminals.
Right (XY, looking down +Z): where the physics is. Current out of the page,
      B circling it counter-clockwise, and the extraction line cutting straight
      across those circles so every sample is a pure |B_phi|.
"""
import matplotlib.pyplot as plt
import numpy as np

from vizstyle import (
    MODES, THEMES, WIRE_RADIUS_MM, R_START_MM, R_END_MM, save, style,
)

HALF_L = 25.0                                    # wire half-length, mm
# 500 % "Percentage Offset" padding is 500 % of the 4 mm bounding box.
X_HALF = WIRE_RADIUS_MM + 5.0 * 2 * WIRE_RADIUS_MM
PANEL = 37.0   # half-width of both panels, mm -- one shared scale


def dimension(ax, p0, p1, label, t, offset=(0, 0), ha="center", va="center"):
    """A double-headed dimension line with its label."""
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(
        arrowstyle="<|-|>", color=t["muted"], lw=1,
        shrinkA=0, shrinkB=0, mutation_scale=10,
    ), zorder=6)
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    ax.annotate(label, xy=mid, xytext=offset, textcoords="offset points",
                ha=ha, va=va, fontsize=9, color=t["muted"], zorder=6)


def side_view(ax, t):
    """XZ cross-section, drawn to scale."""
    c_wire, c_term, c_line = t["series"]

    ax.add_patch(plt.Rectangle(
        (-X_HALF, -HALF_L), 2 * X_HALF, 2 * HALF_L,
        facecolor=t["grid"], alpha=0.35, edgecolor=t["muted"], lw=1.2, zorder=1,
    ))
    ax.add_patch(plt.Rectangle(
        (-WIRE_RADIUS_MM, -HALF_L), 2 * WIRE_RADIUS_MM, 2 * HALF_L,
        facecolor=c_wire, alpha=0.30, edgecolor=c_wire, lw=1.8, zorder=3,
    ))

    # The two external current terminals, ON the top and bottom boundary faces.
    for z, name, va, dy in ((HALF_L, "I_in", "bottom", 8),
                            (-HALF_L, "I_out", "top", -8)):
        ax.plot([-WIRE_RADIUS_MM, WIRE_RADIUS_MM], [z, z], color=c_term, lw=5,
                solid_capstyle="butt", zorder=5)
        ax.annotate(name, xy=(0, z), xytext=(0, dy), textcoords="offset points",
                    ha="center", va=va, fontsize=9, color=c_term, zorder=5)
    ax.annotate("", xy=(0, HALF_L - 8), xytext=(0, -HALF_L + 8),
                arrowprops=dict(arrowstyle="-|>", color=c_term, lw=2), zorder=5)
    ax.annotate("5 A", xy=(0, 6), xytext=(-6, 0), textcoords="offset points",
                ha="right", fontsize=9, color=c_term, zorder=5)

    # B is azimuthal, so in this plane it points straight through the page:
    # into it on +x, out of it on -x. Right-hand rule, current up.
    for x, glyph, text in ((15, "⊗", "B into page"),
                           (-15, "⊙", "B out of page")):
        ax.annotate(glyph, xy=(x, -10), ha="center", va="center", fontsize=17,
                    color=t["secondary"], zorder=5)
        ax.annotate(text, xy=(x, -10), xytext=(0, -14),
                    textcoords="offset points", ha="center", va="top",
                    fontsize=8, color=t["muted"], zorder=5)

    ax.plot([R_START_MM, R_END_MM], [0, 0], color=c_line, lw=2.5, zorder=6)
    ax.plot([R_START_MM, R_END_MM], [0, 0], "o", ms=6, color=c_line, zorder=6,
            markeredgecolor=t["surface"], markeredgewidth=1.5)
    ax.annotate("Extraction_Line", xy=(11.5, 0), xytext=(0, 8),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=9, color=c_line, zorder=6)

    dimension(ax, (-7, -HALF_L), (-7, HALF_L), "L = 50 mm", t,
              offset=(-5, 0), ha="right")
    dimension(ax, (-X_HALF, HALF_L + 7), (X_HALF, HALF_L + 7),
              "region: 44 mm wide (500 % padding)", t, offset=(0, 5),
              va="bottom")

    callout = dict(fontsize=9, zorder=6, textcoords="offset points",
                   arrowprops=dict(arrowstyle="-", color=t["muted"], lw=0.9))
    ax.annotate("Copper_Wire\nr = 2 mm", xy=(WIRE_RADIUS_MM, 14),
                xytext=(22, 6), ha="left", va="center",
                color=t["secondary"], **callout)
    ax.annotate("±Z padding = 0 —\nthe end faces ARE\nthe boundary",
                xy=(WIRE_RADIUS_MM, -HALF_L), xytext=(22, -4), ha="left",
                va="top", color=t["secondary"], **callout)

    # Both panels share one scale, so the region reads as the same box in each.
    ax.set_xlim(-PANEL, PANEL)
    ax.set_ylim(-PANEL, PANEL)
    ax.set_aspect("equal")
    ax.set_title("XZ — side view, to scale", color=t["primary"], fontsize=12,
                 loc="left", pad=8)


def top_view(ax, t):
    """XY cross-section at z = 0, where the field structure is visible."""
    c_wire, c_term, c_line = t["series"]

    ax.add_patch(plt.Rectangle(
        (-X_HALF, -X_HALF), 2 * X_HALF, 2 * X_HALF,
        facecolor=t["grid"], alpha=0.35, edgecolor=t["muted"], lw=1.2, zorder=1,
    ))

    # B field lines: concentric circles, counter-clockwise for current out of
    # the page. Arrowheads sit at 45 deg so they never collide with the labels.
    theta = np.linspace(0, 2 * np.pi, 200)
    for radius in (6, 11, 16, 21):
        ax.plot(radius * np.cos(theta), radius * np.sin(theta), lw=1.2,
                color=t["muted"], alpha=0.75, zorder=2)
        a = np.deg2rad(115)
        ax.annotate("", xy=(radius * np.cos(a + 0.09), radius * np.sin(a + 0.09)),
                    xytext=(radius * np.cos(a), radius * np.sin(a)),
                    arrowprops=dict(arrowstyle="-|>", color=t["muted"], lw=1.2),
                    zorder=2)
    ax.annotate("B field lines (right-hand rule)", xy=(-X_HALF, X_HALF + 2),
                ha="left", va="bottom", fontsize=9, color=t["muted"], zorder=4)

    ax.add_patch(plt.Circle((0, 0), WIRE_RADIUS_MM, facecolor=c_wire,
                            alpha=0.30, edgecolor=c_wire, lw=1.8, zorder=3))
    ax.annotate("⊙", xy=(0, 0), ha="center", va="center", fontsize=17,
                color=c_term, zorder=4)
    # Captions go below the drawing -- inside it they would sit on field lines.
    ax.annotate("⊙  5 A out of the page", xy=(-X_HALF, -X_HALF - 3),
                ha="left", va="top", fontsize=9, color=c_term, zorder=4)

    ax.plot([R_START_MM, R_END_MM], [0, 0], color=c_line, lw=2.5, zorder=5)
    ax.plot([R_START_MM, R_END_MM], [0, 0], "o", ms=6, color=c_line, zorder=5,
            markeredgecolor=t["surface"], markeredgewidth=1.5)
    for r_mark, label, dx, ha in ((R_START_MM, "r = 3", 7, "left"),
                                  (R_END_MM, "r = 20 mm", 0, "center")):
        ax.annotate(label, xy=(r_mark, 0), xytext=(dx, 9),
                    textcoords="offset points", ha=ha, fontsize=9,
                    color=c_line, zorder=5)

    ax.annotate(
        "the extraction line crosses the field lines at 90°, so |B| is all B_φ",
        xy=(-X_HALF, -X_HALF - 8), ha="left", va="top", fontsize=9,
        color=t["secondary"], zorder=5,
    )

    ax.set_xlim(-PANEL, PANEL)
    ax.set_ylim(-PANEL, PANEL)
    ax.set_aspect("equal")
    ax.set_title("XY — looking down the wire (z = 0)", color=t["primary"],
                 fontsize=12, loc="left", pad=8)


def figure(mode):
    t = THEMES[mode]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.5, 5.6))
    side_view(ax, t)
    top_view(ax2, t)
    style(fig, (ax, ax2), t)
    for a in (ax, ax2):
        a.grid(False)
        a.set_xticks([])
        a.set_yticks([])
        for side in ("left", "bottom"):
            a.spines[side].set_visible(False)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.03, wspace=0.06)
    save(fig, "geometry", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
