"""
Figure 6 -- effect of the region padding (where you cut off free space).

    python studies/study_padding.py       # produces results/padding/*.csv
    python tools/plot_padding_study.py    # -> docs/images/padding_study{,-dark}.png

Left  : |B|(r) for each region size, against the analytic curve. A tight region
        distorts the field worst at large r -- exactly where the sampled points
        get close to the wall.
Right : the error at r = 20 mm versus how far away the wall is. Once the curve
        flattens, the boundary has stopped participating in the answer and the
        region is big enough.
"""
import matplotlib.pyplot as plt
import numpy as np

from vizstyle import (
    MODES, THEMES, R_START_MM, R_END_MM,
    at_radius, b_reference, caption, legend, linear_ticks, load_sweep,
    missing, save, style, title,
)

STUDY = load_sweep("padding", "wall_")


def wall(case):
    """Distance from the wire axis to the region wall, in mm."""
    return float(case["meta"].get("wall_mm", case["value"]))


def figure(mode):
    t = THEMES[mode]
    ramp = t["ramp"]
    c_theory = t["series"][1]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))

    # ---------------- left: the curves ----------------
    r_ref = np.linspace(R_START_MM, R_END_MM, 200)

    for i, case in enumerate(STUDY):
        color = ramp[min(i, len(ramp) - 1)]
        ax.plot(case["r"], case["b"], lw=2, color=color, zorder=2 + i,
                label=f"wall at {wall(case):.0f} mm")

    # Drawn last: once the sweep converges the curves land on top of it,
    # and a reference line hidden under the data is not a reference line.
    ax.plot(r_ref, b_reference(r_ref), lw=2, color=c_theory,
            ls=(0, (5, 3)), label="analytic: infinite wire", zorder=20)

    ax.set_yscale("log")
    ax.set_yticks([30, 50, 100, 200, 300])
    linear_ticks(ax)
    ax.set_xlabel("r  [mm]")
    ax.set_ylabel("|B|  [µT]")
    title(ax, "A tight region is a wall the field can feel", t)
    legend(ax, t, loc="upper right")

    # ---------------- right: convergence in region size ----------------
    analytic = float(b_reference(R_END_MM))
    x = [wall(case) for case in STUDY]
    y = [100 * (at_radius(case["r"], case["b"], R_END_MM) - analytic) / analytic
         for case in STUDY]

    ax2.axhline(0, color=t["grid"], lw=1)
    ax2.plot(x, y, lw=2, color=ramp[3], marker="o", ms=8,
             markeredgecolor=t["surface"], markeredgewidth=2)
    for case, xi, yi in zip(STUDY, x, y):
        ax2.annotate(
            f"{wall(case):.0f} mm", xy=(xi, yi), xytext=(0, 12),
            textcoords="offset points", ha="center", fontsize=9,
            color=t["secondary"],
        )
    ax2.axvline(R_END_MM, color=t["muted"], lw=1, ls=(0, (4, 3)))
    ax2.annotate(
        "wall at the last\nsampled radius", xy=(R_END_MM, 0.04),
        xycoords=("data", "axes fraction"), xytext=(6, 0), va="bottom",
        textcoords="offset points", fontsize=9, color=t["muted"],
    )
    ax2.set_xscale("log")
    ax2.set_xlim(min(x) * 0.75, max(x) * 1.7)
    ax2.set_xlabel("distance from the axis to the region wall  [mm]  (log)")
    ax2.margins(y=0.28)   # headroom for the point labels
    ax2.set_ylabel("error at r = 20 mm  [%]")
    title(ax2, "Push the wall out until it stops mattering", t)

    style(fig, (ax, ax2), t)
    caption(
        fig,
        "results/padding/ — 5 adaptive passes in every case; only the region "
        "size changes. The ±Z faces stay on the wire ends throughout.",
        t, x=0.075,
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.17, wspace=0.24)
    save(fig, "padding_study", mode, t)


if __name__ == "__main__":
    if not STUDY:
        missing("padding study", "studies/study_padding.py")
    else:
        for m in MODES:
            figure(m)
