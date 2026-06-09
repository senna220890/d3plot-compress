"""Command-line interface for d3plot_compress."""

import argparse
import sys
from pathlib import Path

from .core import compress_folder, decompress_folder


def main():
    parser = argparse.ArgumentParser(
        prog="d3plot-compress",
        description=(
            "Lossless gzip compression for LS-DYNA d3plot files.\n"
            "Compressed files are readable directly by BETA CAE META post-processor."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  d3plot-compress compress ./results
  d3plot-compress compress ./results --keep-original --level 9
  d3plot-compress decompress ./results
  d3plot-compress decompress ./results --keep-compressed
""",
    )

    parser.add_argument(
        "action",
        choices=["compress", "decompress"],
        help="compress: d3plot → d3plot.gz  |  decompress: d3plot.gz → d3plot",
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing d3plot files",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        help="(compress) Keep uncompressed originals alongside .gz files",
    )
    parser.add_argument(
        "--keep-compressed",
        action="store_true",
        help="(decompress) Keep .gz files alongside restored originals",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=6,
        choices=range(1, 10),
        metavar="1-9",
        help="Gzip compression level: 1=fastest, 9=smallest (default: 6)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    args = parser.parse_args()

    if not args.folder.is_dir():
        print(f"Error: folder not found: {args.folder}", file=sys.stderr)
        sys.exit(1)

    verbose = not args.quiet

    if args.action == "compress":
        results = compress_folder(
            args.folder,
            keep_original=args.keep_original,
            level=args.level,
            verbose=verbose,
        )
        if verbose and results:
            print(f"\nDone. {len(results)} file(s) compressed.")
    else:
        results = decompress_folder(
            args.folder,
            keep_compressed=args.keep_compressed,
            verbose=verbose,
        )
        if verbose and results:
            print(f"\nDone. {len(results)} file(s) decompressed.")


if __name__ == "__main__":
    main()
