"""
Figure 6a -- the five region sizes the padding study sweeps, drawn to scale.

    python tools/plot_region_sizes.py
        ->  docs/images/region_sizes{,-dark}.png

Needs no solver output: this is geometry, and it is worth seeing before the
error curve. "500 % padding" and "4000 % padding" are abstractions until you
notice the second one is a box roughly fifty times the volume of the first --
which is what you pay, in mesh, for the last percent of accuracy.

Only the side walls move. The +/-Z faces stay put in every case, because the
current terminals have to stay on them.
"""
import matplotlib.pyplot as plt

from vizstyle import (
    MODES, THEMES, WIRE_RADIUS_MM, R_START_MM, R_END_MM, save, style,
)

HALF_L = 25.0
# The paddings in studies/study_padding.py, and the wall they put in place.
CASES = [(pad, WIRE_RADIUS_MM + pad / 100.0 * 2 * WIRE_RADIUS_MM)
         for pad in (500, 750, 1000, 2000, 4000)]
BIGGEST = CASES[-1][1]


def footprint(ax, t):
    """XY footprint -- nested squares, to scale."""
    ramp = t["ramp"]
    c_line = t["series"][2]

    for (pad, half), color in zip(CASES, ramp[:len(CASES)]):
        ax.add_patch(plt.Rectangle(
            (-half, -half), 2 * half, 2 * half, facecolor="none",
            edgecolor=color, lw=1.6, zorder=2,
        ))
        # Labelled at the top-left corner: nested squares put those corners on
        # a diagonal, so five labels that would collide on one edge don't.
        ax.annotate(f"{pad} %", xy=(-half, half), xytext=(-3, 3),
                    textcoords="offset points", ha="right", va="bottom",
                    fontsize=9, color=color, zorder=3)

    ax.add_patch(plt.Circle((0, 0), WIRE_RADIUS_MM, facecolor=t["series"][0],
                            edgecolor=t["series"][0], lw=1, zorder=4))
    ax.plot([R_START_MM, R_END_MM], [0, 0], color=c_line, lw=2.5, zorder=4)
    ax.annotate("wire + extraction line (r = 3 → 20 mm)", xy=(R_END_MM, 0),
                xytext=(BIGGEST * 0.16, -BIGGEST * 0.20), textcoords="data",
                ha="left", va="center", fontsize=9, color=c_line, zorder=4,
                arrowprops=dict(arrowstyle="-", color=c_line, lw=0.8))

    ax.set_xlim(-BIGGEST * 1.08, BIGGEST * 1.08)
    ax.set_ylim(-BIGGEST * 1.08, BIGGEST * 1.15)
    ax.set_aspect("equal")
    ax.set_title("XY footprint, all five to scale", color=t["primary"],
                 fontsize=12, loc="left", pad=8)


def profile(ax, t):
    """XZ profile -- the same five, showing the height never changes."""
    ramp = t["ramp"]
    c_term = t["series"][1]

    # The boxes are 50 mm tall and up to 324 mm wide, so labels stacked above
    # them on leaders are the only ones that stay legible.
    for i, ((pad, half), color) in enumerate(zip(CASES, ramp[:len(CASES)])):
        ax.add_patch(plt.Rectangle(
            (-half, -HALF_L), 2 * half, 2 * HALF_L, facecolor="none",
            edgecolor=color, lw=1.6, zorder=2,
        ))
        ax.annotate(f"wall at {half:.0f} mm", xy=(half, HALF_L),
                    xytext=(half, HALF_L + 22 + i * 24), textcoords="data",
                    ha="center", va="bottom", fontsize=9, color=color, zorder=3,
                    arrowprops=dict(arrowstyle="-", color=color, lw=0.8))

    ax.add_patch(plt.Rectangle(
        (-WIRE_RADIUS_MM, -HALF_L), 2 * WIRE_RADIUS_MM, 2 * HALF_L,
        facecolor=t["series"][0], edgecolor=t["series"][0], lw=1, zorder=4,
    ))
    for z in (HALF_L, -HALF_L):
        ax.plot([-WIRE_RADIUS_MM * 3, WIRE_RADIUS_MM * 3], [z, z],
                color=c_term, lw=4, zorder=5)
    ax.annotate("±Z faces never move — the terminals live on them",
                xy=(0, -HALF_L), xytext=(0, -60), textcoords="data",
                ha="center", va="top", fontsize=9, color=t["secondary"],
                zorder=5,
                arrowprops=dict(arrowstyle="-", color=t["muted"], lw=0.9))

    ax.set_xlim(-BIGGEST * 1.08, BIGGEST * 1.08)
    ax.set_ylim(-BIGGEST * 1.08, BIGGEST * 1.15)
    ax.set_aspect("equal")
    ax.set_title("XZ profile, same scale", color=t["primary"], fontsize=12,
                 loc="left", pad=8)


def figure(mode):
    t = THEMES[mode]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.5, 5.4))
    footprint(ax, t)
    profile(ax2, t)
    style(fig, (ax, ax2), t)
    for a in (ax, ax2):
        a.grid(False)
        a.set_xticks([])
        a.set_yticks([])
        for side in ("left", "bottom"):
            a.spines[side].set_visible(False)

    volumes = [(2 * half) ** 2 * (2 * HALF_L) for _, half in CASES]
    fig.text(
        0.03, 0.03,
        f"The 4000 % region holds {volumes[-1] / volumes[0]:.0f}× the volume of "
        "the 500 % one — and every bit of it has to be meshed and solved.",
        fontsize=8, color=t["muted"],
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.08, wspace=0.06)
    save(fig, "region_sizes", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
