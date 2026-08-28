# Side-by-side comparison of multiple detection models. Loads 2+ YOLO models, runs them on the same validation dataset, and produces a comparison table (markdown) plus a bar chart saved to results/.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from src.config import CLASS_NAMES, ROOT_DIR
from src.pipeline.benchmark import BenchmarkResult, ModelBenchmark
from src.pipeline.models import ModelRegistry

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _model_size_mb(path: Path) -> float:
    return path.stat().st_size / 1_048_576 if path.exists() else 0.0


def _rank_results(results: list[BenchmarkResult]) -> list[BenchmarkResult]:
    return sorted(results, key=lambda result: result.overall_f1, reverse=True)


def build_comparison(results: list[BenchmarkResult]) -> str:
    # Return markdown table which compares models
    sorted_res = _rank_results(results)

    header = "| Model | Size (MB) | Latency (ms) | Throughput (FPS) | Precision | Recall | F1 | mAP50 | mAP50-95 |"
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|"
    rows = [header, sep]

    for r in sorted_res:
        size = _model_size_mb(Path(r.model_path))
        throughput = 1000.0 / r.avg_latency_ms if r.avg_latency_ms > 0 else 0.0
        rows.append(
            f"| {r.model_name} "
            f"| {size:.1f} "
            f"| {r.avg_latency_ms:.1f} "
            f"| {throughput:.1f} "
            f"| {r.overall_precision:.1%} "
            f"| {r.overall_recall:.1%} "
            f"| {r.overall_f1:.1%} "
            f"| {r.map50:.1%} "
            f"| {r.map50_95:.1%} |"
        )

    return "\n".join(rows)


def build_per_class_table(results: list[BenchmarkResult]) -> str:
    # Return a markdown table with per-class precision / recall / F1.
    sorted_res = _rank_results(results)
    headers = ["Model"]
    for cls in CLASS_NAMES:
        headers.extend([f"{cls} P", f"{cls} R", f"{cls} F1"])
    sep = ["|---"] + ["|---:" for _ in headers[1:]]
    sep.append("|")

    rows = ["| " + " | ".join(headers) + " |", "".join(sep)]

    for r in sorted_res:
        cells = [r.model_name]
        for cls in CLASS_NAMES:
            m = r.per_class.get(cls)
            if m:
                cells.extend(
                    [
                        f"{m.precision:.1%}",
                        f"{m.recall:.1%}",
                        f"{m.f1:.1%}",
                    ]
                )
            else:
                cells.extend(["-", "-", "-"])
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)


def plot_comparison(results: list[BenchmarkResult], output_path: Path) -> None:
    # Generate a grouped bar chart comparing mAP50, F1, and latency
    sorted_res = _rank_results(results)
    names = [r.model_name for r in sorted_res]
    map50_vals = [r.map50 * 100 for r in sorted_res]
    f1_vals = [r.overall_f1 * 100 for r in sorted_res]
    lat_vals = [r.avg_latency_ms for r in sorted_res]

    x = np.arange(len(names))
    width = 0.3

    fig, ax1 = plt.subplots(figsize=(max(8, len(names) * 2), 5))

    ax1.bar(x - width, map50_vals, width, label="mAP50 (%)", color="#1f77b4", edgecolor="#333", linewidth=0.7)
    ax1.bar(x, f1_vals, width, label="F1 (%)", color="#2ca02c", edgecolor="#333", linewidth=0.7)

    ax1.set_ylabel("Score (%)", fontsize=10, fontweight="bold")
    ax1.set_ylim(0, 105)
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax1.grid(axis="y", linestyle="--")
    ax1.legend(loc="upper left", fontsize=9)

    ax2 = ax1.twinx()
    ax2.bar(
        x + width, lat_vals, width, label="Latency (ms)", color="#d62728", alpha=0.6, edgecolor="#333", linewidth=0.7
    )
    ax2.set_ylabel("Latency (ms)", fontsize=10, fontweight="bold", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax2.legend(loc="upper right", fontsize=9)

    plt.title("Model Comparison Detection Metrics", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"  Chart saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare multiple detection models side-by-side.")
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="Model filenames to compare (at least 2). Searched in models/detection/.",
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to YOLO-format dataset YAML or directory.",
    )
    parser.add_argument("--batch", type=int, default=1, help="Batch size")
    parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold (default: 0.5).")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save the markdown comparison report.",
    )
    args = parser.parse_args()

    if len(args.models) < 2:
        parser.error("At least 2 models are required for comparison.")
    if args.batch != 1:
        parser.error("Batch comparison is not supported; use --batch 1.")

    dataset_path = Path(args.data)
    if not dataset_path.exists():
        print(f"Error: dataset not found at {dataset_path}")
        sys.exit(1)

    registry = ModelRegistry()
    registry.discover()

    models = []
    for name in args.models:
        try:
            models.append(registry.load_model(name))
        except (KeyError, FileNotFoundError, ValueError) as exc:
            print(f"Error loading model '{name}': {exc}")
            sys.exit(1)

    print(f"Comparing {len(models)} models on {dataset_path.name}...")
    benchmark = ModelBenchmark(models=models, dataset=dataset_path, conf=args.conf)
    results = benchmark.run()

    table_md = build_comparison(results)
    per_class_md = build_per_class_table(results)

    print("\n" + table_md + "\n")
    print(per_class_md + "\n")

    chart_path = ROOT_DIR / "results" / "model_comparison.png"
    plot_comparison(results, chart_path)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        full_report = f"# Model Comparison Report\n\n{table_md}\n\n## Per-Class Breakdown\n\n{per_class_md}\n"
        out.write_text(full_report, encoding="utf-8")
        print(f"  Report saved to {out}")

    json_path = ROOT_DIR / "results" / "model_comparison.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    print(f"  JSON results saved to {json_path}")


if __name__ == "__main__":
    main()
