#!/usr/bin/env python3
"""Create the README image by rendering the real Python Masker window."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from download_sample import prepare_sample
from masker import Masker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("sample_data"))
    parser.add_argument(
        "--output", type=Path, default=Path("docs/images/masker-python.png")
    )
    args = parser.parse_args()

    image_path = args.data_dir / "prostate_mri.npy"
    mask_path = args.data_dir / "prostate_mask.npy"
    if not image_path.exists() or not mask_path.exists():
        image_path, mask_path = prepare_sample(args.data_dir)

    image = np.load(image_path, allow_pickle=False)
    mask = np.load(mask_path, allow_pickle=False)
    np.random.seed(4)  # Stable example colour; the live app remains random.
    viewer = Masker(image, mask, show_guide=False)
    viewer.slice_index = int(mask.sum(axis=(0, 1)).argmax())
    viewer.alpha = 0.6
    viewer.contrast = 1.15
    rows, columns = np.nonzero(mask[:, :, viewer.slice_index])
    centre = (float(columns.mean()), float(rows.mean()))
    viewer.brush_size = 14
    viewer._move_brush(centre[0] + 70, centre[1] - 28)
    viewer._redraw_image()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    viewer.figure.set_size_inches(6, 6)
    viewer.figure.savefig(
        args.output, dpi=160, bbox_inches="tight", pad_inches=0, facecolor="black"
    )
    plt.close(viewer.figure)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
