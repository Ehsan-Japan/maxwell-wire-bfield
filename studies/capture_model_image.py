"""
Capture the real AEDT model view as a PNG.

    python studies/capture_model_image.py      # needs AEDT

Builds the model in a scratch design (nothing is solved) and exports:

    aedt_model.png             AEDT's own viewport -- what you see on screen
    aedt_render{,-dark}.png    PyVista render of the same geometry, light/dark

The viewport capture needs the desktop visible, so this runs graphical. The
PyVista render goes through ModelPlotter and is the one that matches the
README's theme switching.

This does NOT replace docs/images/isometric.png. That one is a schematic: it
carries dimension callouts, terminal labels, the field line and the extraction
line, none of which AEDT draws for you. The screenshot proves the model is real;
the schematic explains it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common

IMAGES = os.path.join(common.REPO, "docs", "images")


def viewport_png(m3d, path):
    """AEDT's own screen capture -- signature verified against PyAEDT 1.4.0."""
    m3d.post.export_model_picture(
        full_name=path,
        orientation="isometric",
        show_axis=True,
        show_grid=False,
        show_ruler=False,
        width=1600,
        height=1200,
    )
    return path


def render_png(m3d, path, dark):
    """
    PyVista render of the same bodies.

    plot_air_objects=True keeps the vacuum region in the picture -- without it
    you get a bare cylinder and lose the whole point, which is that the wire
    spans the region from face to face. force_opacity_value makes the region
    translucent so the wire stays visible inside it.
    """
    m3d.plot(
        show=False,
        output_file=path,
        view="isometric",
        plot_air_objects=True,
        force_opacity_value=0.25,
        show_legend=False,
        dark_mode=dark,
    )
    return path


def main():
    os.makedirs(IMAGES, exist_ok=True)
    m3d = common.open_design("model_view", non_graphical=False)
    try:
        common.build_model(m3d, pad_xy=500)
        m3d.modeler.fit_all()

        jobs = [("viewport", lambda: viewport_png(
            m3d, os.path.join(IMAGES, "aedt_model.png")))]
        # The PyVista render draws the region as a translucent solid, which
        # hides the wire ends -- the whole point of the picture. Opt in with
        # --render if the viewport capture is unavailable.
        if "--render" in sys.argv:
            jobs += [
                ("render (light)", lambda: render_png(
                    m3d, os.path.join(IMAGES, "aedt_render.png"), dark=False)),
                ("render (dark)", lambda: render_png(
                    m3d, os.path.join(IMAGES, "aedt_render-dark.png"), dark=True)),
            ]
        for label, fn in jobs:
            try:
                out = fn()
                print(f"    {label} -> {os.path.relpath(out, common.REPO)}")
            except Exception as exc:                  # noqa: BLE001
                print(f"    {label} FAILED: {type(exc).__name__}: {exc}")
        m3d.save_project()
    finally:
        m3d.release_desktop(close_projects=False, close_desktop=False)


if __name__ == "__main__":
    main()
