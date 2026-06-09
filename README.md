# d3plot-compress

Lossless gzip compression for **LS-DYNA d3plot** binary result files.

Compressed files are read **directly** by BETA CAE META post-processor — no manual decompression needed before viewing animations.

## Install

```bash
pip install d3plot-compress
```

## Usage

### Command line

```bash
# Compress all d3plot files in a folder (replaces originals with .gz)
d3plot-compress compress /path/to/results

# Compress but keep originals
d3plot-compress compress /path/to/results --keep-original

# Use maximum compression (slower but smallest size)
d3plot-compress compress /path/to/results --level 9

# Decompress (if you need raw files for a tool that doesn't support .gz)
d3plot-compress decompress /path/to/results
```

### Python API

```python
from d3plot_compress import compress_folder, decompress_folder

# Compress
compress_folder("/path/to/results")

# Decompress
decompress_folder("/path/to/results")
```

## How it works

LS-DYNA writes results as a sequence of binary files:

```
d3plot        ← header + first state
d3plot01      ← subsequent time steps
d3plot02
...
```

This tool compresses each file individually using gzip (lossless), producing:

```
d3plot.gz
d3plot01.gz
d3plot02.gz
...
```

BETA CAE META post-processor recognises the `.gz` extension and decompresses on-the-fly, so animations play exactly as with the original files.

## Options

| Flag | Description |
|------|-------------|
| `--level 1-9` | Compression level (1=fastest, 9=smallest, default=6) |
| `--keep-original` | Keep uncompressed files alongside `.gz` |
| `--keep-compressed` | (decompress) Keep `.gz` alongside restored files |
| `--quiet` | Suppress progress output |

## Requirements

- Python 3.10+
- No external dependencies (uses Python's built-in `gzip` module)
