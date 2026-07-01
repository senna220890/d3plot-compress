"""Command-line interface for d3plot_compress."""

import argparse
import sys
from pathlib import Path

from .core import compress_folder, decompress_folder
from .precision import UnsupportedModel, compress_folder_single


def main():
    parser = argparse.ArgumentParser(
        prog="d3plot-compress",
        description=(
            "Compression for LS-DYNA d3plot files.\n\n"
            "  compress   : gzip (lossless). Readable by post-processors that\n"
            "               support gzip d3plot (e.g. BETA CAE META).\n"
            "  decompress : restore gzip'd files byte-for-byte.\n"
            "  single     : convert double-precision d3plot to single precision\n"
            "               (~50%% smaller, lossy). Output is a valid d3plot that\n"
            "               ANY post-processor opens natively — useful for tools\n"
            "               that do not accept gzip d3plot files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # gzip (lossless) — for post-processors that read gzip d3plot
  d3plot-compress compress ./results
  d3plot-compress compress ./results --keep-original --level 9
  d3plot-compress decompress ./results

  # single precision (~50% smaller) — opens in ANY post-processor
  d3plot-compress single ./results          # → ./results/compressed_d3plot/

  # maximum reduction for gzip-capable tools: single, then gzip on top
  d3plot-compress single ./results
  d3plot-compress compress ./results/compressed_d3plot
""",
    )

    parser.add_argument(
        "action",
        choices=["compress", "decompress", "single"],
        help=(
            "compress: d3plot → d3plot.gz  |  "
            "decompress: d3plot.gz → d3plot  |  "
            "single: double → single precision d3plot"
        ),
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing d3plot files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="(single) Output folder (default: <folder>/compressed_d3plot)",
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
    elif args.action == "single":
        try:
            compress_folder_single(
                args.folder,
                output_dir=args.output_dir,
                verbose=verbose,
            )
        except (UnsupportedModel, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            print(
                "No output written. This model uses a d3plot feature the "
                "converter does not handle yet.",
                file=sys.stderr,
            )
            sys.exit(1)
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
