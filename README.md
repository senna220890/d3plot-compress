# d3plot-compress

Lossless gzip compression for **LS-DYNA d3plot** binary result files.

Compressed files are read **directly** by BETA CAE META post-processor — no manual decompression needed before viewing animations.

## Install

```bash
pip install d3plot-compress
```

## Usage

### Command line

After installing, try the `d3plot-compress` command first:

```bash
d3plot-compress compress /path/to/results
```

> **If you get "command not found" or "not recognized" (common on Windows)**, use this instead:
> ```bash
> python -m d3plot_compress.cli compress /path/to/results
> ```

#### All commands

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

#### Windows example

```cmd
python -m d3plot_compress.cli compress "C:\Users\YourName\simulation_results"
python -m d3plot_compress.cli decompress "C:\Users\YourName\simulation_results"
```

> **Tip (Windows):** To get the folder path easily, hold **Shift + right-click** the folder
> in File Explorer and choose **"Copy as path"**, then paste it into the command.

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

BETA CAE META post-processor recognises the `.gz` extension and decompresses
on-the-fly, so animations play exactly as with the original files.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: d3plot-compress` | Use `python -m d3plot_compress.cli` instead |
| `pip is not recognized` | Use `python -m pip install d3plot-compress` |
| `No uncompressed d3plot files found` | Check the folder path — files must be named `d3plot`, `d3plot01`, `d3plot02`, etc. |
| Files not opening in META after compress | Make sure files end in `.gz` — META reads these natively |

## Options

| Flag | Description |
|------|-------------|
| `--level 1-9` | Compression level (1=fastest, 9=smallest, default=6) |
| `--keep-original` | Keep uncompressed files alongside `.gz` |
| `--keep-compressed` | (decompress) Keep `.gz` alongside restored files |
| `--quiet` | Suppress progress output |

## Requirements

- Python 3.9+
- No external dependencies (uses Python's built-in `gzip` module)
```
