"""
Figure 3 -- the simulation result, on its own. No theory on this figure.

    python tools/plot_simulation.py  ->  docs/images/simulation{,-dark}.png

Left  : |B| along Extraction_Line straight out of the solver.
Right : the same data log-log, with a 1/r guide. A straight line of slope -1
        is the signature of the infinite-wire regime; the solver curve bends
        below it as r grows because the 50 mm wire stops looking infinite.
"""
import numpy as np

import matplotlib.pyplot as plt

from vizstyle import (
    MODES, THEMES, R_START_MM, R_END_MM,
    at_radius, caption, legend, linear_ticks, load_baseline, save, style, title,
)


def figure(mode):
    t = THEMES[mode]
    c_solver, c_guide, _ = t["series"]
    r, b = load_baseline()

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))

    # ---------------- left: the raw sweep ----------------
    ax.plot(r, b, lw=2, color=c_solver)
    for r_mark in (R_START_MM, R_END_MM):
        value = at_radius(r, b, r_mark)
        ax.plot([r_mark], [value], "o", ms=7, color=c_solver, zorder=5,
                markeredgecolor=t["surface"], markeredgewidth=2)
        ha, dx, dy = (("left", 10, 9) if r_mark == R_START_MM
                      else ("right", -10, 26))
        ax.annotate(
            f"{value:.0f} µT at r = {r_mark:.0f} mm", xy=(r_mark, value),
            xytext=(dx, dy), textcoords="offset points", fontsize=9,
            color=t["secondary"], ha=ha,
        )
    ax.set_xlabel("r  [mm]")
    ax.set_ylabel("|B|  [µT]")
    ax.set_xlim(R_START_MM - 0.5, R_END_MM + 0.5)
    ax.set_ylim(0, 380)
    title(ax, "Maxwell 3D: |B| along the wire midplane", t)

    # ---------------- right: log-log and the 1/r slope ----------------
    guide = b[0] * (r / r[0]) ** -1.0
    ax2.plot(r, guide, lw=2, color=c_guide, ls=(0, (5, 3)),
             label="1/r guide (slope −1)")
    ax2.plot(r, b, lw=2, color=c_solver, label="solver")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xticks([3, 5, 10, 20])
    ax2.set_yticks([30, 50, 100, 200, 300])
    linear_ticks(ax2)
    ax2.xaxis.set_major_formatter(plt.matplotlib.ticker.ScalarFormatter())
    ax2.xaxis.set_minor_formatter(plt.matplotlib.ticker.NullFormatter())

    # Local log-log slope, measured on the data itself.
    # Averaged over a window -- the point-to-point slope is mesh noise.
    slope = np.gradient(np.log(b), np.log(r))
    near, far = slope[:120].mean(), slope[-120:].mean()
    ax2.annotate(
        f"local slope  {near:+.2f}  near r = 3 mm\n"
        f"local slope  {far:+.2f}  near r = 20 mm",
        xy=(0.03, 0.06), xycoords="axes fraction", fontsize=9,
        color=t["secondary"],
    )
    ax2.set_xlabel("r  [mm]   (log)")
    ax2.set_ylabel("|B|  [µT]   (log)")
    title(ax2, "Same data, log-log", t)
    legend(ax2, t, loc="upper right")

    style(fig, (ax, ax2), t)
    caption(
        fig,
        "results/B_Field_Data.csv — 1001 points, Setup1 : LastAdaptive, "
        "5 adaptive passes, 5 A through a 50 mm copper wire.",
        t, x=0.075,
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.17, wspace=0.24)
    save(fig, "simulation", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
