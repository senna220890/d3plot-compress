# d3plot-compress

Compression for **LS-DYNA d3plot** binary result files. Two independent methods:

| Method | Command | Lossless? | Size | Who reads the output |
|--------|---------|-----------|------|----------------------|
| **gzip** | `compress` | ✅ Yes (byte-identical) | ~40–60% smaller | Post-processors that support gzip d3plot (e.g. BETA CAE META), on-the-fly |
| **single precision** | `single` | ⚠️ Lossy (keeps ~7 sig. digits) | ~50% smaller | **Any** post-processor natively — the output is a normal d3plot |

**Which do I use?**

- **BETA CAE META** reads gzip d3plot directly → use `compress`.
- **Tools that do NOT accept gzip d3plot** (e.g. Altair HyperView) → use `single`. It
  produces a valid, half-size d3plot that opens natively — no plugin, no license,
  no extension change.
- **Want maximum reduction on a gzip-capable tool?** Run `single` first, then `compress`
  on the result — the two stack.

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

#### Single-precision compression (for HyperView and other non-gzip tools)

Some post-processors — notably **Altair HyperView** — do **not** load gzip d3plot
files. For those, use `single`, which rewrites a double-precision d3plot as single
precision (~50% smaller). The result is a *normal* d3plot that opens natively in any
post-processor.

```bash
# Writes converted files to  /path/to/results/compressed_d3plot/
d3plot-compress single /path/to/results

# Choose a different output folder
d3plot-compress single /path/to/results --output-dir /path/to/results_single
```

Originals are never modified. If the input is already single precision, the tool
reports it and writes nothing (there is nothing to shrink this way).

> **Note:** single-precision conversion is *lossy* — it keeps ~7 significant digits,
> which is standard and more than sufficient for visualization and animation. If you
> need bit-for-bit identical data, use gzip (`compress`) instead.

#### Maximum reduction (META and other gzip-capable tools)

The two methods stack. Convert to single precision first, then gzip the result:

```bash
d3plot-compress single   /path/to/results
d3plot-compress compress /path/to/results/compressed_d3plot
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
from d3plot_compress import (
    compress_folder,
    decompress_folder,
    compress_folder_single,
)

# gzip (lossless)
compress_folder("/path/to/results")
decompress_folder("/path/to/results")

# single precision (lossy, ~50% smaller, opens in any post-processor)
compress_folder_single("/path/to/results")  # → /path/to/results/compressed_d3plot/
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
| `--level 1-9` | (compress) Gzip level (1=fastest, 9=smallest, default=6) |
| `--keep-original` | (compress) Keep uncompressed files alongside `.gz` |
| `--keep-compressed` | (decompress) Keep `.gz` alongside restored files |
| `--output-dir DIR` | (single) Output folder (default: `<folder>/compressed_d3plot`) |
| `--quiet` | Suppress progress output |

## Limitations of `single`

Single-precision conversion covers standard structural models (solids, shells,
thick shells, beams, node/element results, part & contact titles). It **aborts
with a clear message rather than writing a corrupt file** if the model uses a
feature not yet supported: SPH particles, airbag (CPM) particle data, CFD data,
20-node hexahedra, 8-node shells with extra nodes, or temperature-rate data. If
you hit one of these, please open an issue with the model type.

## Requirements

- Python 3.9+
- No external dependencies (standard library only)
```
