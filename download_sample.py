#!/usr/bin/env python3
"""Download and prepare a small, real 3D prostate MRI for Masker."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import urllib.request
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


RECORD_URL = "https://doi.org/10.5281/zenodo.16396"
FILES = {
    "image": {
        "name": "Case10-MR.nrrd",
        "url": "https://zenodo.org/records/16396/files/Case10-MR.nrrd?download=1",
        "md5": "ee6186f1a803e9abf3406071baaab2e2",
    },
    "mask": {
        "name": "Case10-MR-label.nrrd",
        "url": "https://zenodo.org/records/16396/files/Case10-MR-label.nrrd?download=1",
        "md5": "a736ddcf07eb745d01154497e55d75a2",
    },
}


def checksum(path: Path) -> str:
    digest = hashlib.md5()  # Published dataset checksum; used for integrity only.
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path, expected_md5: str,
             force: bool = False) -> None:
    if destination.exists() and not force:
        if checksum(destination) == expected_md5:
            print(f"Using verified download: {destination}")
            return
        raise RuntimeError(
            f"{destination} exists but has the wrong checksum; use --force to replace it"
        )

    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "port-it-sample/1"})
    print(f"Downloading {destination.name} ...")
    try:
        with urllib.request.urlopen(request) as response, temporary.open("wb") as target:
            shutil.copyfileobj(response, target)
        actual_md5 = checksum(temporary)
        if actual_md5 != expected_md5:
            raise RuntimeError(
                f"Checksum mismatch for {destination.name}: {actual_md5}"
            )
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_nrrd(path: Path) -> Tuple[np.ndarray, Dict[str, str]]:
    """Read the scalar, embedded gzip/raw NRRD used by this sample."""
    content = path.read_bytes()
    separator = b"\r\n\r\n" if b"\r\n\r\n" in content else b"\n\n"
    header_bytes, payload = content.split(separator, 1)
    lines = header_bytes.decode("ascii").splitlines()
    if not lines or not lines[0].startswith("NRRD"):
        raise ValueError(f"Not an NRRD file: {path}")

    header = {}
    for line in lines[1:]:
        if line and not line.startswith("#") and ":" in line:
            key, value = line.split(":", 1)
            header[key.strip().lower()] = value.strip()

    type_map = {
        "short": np.dtype("i2"),
        "int16": np.dtype("i2"),
        "unsigned char": np.dtype("u1"),
        "uchar": np.dtype("u1"),
        "uint8": np.dtype("u1"),
    }
    if header.get("type") not in type_map:
        raise ValueError(f"Unsupported NRRD type: {header.get('type')}")
    if int(header.get("dimension", "0")) != 3:
        raise ValueError("This converter expects a 3D scalar NRRD")

    dtype = type_map[header["type"]]
    if dtype.itemsize > 1:
        byte_order = "<" if header.get("endian", "little") == "little" else ">"
        dtype = dtype.newbyteorder(byte_order)
    sizes = tuple(int(value) for value in header["sizes"].split())
    encoding = header.get("encoding", "raw").lower()
    if encoding in ("gzip", "gz"):
        payload = gzip.decompress(payload)
    elif encoding != "raw":
        raise ValueError(f"Unsupported NRRD encoding: {encoding}")

    expected_values = int(np.prod(sizes))
    volume = np.frombuffer(payload, dtype=dtype, count=expected_values)
    if volume.size != expected_values:
        raise ValueError(f"Incomplete voxel data in {path}")

    # NRRD's first axis is fastest. Convert (x, y, z) to NumPy image order
    # (row=y, column=x, slice=z), which is what masker.py displays.
    volume = volume.reshape(sizes, order="F").transpose(1, 0, 2)
    return volume.copy(), header


def prepare_sample(output_dir: Path, force: bool = False) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = {}
    for role, metadata in FILES.items():
        path = output_dir / metadata["name"]
        download(metadata["url"], path, metadata["md5"], force)
        downloaded[role] = path

    image, _ = read_nrrd(downloaded["image"])
    mask, _ = read_nrrd(downloaded["mask"])
    if image.shape != mask.shape:
        raise RuntimeError(f"Image/mask shape mismatch: {image.shape} != {mask.shape}")

    image_path = output_dir / "prostate_mri.npy"
    mask_path = output_dir / "prostate_mask.npy"
    np.save(image_path, image)
    np.save(mask_path, mask.astype(bool))
    # Raw column-major copies let the original MATLAB tool load the same arrays
    # without requiring an NRRD or NumPy-file reader.
    image.astype("<i2", copy=False).ravel(order="F").tofile(
        output_dir / "prostate_mri_int16.raw"
    )
    mask.astype("u1", copy=False).ravel(order="F").tofile(
        output_dir / "prostate_mask_uint8.raw"
    )
    (output_dir / "prostate_shape.txt").write_text(
        " ".join(str(value) for value in image.shape) + "\n", encoding="ascii"
    )
    print(f"Prepared {image_path} and {mask_path} with shape {image.shape}.")
    return image_path, mask_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download an anonymized 3D prostate MRI and label for Masker"
    )
    parser.add_argument("--output-dir", type=Path, default=Path("sample_data"))
    parser.add_argument("--force", action="store_true", help="replace downloads")
    args = parser.parse_args()
    image_path, mask_path = prepare_sample(args.output_dir, args.force)
    print("\nOpen the image with an empty mask:")
    print(f"  python masker.py {image_path} --output {args.output_dir / 'my_mask.npy'}")
    print("\nOr inspect/edit the supplied prostate label:")
    print(f"  python masker.py {image_path} --mask {mask_path}")
    print(f"\nDataset: {RECORD_URL}")
    print("Research demonstration only; not for clinical use.")


if __name__ == "__main__":
    main()
