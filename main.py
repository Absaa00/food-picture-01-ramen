"""Food picture entry for make.fun food-picture-01.

Copies the bundled ramen photograph to the output directory as
``entry.png``. The copy is byte-for-byte deterministic: the same input
always produces the same output, so two runs write identical bytes.
Only the Python standard library is used and no network is touched.
"""

import os
import shutil
import struct
import sys

SOURCE = os.path.realpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png"))
OUTPUT_NAME = "entry.png"

# Competition limits (food-picture-01): output must fit in 1 MiB and
# be at most 1024x1024 pixels.
MAX_BYTES = 1_048_576  # 1 MiB
MAX_DIMENSION = 1024


def fail(message: str) -> "NoReturn":
    """Print a human-readable error and exit non-zero (no raw traceback)."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def resolve_source() -> str:
    """Return the bundled image path, or fail clearly when it is missing.

    The entry image must sit next to this script inside the submitted
    bundle; a missing file means the bundle was built wrong, not that
    the picture is bad, so say exactly which path was expected.
    """
    if not os.path.isfile(SOURCE):
        fail(
            f"bundled source image not found: {SOURCE}\n"
            f"  expected entry.png next to main.py in the repo "
            f"(check the bundle includes it)"
        )
    return SOURCE


def resolve_output_dir() -> str:
    """Normalize MAKEFUN_OUTPUT_DIR (default /output) and create it."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output").strip()
    if not out_dir:
        fail("MAKEFUN_OUTPUT_DIR is set but empty; unset it or give a path")
    out_dir = os.path.abspath(os.path.expanduser(out_dir))
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        fail(f"cannot create output directory {out_dir}: {exc}")
    return out_dir


def jpeg_dimensions(path: str) -> tuple[int, int]:
    """Return (width, height) of a JPEG by parsing its SOF marker.

    Stdlib only; no image library is needed for this one header scan.
    Raises ValueError when the file is not a readable JPEG.
    """
    with open(path, "rb") as fh:
        data = fh.read(2)
        if data != b"\xff\xd8":
            raise ValueError("not a JPEG (missing SOI marker)")
        while True:
            marker = fh.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                raise ValueError("corrupt JPEG marker stream")
            code = marker[1]
            if code in (0xD8, 0xD9) or 0xD0 <= code <= 0xD7:
                continue
            (length,) = struct.unpack(">H", fh.read(2))
            if 0xC0 <= code <= 0xCF and code not in (0xC4, 0xC8, 0xCC):
                segment = fh.read(5)
                if len(segment) < 5:
                    raise ValueError("truncated SOF segment")
                height, width = struct.unpack(">HH", segment[1:5])
                return width, height
            fh.seek(length - 2, os.SEEK_CUR)


def validate_output(path: str) -> None:
    """Fail loudly (non-zero exit) when the output breaks competition rules."""
    if not os.path.isfile(path):
        print(f"error: output missing: {path}", file=sys.stderr)
        sys.exit(1)
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        print(f"error: output {size} bytes exceeds {MAX_BYTES} byte limit",
              file=sys.stderr)
        sys.exit(1)
    try:
        width, height = jpeg_dimensions(path)
    except ValueError as exc:
        print(f"error: cannot read output dimensions: {exc}", file=sys.stderr)
        sys.exit(1)
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        print(f"error: output {width}x{height} exceeds "
              f"{MAX_DIMENSION}x{MAX_DIMENSION} limit", file=sys.stderr)
        sys.exit(1)
    print(f"validated: {path} ({size} bytes, {width}x{height})")


def main() -> None:
    source = resolve_source()
    out_dir = resolve_output_dir()
    out_path = os.path.join(out_dir, OUTPUT_NAME)
    try:
        shutil.copyfile(source, out_path)
    except OSError as exc:
        fail(f"cannot write output {out_path}: {exc}")
    validate_output(out_path)


if __name__ == "__main__":
    main()
