"""
Capture the real AEDT model view as a PNG.

    python studies/capture_model_image.py      # needs AEDT

Builds the model in a scratch design and exports two isometric images to
docs/images/:

    aedt_model.png        AEDT's own viewport, exactly what you see on screen
    aedt_model_pv.png     a PyVista render of the exported geometry (optional)

The second one only appears if `pyvista` is installed; it is the fallback when
the viewport capture misbehaves headless, and it renders on a white background
that sits better in a README.

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
    """AEDT's own screen capture. Needs the desktop up (non_graphical=False)."""
    kwargs = dict(
        full_name=path,
        orientation="isometric",
        show_grid=False,
        show_ruler=False,
        show_axis=True,
    )
    try:
        m3d.post.export_model_picture(**kwargs)
    except TypeError:
        # Older/newer signatures differ on the optional flags; the name and the
        # orientation are the two that have been stable.
        m3d.post.export_model_picture(full_name=path, orientation="isometric")
    return path


def pyvista_png(m3d, path):
    """
    PyVista render of the same geometry. Optional -- skipped if not installed.

    PyAEDT exports the bodies to mesh files and renders them offscreen, so this
    works with no desktop window and gives a repeatable image.
    """
    try:
        import pyvista  # noqa: F401
    except ImportError:
        print("    (pyvista not installed -- skipping the offscreen render)")
        return None

    for key in ("output_file", "export_path"):
        try:
            m3d.plot(show=False, **{key: path})
            return path
        except TypeError:
            continue
    print("    (m3d.plot() signature not recognised -- skipping)")
    return None


def main():
    os.makedirs(IMAGES, exist_ok=True)
    # Graphical: the viewport capture is a screen grab, so there has to be a
    # viewport. The design is geometry only -- nothing is solved here.
    m3d = common.open_design("model_view", non_graphical=False)
    try:
        common.build_model(m3d, pad_xy=500)
        m3d.modeler.fit_all()

        shot = viewport_png(m3d, os.path.join(IMAGES, "aedt_model.png"))
        print(f"    -> {os.path.relpath(shot, common.REPO)}")

        render = pyvista_png(m3d, os.path.join(IMAGES, "aedt_model_pv.png"))
        if render:
            print(f"    -> {os.path.relpath(render, common.REPO)}")
    finally:
        m3d.save_project()

    print("done -- tell Claude and the README will pick the images up")


if __name__ == "__main__":
    main()
