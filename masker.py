#!/usr/bin/env python3
"""A deliberately small Python port of MATLAB Masker."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np


MASK_COLOURS = ((0.1, 0.3, 0.7), (0.6, 0.5, 1.0), (0.3, 0.9, 0.2))
MASK_CUTOFF = 1e-4
BRUSH_MIN, BRUSH_MAX, BRUSH_STEP = 1, 100, 1


class Masker:
    """Interactive state and callbacks for the minimalist annotation window."""

    def __init__(self, image: np.ndarray, mask: Optional[np.ndarray] = None,
                 output: Optional[Union[str, Path]] = None,
                 show_guide: bool = True) -> None:
        image = np.asarray(image)
        if image.ndim not in (2, 3):
            raise ValueError("image must be a 2D or 3D array")

        self.was_2d = image.ndim == 2
        self.image = image[:, :, None] if self.was_2d else image
        expected_shape = image.shape
        if mask is None or np.asarray(mask).size == 0:
            binary_mask = np.zeros(expected_shape, dtype=bool)
        else:
            mask = np.asarray(mask)
            if mask.shape != expected_shape:
                raise ValueError("Incompatible sizes between image and mask.")
            binary_mask = mask >= MASK_CUTOFF
        self.mask = binary_mask[:, :, None] if self.was_2d else binary_mask

        # Follow MATLAB's min/max normalization, including NaNs for constants.
        image_float = self.image.astype(np.float32)
        with np.errstate(divide="ignore", invalid="ignore"):
            self.image = ((image_float - image_float.min()) /
                          (image_float.max() - image_float.min()))

        self.output = Path(output) if output is not None else None
        self.slice_index = 0
        self.alpha = 0.5
        self.contrast = 1.0
        self.brush_size = 3
        self.left_held = False
        self.right_held = False
        self.keys = {"a": False, "s": False, "c": False}
        self.current_point = (0.0, 0.0)
        self.mask_colour = np.asarray(MASK_COLOURS[np.random.randint(3)])
        self._saved = False

        self.figure, self.axes = plt.subplots(num="The little masker")
        self.figure.subplots_adjust(0, 0, 1, 1)
        self.axes.set_axis_off()
        self.axes.set_aspect("equal")
        self.image_artist = self.axes.imshow(self._display_slice(), origin="upper")
        (self.brush_artist,) = self.axes.plot([], [], ".", color=self.mask_colour,
                                              linewidth=1)
        self._move_brush(*self.current_point)
        self._connect_events()

        if show_guide:
            print("Mouse scroll: change slice\n"
                  "Left-click: labeling\n"
                  "Right-click: removing labeling\n"
                  '"s" + scroll: brush size\n'
                  '"c" + scroll: image intensity contrast\n'
                  '"a" + scroll: label transparency')

    def _connect_events(self) -> None:
        canvas = self.figure.canvas
        canvas.mpl_connect("scroll_event", self._on_scroll)
        canvas.mpl_connect("button_press_event", self._on_button_down)
        canvas.mpl_connect("button_release_event", self._on_button_up)
        canvas.mpl_connect("motion_notify_event", self._on_motion)
        canvas.mpl_connect("key_press_event", self._on_key_press)
        canvas.mpl_connect("key_release_event", self._on_key_release)
        canvas.mpl_connect("close_event", self._on_close)

    def _display_slice(self) -> np.ndarray:
        grey = self.image[:, :, self.slice_index] * self.contrast
        overlay = (self.mask[:, :, self.slice_index, None] *
                   self.alpha * self.mask_colour)
        return np.clip(grey[:, :, None] + overlay, 0.0, 1.0)

    def _redraw_image(self) -> None:
        self.image_artist.set_data(self._display_slice())
        self.figure.canvas.draw_idle()

    def _move_brush(self, x: float, y: float) -> None:
        angle = np.linspace(-np.pi, np.pi, 36)
        self.current_point = (x, y)
        self.brush_artist.set_data(np.cos(angle) * self.brush_size + x,
                                   np.sin(angle) * self.brush_size + y)

    def _apply_brush(self, x: float, y: float, add: bool) -> None:
        rows, columns = np.ogrid[:self.mask.shape[0], :self.mask.shape[1]]
        footprint = (columns - x) ** 2 + (rows - y) ** 2 <= self.brush_size ** 2
        current = self.mask[:, :, self.slice_index]
        if add:
            current |= footprint
        else:
            current &= ~footprint

    @staticmethod
    def _point(event) -> Optional[tuple[float, float]]:
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return None
        return float(event.xdata), float(event.ydata)

    def _on_scroll(self, event) -> None:
        step = float(event.step)  # positive up; opposite MATLAB's wheel count
        if self.keys["a"]:
            self.alpha = float(np.clip(self.alpha + step * 0.1, 0.0, 1.0))
            self._redraw_image()
        elif self.keys["s"]:
            self.brush_size = int(np.clip(self.brush_size + step * BRUSH_STEP,
                                          BRUSH_MIN, BRUSH_MAX))
            self._move_brush(*self.current_point)
            self.figure.canvas.draw_idle()
        elif self.keys["c"]:
            self.contrast = float(np.clip(self.contrast + step * 0.1, 0.0, 2.0))
            self._redraw_image()
        else:
            new_index = int(np.clip(self.slice_index - step, 0,
                                    self.image.shape[2] - 1))
            if new_index != self.slice_index:
                self.slice_index = new_index
                self._redraw_image()
                print(f"masker: Slice = {self.slice_index + 1}/{self.image.shape[2]}.")

    def _on_button_down(self, event) -> None:
        point = self._point(event)
        if point is None:
            return
        if event.button == 1:
            self.left_held, self.right_held, add = True, False, True
        elif event.button == 3:
            self.left_held, self.right_held, add = False, True, False
        else:
            return
        self._apply_brush(*point, add)
        self._move_brush(*point)
        self._redraw_image()

    def _on_button_up(self, _event) -> None:
        self.left_held = self.right_held = False

    def _on_motion(self, event) -> None:
        point = self._point(event)
        if point is None:
            return
        self._move_brush(*point)
        if self.left_held or self.right_held:
            self._apply_brush(*point, self.left_held)
            self._redraw_image()
        else:
            self.figure.canvas.draw_idle()

    def _on_key_press(self, event) -> None:
        self.keys = {key: False for key in self.keys}
        if event.key in self.keys:
            self.keys[event.key] = True

    def _on_key_release(self, event) -> None:
        if event.key in self.keys:
            self.keys[event.key] = False

    def _on_close(self, _event) -> None:
        if self.output is not None and not self._saved:
            destination = self.output
            if destination.exists():
                counter = 1
                while destination.with_name(
                        f"{destination.stem}-{counter}{destination.suffix}").exists():
                    counter += 1
                destination = destination.with_name(
                    f"{destination.stem}-{counter}{destination.suffix}")
            np.save(destination, self.result().astype(np.uint8))
            self._saved = True
            print(f"masker: Masks saved: {destination}.")

    def result(self) -> np.ndarray:
        """Return the current binary mask in the input image's dimensions."""
        return self.mask[:, :, 0].copy() if self.was_2d else self.mask.copy()

    def show(self) -> np.ndarray:
        """Block until the window closes, then return the edited mask."""
        plt.show(block=True)
        return self.result()


def masker(image: np.ndarray, mask: Optional[np.ndarray] = None,
           filename: Optional[Union[str, Path]] = None,
           show_guide: bool = True) -> np.ndarray:
    """Open Masker and return the edited binary mask after the window closes."""
    return Masker(image, mask, filename, show_guide).show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal 2D/3D mask editor")
    parser.add_argument("image", type=Path, help="2D or 3D image in .npy format")
    parser.add_argument("--mask", type=Path, help="optional existing .npy mask")
    parser.add_argument("--output", type=Path, help="save mask on close (.npy)")
    parser.add_argument("--no-guide", action="store_true", help="hide usage guide")
    args = parser.parse_args()
    image = np.load(args.image, allow_pickle=False)
    mask = np.load(args.mask, allow_pickle=False) if args.mask else None
    masker(image, mask, args.output, not args.no_guide)


if __name__ == "__main__":
    main()
