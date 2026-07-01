"""d3plot_compress — compression for LS-DYNA d3plot files.

Two independent methods:

* gzip (lossless)          : ``compress_folder`` / ``decompress_folder``.
  Byte-identical restore. Readable by post-processors that support gzip
  d3plot (e.g. BETA CAE META).

* single precision (lossy) : ``compress_folder_single``.
  Rewrites double-precision d3plot as single precision (~50% smaller). The
  output is a valid d3plot that ANY post-processor opens natively — useful
  for tools that do not accept gzip d3plot files. Can be combined with gzip
  afterwards for additional lossless reduction on top.
"""

from .core import (
    compress_file,
    compress_folder,
    decompress_file,
    decompress_folder,
)
from .precision import compress_folder_single

__version__ = "0.2.0"

__all__ = [
    "compress_file",
    "compress_folder",
    "decompress_file",
    "decompress_folder",
    "compress_folder_single",
]
