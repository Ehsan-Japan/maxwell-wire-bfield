"""
Regenerate the README figures from results/B_Field_Data.csv.

    python tools/plot_results.py

Writes light and dark variants of each figure to docs/images/. The README
serves them through <picture media="(prefers-color-scheme: dark)">, so both
must exist and stay in sync.

Depends only on numpy + matplotlib (see requirements-plot.txt) -- it does not
touch AEDT, so it runs anywhere the CSV does.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------------------------------------------
# Model constants -- must match magnetic_field_wire.py
# ----------------------------------------------------------------------
MU0 = 4e-7 * np.pi
CURRENT = 5.0        # A
WIRE_LENGTH = 50e-3  # m
WIRE_RADIUS = 2.0    # mm
R_START = 3.0        # mm, first point of Extraction_Line

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(REPO, "results", "B_Field_Data.csv")
OUT = os.path.join(REPO, "docs", "images")

# Categorical slots 1-3 of the reference palette, light / dark steps.
THEMES = {
    "light": dict(
        surface="#fcfcfb", primary="#0b0b0b", secondary="#52514e",
        muted="#8b8a85", grid="#e4e3df",
        series=("#2a78d6", "#eb6834", "#1baf7a"),
    ),
    "dark": dict(
        surface="#1a1a19", primary="#ffffff", secondary="#c3c2b7",
        muted="#8b8a85", grid="#333331",
        series=("#3987e5", "#d95926", "#199e70"),
    ),
}


def load():
    """r [mm], |B| [uT] from the semicolon-separated solver export."""
    d = np.genfromtxt(CSV, delimiter=";", names=True, encoding="utf-8")
    distance_mm = d[d.dtype.names[0]]
    b_tesla = d[d.dtype.names[1]]
    return R_START + distance_mm, b_tesla * 1e6


def analytic(r_mm):
    """Finite-segment (midplane) and infinite-wire |B| in uT."""
    r = r_mm * 1e-3
    finite = MU0 * CURRENT * WIRE_LENGTH / (
        2 * np.pi * r * np.sqrt(WIRE_LENGTH**2 + 4 * r**2)
    )
    infinite = MU0 * CURRENT / (2 * np.pi * r)
    return finite * 1e6, infinite * 1e6


def style(fig, axes, t):
    fig.patch.set_facecolor(t["surface"])
    for ax in axes:
        ax.set_facecolor(t["surface"])
        ax.tick_params(colors=t["secondary"], labelsize=9, length=3, width=0.8)
        ax.xaxis.label.set_color(t["secondary"])
        ax.yaxis.label.set_color(t["secondary"])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(t["grid"])
            ax.spines[side].set_linewidth(0.8)
        ax.grid(True, color=t["grid"], linewidth=0.8, alpha=0.9)
        ax.set_axisbelow(True)


def figure_b_field(mode):
    t = THEMES[mode]
    c_solver, c_finite, c_inf = t["series"]
    r, b = load()
    finite, infinite = analytic(r)

    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(8, 6.2), sharex=True,
        gridspec_kw=dict(height_ratios=[3, 1], hspace=0.12),
    )

    ax.plot(r, infinite, lw=2, color=c_inf, label="Infinite-wire formula")
    ax.plot(r, finite, lw=2, color=c_finite, label="Analytic, finite segment")
    ax.plot(r, b, lw=2, color=c_solver, label="Maxwell 3D solver")

    # Direct labels at the right end, where the three curves are furthest apart.
    # dy nudges the two closest values (39 vs 36 uT) apart.
    for y, text, dy in (
        (infinite[-1], "infinite", 0),
        (finite[-1], "finite", 4),
        (b[-1], "solver", -4),
    ):
        ax.annotate(
            f"{text}  {y:.0f}", xy=(r[-1], y), xytext=(7, dy),
            textcoords="offset points", va="center", fontsize=9,
            color=t["secondary"],
        )

    ax.set_yscale("log")
    ax.set_yticks([30, 50, 100, 200, 300])
    ax.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylim(28, 400)
    ax.set_ylabel("|B|  [\u00b5T]")
    ax.set_title(
        "|B| along the wire midplane, 5 A through a 50 mm copper wire",
        color=t["primary"], fontsize=12, loc="left", pad=10,
    )
    leg = ax.legend(
        frameon=False, fontsize=9, loc="upper right", handlelength=1.6,
    )
    for txt in leg.get_texts():
        txt.set_color(t["secondary"])

    err = 100 * (b - finite) / finite
    ax2.axhline(0, color=t["grid"], lw=1)
    ax2.plot(r, err, lw=2, color=t["muted"])
    ax2.set_ylabel("solver \u2212 analytic\n[%]", fontsize=9)
    ax2.set_xlabel("r  [mm]   (wire surface at r = 2 mm)")

    style(fig, (ax, ax2), t)
    ax.set_xlim(r[0] - 0.3, r[-1] + 3.4)
    ax2.set_xticks([5, 10, 15, 20])
    fig.text(
        0.11, 0.015,
        "results/B_Field_Data.csv \u2014 1001 points, Setup1 : LastAdaptive, 5 adaptive passes",
        fontsize=8, color=t["muted"],
    )
    fig.subplots_adjust(left=0.11, right=0.9, top=0.92, bottom=0.13)
    save(fig, "b_field_vs_radius", mode, t)


def figure_geometry(mode):
    """XZ cross-section: why the Z padding must be zero."""
    t = THEMES[mode]
    c_wire, c_term, c_line = t["series"]

    fig, ax = plt.subplots(figsize=(6.2, 6.6))
    half_l = 25.0   # wire half-length, mm
    # 500 % "Percentage Offset" padding on X is 500 % of the 4 mm bounding box.
    x_half = 2.0 + 20.0

    ax.add_patch(plt.Rectangle(
        (-x_half, -half_l), 2 * x_half, 2 * half_l,
        facecolor="none", edgecolor=t["grid"], lw=1.5, zorder=1,
    ))
    ax.annotate(
        "Region (vacuum)\npad = [500, 500, 500, 500, 0, 0] %",
        xy=(-x_half + 1.5, half_l - 1.5), fontsize=9, color=t["secondary"],
        va="top", zorder=3,
    )

    ax.add_patch(plt.Rectangle(
        (-2.0, -half_l), 4.0, 2 * half_l,
        facecolor=c_wire, alpha=0.25, edgecolor=c_wire, lw=2, zorder=2,
    ))
    ax.annotate(
        "Copper_Wire\nr = 2 mm, L = 50 mm", xy=(3.5, -12), fontsize=9,
        color=t["secondary"], va="center", zorder=3,
    )

    # Both external current terminals sit ON the region boundary -- that is the
    # whole reason the Z padding is 0.
    for z, name, va in ((half_l, "I_in  (5 A)", "bottom"),
                        (-half_l, "I_out  (5 A)", "top")):
        ax.plot([-2.0, 2.0], [z, z], color=c_term, lw=5,
                solid_capstyle="butt", zorder=4)
        ax.annotate(
            name, xy=(0, z), xytext=(0, 7 if va == "bottom" else -7),
            textcoords="offset points", ha="center", va=va,
            fontsize=9, color=c_term, zorder=4,
        )
    ax.annotate(
        "", xy=(0, half_l - 7), xytext=(0, -half_l + 7),
        arrowprops=dict(arrowstyle="-|>", color=c_term, lw=2), zorder=4,
    )

    ax.plot([3, 20], [0, 0], color=c_line, lw=2.5, zorder=5)
    ax.plot([3, 20], [0, 0], "o", ms=7, color=c_line, zorder=5)
    ax.annotate(
        "Extraction_Line\nr = 3 → 20 mm", xy=(11.5, 0), xytext=(0, 9),
        textcoords="offset points", ha="center", va="bottom", fontsize=9,
        color=c_line, zorder=5,
    )

    ax.set_xlim(-x_half - 3, x_half + 3)
    ax.set_ylim(-half_l - 9, half_l + 9)
    ax.set_aspect("equal")
    ax.set_xlabel("x  [mm]")
    ax.set_ylabel("z  [mm]")
    ax.set_title(
        "XZ cross-section \u2014 the wire end faces sit\n"
        "exactly on the region boundary",
        color=t["primary"], fontsize=12, loc="left", pad=10,
    )
    style(fig, (ax,), t)
    ax.grid(False)
    fig.tight_layout()
    save(fig, "geometry", mode, t)


def save(fig, name, mode, t):
    suffix = "" if mode == "light" else "-dark"
    path = os.path.join(OUT, f"{name}{suffix}.png")
    fig.savefig(path, dpi=160, facecolor=t["surface"])
    plt.close(fig)
    print(f"wrote {os.path.relpath(path, REPO)}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for mode in ("light", "dark"):
        figure_b_field(mode)
        figure_geometry(mode)
