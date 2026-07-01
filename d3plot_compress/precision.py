"""
Precision compression for LS-DYNA d3plot files.

LS-DYNA can write d3plot results in 64-bit (double) precision. The same data
in 32-bit (single) precision is roughly half the size and is still a fully
valid d3plot that post-processors read natively — including tools that do not
accept gzip-compressed d3plot files.

This module converts a double-precision d3plot family to single precision by
walking the binary structure and re-typing each word:

  * integer words  (control data, connectivity, numbering)  int64  -> int32
  * float words    (coordinates, all state/result data)     float64 -> float32
  * text words     (title, part names)                       truncated to fit

Note: single precision is lossy relative to double (it keeps ~7 significant
digits), which is standard and more than sufficient for visualization. Use
this when you need a smaller file that opens directly in any post-processor.
For a lossless option that stays byte-identical, use gzip compression instead
(readable by post-processors that support gzip d3plot).

Pure Python standard library — no third-party dependencies.
"""

from __future__ import annotations

import os
import re
from array import array
from pathlib import Path

_FAMILY_PATTERN = re.compile(r"^d3plot(\d*)$", re.IGNORECASE)

# Title = words 0-9, control section = words 10-63.
N_HEADER_WORDS = 64
INT32_MIN, INT32_MAX = -(2**31), 2**31 - 1


class UnsupportedModel(Exception):
    """Model uses a d3plot feature this converter does not handle yet."""


class D3plotPrecisionConverter:
    """Streams one d3plot family file, emitting a single-precision copy."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0  # current word index (8-byte words)
        self.out = bytearray()

    # ---------------- word-level helpers ----------------

    @property
    def words_total(self) -> int:
        return len(self.data) // 8

    @property
    def words_left(self) -> int:
        return self.words_total - self.pos

    def _slice(self, n_words: int) -> bytes:
        start = self.pos * 8
        end = start + n_words * 8
        if end > len(self.data):
            raise UnsupportedModel(
                f"file truncated: need {n_words} words at word {self.pos}"
            )
        self.pos += n_words
        return self.data[start:end]

    def peek_int(self) -> int:
        raw = self.data[self.pos * 8 : self.pos * 8 + 8]
        return int.from_bytes(raw, "little", signed=True)

    def emit_ints(self, n_words: int) -> list[int]:
        """Convert n int64 words to int32. Returns the values read."""
        if n_words <= 0:
            return []
        src = array("q")
        src.frombytes(self._slice(n_words))
        try:
            dst = array("i", src)
        except OverflowError:
            bad = next(v for v in src if not INT32_MIN <= v <= INT32_MAX)
            raise UnsupportedModel(
                f"integer value {bad} does not fit in 32 bits"
            ) from None
        self.out += dst.tobytes()
        return list(src)

    def emit_floats(self, n_words: int) -> None:
        """Convert n float64 words to float32 (chunked to bound memory)."""
        CHUNK = 4 * 1024 * 1024  # words per chunk
        remaining = n_words
        while remaining > 0:
            n = min(remaining, CHUNK)
            src = array("d")
            src.frombytes(self._slice(n))
            self.out += array("f", src).tobytes()
            remaining -= n

    def emit_chars(self, n_words: int) -> None:
        """Text field: n words of 8 bytes -> same n words of 4 bytes.

        Text fills the field contiguously, so halving the field means
        keeping the first half of its bytes (e.g. an 80-char title
        becomes its first 40 characters).
        """
        raw = self._slice(n_words)
        self.out += raw[: n_words * 4]

    # ---------------- format-aware conversion ----------------

    def convert_root(self) -> dict:
        """Convert the first family file (header + geometry + states)."""
        c = array("q")
        c.frombytes(self.data[: N_HEADER_WORDS * 8])
        if len(c) < N_HEADER_WORDS:
            raise UnsupportedModel("file smaller than d3plot header")

        ctrl = {
            "ndim": c[15], "numnp": c[16], "icode": c[17], "nglbv": c[18],
            "it": c[19], "iu": c[20], "iv": c[21], "ia": c[22],
            "nel8": c[23], "nummat8": c[24],
            "nel2": c[28], "nummat2": c[29],
            "nel4": c[31], "nummat4": c[32],
            "maxint": c[36], "nmsph": c[37], "ngpsph": c[38], "narbs": c[39],
            "nelt": c[40], "nummatt": c[41],
            "ialemat": c[47], "ncfdv1": c[48], "ncfdv2": c[49],
            "npefg": c[54], "nel48": c[55], "idtdt": c[56], "extra": c[57],
        }

        self._check_supported(ctrl)

        # -- header --
        self.emit_chars(10)                    # title (80 -> 40 chars)
        self.pos = 10
        self.emit_ints(3)                      # runtime date, filetype, src version
        self.emit_chars(1)                     # release (text)
        self.emit_floats(1)                    # code version (float)
        self.emit_ints(N_HEADER_WORDS - 15)    # remaining control words

        extra = max(0, int(ctrl["extra"]))
        if extra:
            extra_words = self.emit_ints(extra)
            if extra_words and extra_words[0] > 0:  # NEL20
                raise UnsupportedModel("20-node hexahedra (NEL20 > 0)")

        # -- geometry --
        numnp = int(ctrl["numnp"])
        self.emit_floats(3 * numnp)                     # node coordinates
        self.emit_ints(9 * max(0, int(ctrl["nel8"])))   # solid connectivity
        self.emit_ints(9 * max(0, int(ctrl["nelt"])))   # thick shell connectivity
        self.emit_ints(6 * max(0, int(ctrl["nel2"])))   # beam connectivity
        self.emit_ints(5 * max(0, int(ctrl["nel4"])))   # shell connectivity
        self.emit_ints(max(0, int(ctrl["narbs"])))      # arbitrary numbering
        self.emit_ints(max(0, int(ctrl["ialemat"])))    # ALE material list

        # -- optional title blocks (part/contact names) before the states --
        while self.words_left > 0:
            ntype = self.peek_int()
            if ntype == 90000:                 # extra run title
                self.emit_ints(1)
                self.emit_chars(18)
            elif ntype in (90001, 90002):      # part / contact titles
                _, n = self.emit_ints(2)
                for _ in range(max(0, int(n))):
                    self.emit_ints(1)          # id
                    self.emit_chars(18)        # name (144 -> 72 chars)
            elif ntype == 90010:
                raise UnsupportedModel("extra keyword-lines block (NTYPE 90010)")
            else:
                break

        # -- everything else is float data: states, end markers, padding --
        self.emit_floats(self.words_left)
        return ctrl

    def convert_family_member(self) -> None:
        """Family continuation files contain only state (float) data."""
        self.emit_floats(self.words_left)

    @staticmethod
    def _check_supported(ctrl: dict) -> None:
        problems = []
        if ctrl["ndim"] not in (3, 4):
            problems.append(f"NDIM={ctrl['ndim']} (only 3/4 supported)")
        if ctrl["nel8"] < 0:
            problems.append("10-node solids (NEL8 < 0)")
        if ctrl["nmsph"] > 0:
            problems.append("SPH particles")
        if ctrl["npefg"] > 0:
            problems.append("airbag particle (CPM) data")
        if ctrl["ncfdv1"] or ctrl["ncfdv2"]:
            problems.append("CFD data")
        if ctrl["nel48"] > 0:
            problems.append("8-node shells with extra nodes (NEL48)")
        if ctrl["idtdt"] != 0:
            problems.append(f"IDTDT={ctrl['idtdt']} temperature-rate data")
        if problems:
            raise UnsupportedModel("; ".join(problems))


# ---------------- public helpers ----------------


def detect_word_size(d3plot_path: Path) -> int:
    """Return 4 (single) or 8 (double) by probing NDIM/NUMNP under both layouts."""
    with d3plot_path.open("rb") as f:
        head = f.read(N_HEADER_WORDS * 8)

    def probe(ws: int) -> bool:
        if len(head) < 17 * ws:
            return False
        ndim = int.from_bytes(head[15 * ws : 15 * ws + ws], "little", signed=True)
        numnp = int.from_bytes(head[16 * ws : 16 * ws + ws], "little", signed=True)
        return ndim in (2, 3, 4, 5, 6, 7) and 0 < numnp < 2_000_000_000

    ok4, ok8 = probe(4), probe(8)
    if ok8 and not ok4:
        return 8
    if ok4 and not ok8:
        return 4
    raise UnsupportedModel("could not determine file precision from header")


def find_d3plot_family(folder: Path) -> list[Path]:
    """Return d3plot, d3plot01, ... in folder, sorted by sequence number."""
    files = [
        f for f in folder.iterdir()
        if f.is_file() and _FAMILY_PATTERN.match(f.name)
    ]
    return sorted(files, key=lambda f: int(_FAMILY_PATTERN.match(f.name).group(1) or 0))


def convert_file_to_single(data: bytes, is_root: bool) -> bytes:
    """Convert one family file's bytes from double to single precision."""
    conv = D3plotPrecisionConverter(data)
    if is_root:
        conv.convert_root()
    else:
        conv.convert_family_member()
    return bytes(conv.out)


def compress_folder_single(
    folder: str | os.PathLike,
    output_dir: str | os.PathLike | None = None,
    verbose: bool = True,
) -> list[Path]:
    """
    Convert all d3plot files in *folder* from double to single precision.

    Parameters
    ----------
    folder     : path containing d3plot, d3plot01, d3plot02, ...
    output_dir : where to write converted files (default: <folder>/compressed_d3plot).
                 Must differ from the source folder; created if missing.
    verbose    : print progress

    Returns list of written file paths (empty if input is already single
    precision or no files were found).
    """
    folder = Path(folder)
    dst = Path(output_dir) if output_dir is not None else folder / "compressed_d3plot"

    family = find_d3plot_family(folder)
    if not family:
        if verbose:
            print(f"No d3plot files found in: {folder}")
        return []

    if dst.resolve() == folder.resolve():
        raise ValueError("output_dir must differ from the source folder")

    ws = detect_word_size(family[0])
    if ws == 4:
        if verbose:
            print(
                "These d3plot files are already SINGLE precision — they are as "
                "small as this method can make them. Nothing was written."
            )
        return []

    dst.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    total_in = total_out = 0

    for idx, src in enumerate(family):
        data = src.read_bytes()
        if len(data) % 8:
            raise UnsupportedModel(
                f"{src.name}: size {len(data)} is not a multiple of 8 "
                "(not a double-precision d3plot?)"
            )
        out_bytes = convert_file_to_single(data, is_root=(idx == 0))
        out_path = dst / src.name
        out_path.write_bytes(out_bytes)
        results.append(out_path)
        total_in += len(data)
        total_out += len(out_bytes)
        if verbose:
            print(f"  {src.name}: {len(data):,} → {len(out_bytes):,} bytes")

    if verbose and total_in:
        print(
            f"\nDone. {len(results)} file(s) → {dst}\n"
            f"  {total_in / 1_048_576:.1f} MB → {total_out / 1_048_576:.1f} MB "
            f"({total_out / total_in * 100:.1f}% of original)"
        )
    return results
