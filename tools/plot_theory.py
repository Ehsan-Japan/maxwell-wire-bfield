"""
Figure 2 -- the theory, on its own. No solver data involved.

    python tools/plot_theory.py  ->  docs/images/theory{,-dark}.png

Left  : |B|(r) from the axis outward. Inside the conductor Ampere's law encloses
        only (r/a)^2 of the current, so |B| grows linearly; outside it falls as
        1/r. The maximum is exactly at the conductor surface.
Right : how much the finite length costs you. B_finite / B_infinite =
        L / sqrt(L^2 + 4 r^2) -- the only reason the textbook formula fails here.
"""
import matplotlib.pyplot as plt
import numpy as np

from vizstyle import (
    MODES, THEMES, WIRE_RADIUS_MM, WIRE_LENGTH, R_START_MM, R_END_MM,
    b_finite, b_infinite, b_inside, finite_length_factor,
    caption, legend, save, style, title,
)


def figure(mode):
    t = THEMES[mode]
    c_in, c_finite, c_inf = t["series"]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))

    # ---------------- left: inside vs outside ----------------
    r_in = np.linspace(0, WIRE_RADIUS_MM, 200)
    r_out = np.linspace(WIRE_RADIUS_MM, R_END_MM, 400)

    ax.axvspan(0, WIRE_RADIUS_MM, color=c_in, alpha=0.10, lw=0)
    ax.plot(r_in, b_inside(r_in), lw=2, color=c_in,
            label="inside:  B = μ₀ I r / (2π a²)")
    ax.plot(r_out, b_infinite(r_out), lw=2, color=c_inf,
            label="outside, infinite:  B = μ₀ I / (2π r)")
    ax.plot(r_out, b_finite(r_out), lw=2, color=c_finite,
            label="outside, 50 mm segment")

    b_surface = b_inside(WIRE_RADIUS_MM)
    ax.plot([WIRE_RADIUS_MM], [b_surface], "o", ms=8, color=c_in, zorder=5,
            markeredgecolor=t["surface"], markeredgewidth=2)
    ax.annotate(
        f"surface, r = a = {WIRE_RADIUS_MM:.0f} mm\n{b_surface:.0f} µT — the maximum",
        xy=(WIRE_RADIUS_MM, b_surface), xytext=(14, 10),
        textcoords="offset points", fontsize=9, color=t["secondary"],
    )
    ax.annotate(
        "conductor", xy=(WIRE_RADIUS_MM / 2, 30), ha="center", fontsize=9,
        color=t["secondary"],
    )

    ax.set_xlim(0, R_END_MM)
    ax.set_ylim(0, 620)
    ax.set_xlabel("r  [mm]   (from the wire axis)")
    ax.set_ylabel("|B|  [µT]")
    title(ax, "|B| through the conductor and out into the vacuum", t)
    legend(ax, t, loc="center right")

    # ---------------- right: the finite-length penalty ----------------
    r = np.linspace(0.5, R_END_MM, 400)
    factor = 100 * finite_length_factor(r)
    ax2.plot(r, factor, lw=2, color=c_finite)
    ax2.axhline(100, color=t["grid"], lw=1)
    ax2.annotate(
        "infinite-wire limit", xy=(0.5, 100), xytext=(0, 6),
        textcoords="offset points", fontsize=9, color=t["muted"],
    )

    # The sampled window, and its two endpoints.
    ax2.axvspan(R_START_MM, R_END_MM, color=t["series"][0], alpha=0.08, lw=0)
    for r_mark, ha, dx in ((R_START_MM, "left", 9), (R_END_MM, "right", -9)):
        f = 100 * float(finite_length_factor(r_mark))
        ax2.plot([r_mark], [f], "o", ms=7, color=c_finite, zorder=5,
                 markeredgecolor=t["surface"], markeredgewidth=2)
        ax2.annotate(
            f"r = {r_mark:.0f} mm\n{f:.0f} %", xy=(r_mark, f),
            xytext=(dx, -6), textcoords="offset points", fontsize=9,
            color=t["secondary"], ha=ha, va="top",
        )
    ax2.annotate(
        "sampled window", xy=((R_START_MM + R_END_MM) / 2, 74), ha="center",
        fontsize=9, color=t["secondary"],
    )

    ax2.set_xlim(0, R_END_MM + 2)
    ax2.set_ylim(70, 106)
    ax2.set_xlabel("r  [mm]")
    ax2.set_ylabel("B_finite / B_infinite  [%]")
    title(ax2, "What the finite 50 mm length costs", t)

    style(fig, (ax, ax2), t)
    caption(
        fig,
        "Analytic only — no simulation on this figure.  "
        f"a = {WIRE_RADIUS_MM:.0f} mm, L = {WIRE_LENGTH * 1e3:.0f} mm, I = 5 A.",
        t, x=0.075,
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.17, wspace=0.28)
    save(fig, "theory", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
