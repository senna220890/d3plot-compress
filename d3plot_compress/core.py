"""Core compress/decompress logic for LS-DYNA d3plot files."""

from __future__ import annotations

import gzip
import os
import re
import shutil
from pathlib import Path

# Matches: d3plot, d3plot01, d3plot02, ..., d3plot99, d3plot100, etc.
_D3PLOT_PATTERN = re.compile(r"^d3plot(\d*)$", re.IGNORECASE)
_D3PLOT_GZ_PATTERN = re.compile(r"^d3plot(\d*)\.gz$", re.IGNORECASE)


def find_d3plot_files(folder: Path) -> list[Path]:
    """Return uncompressed d3plot files in folder, sorted by sequence number."""
    files = [
        f for f in folder.iterdir()
        if f.is_file() and _D3PLOT_PATTERN.match(f.name)
    ]
    return sorted(files, key=lambda f: _sort_key(f.name))


def find_compressed_files(folder: Path) -> list[Path]:
    """Return compressed d3plot.gz files in folder, sorted by sequence number."""
    files = [
        f for f in folder.iterdir()
        if f.is_file() and _D3PLOT_GZ_PATTERN.match(f.name)
    ]
    return sorted(files, key=lambda f: _sort_key(f.name))


def _sort_key(name: str) -> tuple:
    m = _D3PLOT_PATTERN.match(name) or _D3PLOT_GZ_PATTERN.match(name)
    suffix = m.group(1) if m else ""
    return (int(suffix),) if suffix else (0,)


def compress_file(src: Path, keep_original: bool = False, level: int = 6) -> Path:
    """
    Compress a single d3plot file to <name>.gz in the same folder.
    Returns path to the compressed file.
    """
    dst = src.with_name(src.name + ".gz")
    with src.open("rb") as f_in, gzip.open(dst, "wb", compresslevel=level) as f_out:
        shutil.copyfileobj(f_in, f_out)
    if not keep_original:
        src.unlink()
    return dst


def decompress_file(src: Path, keep_compressed: bool = False) -> Path:
    """
    Decompress a single d3plot.gz file, restoring original name.
    Returns path to the decompressed file.
    """
    # d3plot01.gz  →  d3plot01
    dst = src.with_suffix("")  # strips .gz
    with gzip.open(src, "rb") as f_in, dst.open("wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    if not keep_compressed:
        src.unlink()
    return dst


def compress_folder(
    folder: str | os.PathLike,
    keep_original: bool = False,
    level: int = 6,
    verbose: bool = True,
) -> list[Path]:
    """
    Compress all d3plot files in *folder*.

    Parameters
    ----------
    folder       : path containing d3plot, d3plot01, d3plot02, ...
    keep_original: keep uncompressed originals alongside .gz files
    level        : gzip compression level 1 (fastest) – 9 (smallest), default 6
    verbose      : print progress

    Returns list of compressed file paths.
    """
    folder = Path(folder)
    files = find_d3plot_files(folder)
    if not files:
        if verbose:
            print(f"No uncompressed d3plot files found in: {folder}")
        return []

    results = []
    for f in files:
        if verbose:
            size_mb = f.stat().st_size / 1_048_576
            print(f"  Compressing {f.name} ({size_mb:.1f} MB) ...", end=" ", flush=True)
        out = compress_file(f, keep_original=keep_original, level=level)
        if verbose:
            out_mb = out.stat().st_size / 1_048_576
            print(f"→ {out.name} ({out_mb:.1f} MB)")
        results.append(out)
    return results


def decompress_folder(
    folder: str | os.PathLike,
    keep_compressed: bool = False,
    verbose: bool = True,
) -> list[Path]:
    """
    Decompress all d3plot.gz files in *folder*.

    Parameters
    ----------
    folder         : path containing d3plot.gz, d3plot01.gz, ...
    keep_compressed: keep .gz files alongside restored originals
    verbose        : print progress

    Returns list of decompressed file paths.
    """
    folder = Path(folder)
    files = find_compressed_files(folder)
    if not files:
        if verbose:
            print(f"No compressed d3plot.gz files found in: {folder}")
        return []

    results = []
    for f in files:
        if verbose:
            size_mb = f.stat().st_size / 1_048_576
            print(f"  Decompressing {f.name} ({size_mb:.1f} MB) ...", end=" ", flush=True)
        out = decompress_file(f, keep_compressed=keep_compressed)
        if verbose:
            out_mb = out.stat().st_size / 1_048_576
            print(f"→ {out.name} ({out_mb:.1f} MB)")
        results.append(out)
    return results
