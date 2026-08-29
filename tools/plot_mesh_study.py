"""
Figure 5 -- effect of mesh refinement.

    python studies/study_mesh.py        # produces results/mesh/*.csv in AEDT
    python tools/plot_mesh_study.py     # -> docs/images/mesh_study{,-dark}.png

Left  : |B|(r) for each adaptive-pass count, against the analytic curve.
Right : the error at r = 20 mm as the mesh refines. Convergence means this
        flattens out -- the remaining offset is the model, not the mesh.
"""
import matplotlib.pyplot as plt
import numpy as np

from vizstyle import (
    MODES, THEMES, R_START_MM, R_END_MM,
    at_radius, b_reference, caption, legend, linear_ticks, load_sweep,
    missing, save, style, title,
)

STUDY = load_sweep("mesh", "passes_")


def figure(mode):
    t = THEMES[mode]
    ramp = t["ramp"]
    c_theory = t["series"][1]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))

    # ---------------- left: the curves ----------------
    r_ref = np.linspace(R_START_MM, R_END_MM, 200)

    for i, case in enumerate(STUDY):
        color = ramp[min(i, len(ramp) - 1)]
        ax.plot(case["r"], case["b"], lw=2, color=color,
                label=f"{int(case['value'])} pass"
                      f"{'es' if case['value'] != 1 else ''}", zorder=2 + i)

    # Drawn last: once the sweep converges the curves land on top of it,
    # and a reference line hidden under the data is not a reference line.
    ax.plot(r_ref, b_reference(r_ref), lw=2, color=c_theory,
            ls=(0, (5, 3)), label="analytic: infinite wire", zorder=20)

    ax.set_yscale("log")
    ax.set_yticks([30, 50, 100, 200, 300])
    linear_ticks(ax)
    ax.set_xlabel("r  [mm]")
    ax.set_ylabel("|B|  [µT]")
    title(ax, "Coarse meshes under-resolve the far field", t)
    legend(ax, t, loc="upper right")

    # ---------------- right: convergence ----------------
    x, y, labels = [], [], []
    for case in STUDY:
        elements = case["meta"].get("elements")
        x.append(elements if elements else case["value"])
        analytic = float(b_reference(R_END_MM))
        y.append(100 * (at_radius(case["r"], case["b"], R_END_MM) - analytic)
                 / analytic)
        labels.append(int(case["value"]))
    use_elements = all(case["meta"].get("elements") for case in STUDY)

    ax2.axhline(0, color=t["grid"], lw=1)
    ax2.plot(x, y, lw=2, color=ramp[3], marker="o", ms=8,
             markeredgecolor=t["surface"], markeredgewidth=2)
    for xi, yi, label in zip(x, y, labels):
        ax2.annotate(
            f"{label} pass{'es' if label != 1 else ''}", xy=(xi, yi),
            xytext=(0, 12), textcoords="offset points", ha="center",
            fontsize=9, color=t["secondary"],
        )
    if use_elements:
        ax2.set_xscale("log")
        ax2.set_xlim(min(x) * 0.7, max(x) * 1.8)
        ax2.set_xlabel("tetrahedra in the final mesh  (log)")
    else:
        ax2.set_xlabel("adaptive passes")
    ax2.margins(y=0.28)   # headroom for the point labels
    ax2.set_ylabel("error at r = 20 mm  [%]")
    title(ax2, "Refine until the answer stops moving", t)

    style(fig, (ax, ax2), t)
    caption(
        fig,
        "results/mesh/ — same geometry and excitation in every case; only the "
        "discretisation changes.",
        t, x=0.075,
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.17, wspace=0.24)
    save(fig, "mesh_study", mode, t)


if __name__ == "__main__":
    if not STUDY:
        missing("mesh study", "studies/study_mesh.py")
    else:
        for m in MODES:
            figure(m)
