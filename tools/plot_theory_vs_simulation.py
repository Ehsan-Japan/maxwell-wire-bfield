"""
Figure 4 -- theory against simulation.

    python tools/plot_theory_vs_simulation.py
        ->  docs/images/theory_vs_simulation{,-dark}.png

Top    : the solver overlaid on both analytic curves.
Bottom : solver minus finite-segment analytic, in percent. This is the panel
         that matters -- a validation figure is only as good as its residual.

The comparison must be against the *finite* segment formula. Checking a 50 mm
wire against mu0*I/(2*pi*r) and calling the gap a solver error is the classic
beginner mistake; see the right panel of docs/images/theory.png.
"""
import matplotlib.pyplot as plt

from vizstyle import (
    MODES, THEMES, R_START_MM, R_END_MM,
    b_finite, b_infinite, caption, legend, linear_ticks, load_baseline,
    save, style, title,
)


def figure(mode):
    t = THEMES[mode]
    c_solver, c_finite, c_inf = t["series"]
    r, b = load_baseline()
    finite = b_finite(r)
    infinite = b_infinite(r)

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(8, 6.2), sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1], hspace=0.12),
    )

    ax.plot(r, infinite, lw=2, color=c_inf, label="theory: infinite wire")
    ax.plot(r, finite, lw=2, color=c_finite, label="theory: 50 mm segment")
    ax.plot(r, b, lw=2, color=c_solver, label="Maxwell 3D solver")

    # Direct labels at the right end, where the three curves separate.
    # dy nudges the two closest values (39 vs 36 uT) apart.
    for y, text, dy in ((infinite[-1], "infinite", 0),
                        (finite[-1], "finite", 4),
                        (b[-1], "solver", -4)):
        ax.annotate(
            f"{text}  {y:.0f}", xy=(r[-1], y), xytext=(7, dy),
            textcoords="offset points", va="center", fontsize=9,
            color=t["secondary"],
        )

    ax.set_yscale("log")
    ax.set_yticks([30, 50, 100, 200, 300])
    linear_ticks(ax)
    ax.set_ylim(28, 400)
    ax.set_ylabel("|B|  [µT]")
    title(ax, "Theory vs simulation, 5 A through a 50 mm copper wire", t)
    legend(ax, t, loc="upper right")

    err = 100 * (b - finite) / finite
    ax2.axhline(0, color=t["grid"], lw=1)
    ax2.plot(r, err, lw=2, color=t["muted"])
    ax2.set_ylabel("solver − theory\n(finite)  [%]", fontsize=9)
    ax2.set_xlabel("r  [mm]   (wire surface at r = 2 mm)")
    ax2.set_xticks([5, 10, 15, 20])

    style(fig, (ax, ax2), t)
    ax.set_xlim(R_START_MM - 0.3, R_END_MM + 3.4)
    caption(
        fig,
        f"Agreement is within {abs(err).max():.0f} % everywhere; the drift at "
        "large r is mesh coarseness, not physics.",
        t,
    )
    fig.subplots_adjust(left=0.11, right=0.9, top=0.92, bottom=0.13)
    save(fig, "theory_vs_simulation", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
