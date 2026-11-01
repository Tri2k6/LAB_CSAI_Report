"""Render legible report figures from the existing benchmark summary CSV.

This script only changes chart presentation. It does not run benchmarks, edit CSV,
or replace the original PNG figures copied from the source repository.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


REPORT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_CSV = REPORT_ROOT / "data" / "benchmark_summary.csv"
OUTPUT_DIR = REPORT_ROOT / "img" / "benchmark"
LEVELS = [f"level_{number:02d}" for number in range(1, 16)]
ALGORITHMS = ("bfs", "dfs", "ucs", "astar")
STYLES = {
    "bfs": ("BFS", "#E69F00", "//"),
    "dfs": ("DFS", "#009E73", "xx"),
    "ucs": ("UCS", "#D55E00", "--"),
    "astar": ("A*", "#0072B2", ".."),
}
METRICS = (
    ("mean_search_time_ms", "Thời gian trung bình (ms)", 1.0, "search_time_ms_readable"),
    (
        "mean_peak_python_memory_bytes",
        "Bộ nhớ đỉnh trung bình (KiB)",
        1.0 / 1024.0,
        "peak_python_memory_kib_readable",
    ),
    ("mean_expanded_nodes", "Nút mở rộng trung bình", 1.0, "expanded_nodes_readable"),
)


def read_summary() -> dict[tuple[str, str], dict[str, str]]:
    with SUMMARY_CSV.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    expected = {(level, algorithm) for level in LEVELS for algorithm in ALGORITHMS}
    by_key = {(row["level_id"], row["algorithm"]): row for row in rows}
    if len(rows) != len(expected) or set(by_key) != expected:
        raise ValueError("Summary CSV must contain exactly 15 levels x 4 algorithms")
    for row in rows:
        if (int(row["total_runs"]), int(row["found_runs"])) != (3, 3):
            raise ValueError("A chart row does not contain three FOUND runs")
        for field, _, _, _ in METRICS:
            value = float(row[field])
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid value in {field}")
    return by_key


def render_metric(
    rows: dict[tuple[str, str], dict[str, str]],
    field: str,
    ylabel: str,
    factor: float,
    name: str,
) -> None:
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    ):
        figure, axis = plt.subplots(figsize=(6.3, 3.2))
        positions = list(range(len(LEVELS)))
        bar_width = 0.19
        for index, algorithm in enumerate(ALGORITHMS):
            label, color, hatch = STYLES[algorithm]
            values = [float(rows[(level, algorithm)][field]) * factor for level in LEVELS]
            offsets = [position - 0.285 + index * bar_width for position in positions]
            axis.bar(
                offsets,
                values,
                width=bar_width,
                label=label,
                color=color,
                edgecolor="#333333",
                linewidth=0.3,
                hatch=hatch,
                zorder=3,
            )

        axis.set_xlim(-0.55, len(LEVELS) - 0.45)
        axis.set_ylim(bottom=0)
        axis.set_xticks(positions, [level[-2:] for level in LEVELS])
        axis.set_xlabel("Màn chơi")
        axis.set_ylabel(ylabel)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axis.grid(axis="y", color="#cccccc", linewidth=0.5, zorder=0)
        axis.spines[["top", "right"]].set_visible(False)
        axis.legend(loc="upper left", ncol=4, frameon=False, handlelength=1.2)
        figure.subplots_adjust(left=0.15, right=0.99, bottom=0.17, top=0.96)

        for suffix, kwargs in (("pdf", {}), ("png", {"dpi": 300})):
            figure.savefig(OUTPUT_DIR / f"{name}.{suffix}", **kwargs)
        plt.close(figure)


def main() -> None:
    rows = read_summary()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for field, ylabel, factor, name in METRICS:
        render_metric(rows, field, ylabel, factor, name)


if __name__ == "__main__":
    main()
