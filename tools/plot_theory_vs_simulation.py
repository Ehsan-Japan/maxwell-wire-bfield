"""
Figure 4 -- theory against simulation.

    python tools/plot_theory_vs_simulation.py
        ->  docs/images/theory_vs_simulation{,-dark}.png

Top    : the solver overlaid on both analytic laws.
Bottom : solver minus the INFINITE-wire law, in percent. A validation figure is
         only as good as its residual.

Which law applies is decided by the boundary conditions, not by the length of
the cylinder you drew. Both current terminals sit on the region boundary, so
the current enters and leaves the problem domain: no segment ends, infinite
wire. The finite-segment curve is on the figure to show how different that
other problem is -- 22 % low at r = 20 mm -- not as the target.
"""
import matplotlib.pyplot as plt

from vizstyle import (
    MODES, THEMES, R_START_MM, R_END_MM,
    b_finite, b_reference, caption, legend, linear_ticks, load_baseline,
    save, style, title,
)


def figure(mode):
    t = THEMES[mode]
    c_solver, c_finite, c_ref = t["series"]
    r, b = load_baseline()
    reference = b_reference(r)
    finite = b_finite(r)

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(8, 6.2), sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1], hspace=0.12),
    )

    ax.plot(r, reference, lw=2, color=c_ref,
            label="theory: infinite wire  ← this model")
    ax.plot(r, finite, lw=2, color=c_finite, ls=(0, (5, 3)),
            label="theory: isolated 50 mm segment (different problem)")
    ax.plot(r, b, lw=2, color=c_solver, label="Maxwell 3D solver")

    for y, text, dy in ((reference[-1], "infinite", 5),
                        (finite[-1], "segment", -5),
                        (b[-1], "solver", 16)):
        ax.annotate(
            f"{text}  {y:.0f}", xy=(r[-1], y), xytext=(7, dy),
            textcoords="offset points", va="center", fontsize=9,
            color=t["secondary"],
        )

    ax.set_yscale("log")
    ax.set_yticks([30, 50, 100, 200, 300])
    linear_ticks(ax)
    ax.set_ylim(28, 450)
    ax.set_ylabel("|B|  [µT]")
    title(ax, "Theory vs simulation, 5 A through the wire", t)
    legend(ax, t, loc="upper right")

    err = 100 * (b - reference) / reference
    ax2.axhline(0, color=t["grid"], lw=1)
    ax2.plot(r, err, lw=2, color=t["muted"])
    ax2.set_ylabel("solver − infinite\n[%]", fontsize=9)
    ax2.set_xlabel("r  [mm]   (wire surface at r = 2 mm)")
    ax2.set_xticks([5, 10, 15, 20])

    style(fig, (ax, ax2), t)
    ax.set_xlim(R_START_MM - 0.3, R_END_MM + 3.4)
    far = abs(err[r >= 8]).max()
    caption(
        fig,
        f"Within {far:.0f} % of the infinite-wire law from r = 8 mm out; the "
        f"worst point anywhere is {abs(err).max():.0f} %. The wobble is mesh, not physics.",
        t,
    )
    fig.subplots_adjust(left=0.11, right=0.9, top=0.92, bottom=0.13)
    save(fig, "theory_vs_simulation", mode, t)


if __name__ == "__main__":
    for m in MODES:
        figure(m)
