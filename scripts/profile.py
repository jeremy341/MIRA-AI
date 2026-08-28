# Profile a model's performance and save results to a JSON file.

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import numpy as np

from src.config import ROOT_DIR
from src.pipeline.models import ModelRegistry

try:
    import torch

    _CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    torch = None  # type: ignore[assignment]
    _CUDA_AVAILABLE = False


def _generate_dummy_image(width: int = 640, height: int = 640) -> Path:
    dummy = ROOT_DIR / "results" / "_dummy_profile.png"
    dummy.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image

        img = Image.fromarray(np.random.randint(0, 255, (height, width, 3), dtype=np.uint8))
        img.save(str(dummy))
        return dummy
    except ImportError:
        import cv2

        img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
        cv2.imwrite(str(dummy), img)
        return dummy


def _peak_gpu_memory_mb() -> float | None:
    if not _CUDA_AVAILABLE:
        return None
    return torch.cuda.max_memory_allocated() / 1_048_576


def _current_gpu_memory_mb() -> float | None:
    if not _CUDA_AVAILABLE:
        return None
    return torch.cuda.memory_allocated() / 1_048_576


def _peak_cpu_memory_mb() -> float | None:
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Linux: KB -> MB
    except (ImportError, AttributeError):
        pass
    try:
        import psutil

        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / 1_048_576
    except (ImportError, Exception):
        return None


def measure_inference(model, image_path: Path, imgsz: int = 640, batch_size: int = 1) -> float:
    from pipeline.models import letterbox_preprocess, _get_device
    import torch

    im_tensor, top, bottom, left, right, r, w0, h0 = letterbox_preprocess(image_path, imgsz)
    backend = getattr(model, "_backend", None)
    if backend is None:
        loaded_model = getattr(model, "_model", None)
        backend = getattr(loaded_model, "model", loaded_model)
    if backend is None:
        raise AttributeError(f"Model {model.name} has no inference backend")
    dev = _get_device(backend)
    im_tensor = im_tensor.repeat(batch_size, 1, 1, 1).to(dev)

    if getattr(dev, "type", None) == "cuda":
        torch.cuda.synchronize(dev)
    start = time.perf_counter()
    with torch.no_grad():
        _ = backend(im_tensor)
    if getattr(dev, "type", None) == "cuda":
        torch.cuda.synchronize(dev)
    return (time.perf_counter() - start) * 1000


def profile_model(
    model_name: str,
    image_path: Path | None,
    iterations: int,
    warmup: int,
    batch_size: int,
) -> dict:
    registry = ModelRegistry()
    registry.discover()
    model = registry.load_model(model_name)

    imgsz = getattr(model, "_imgsz", 640)
    if image_path is None or not image_path.exists():
        print("  No test image provided, generating dummy image...")
        image_path = _generate_dummy_image(imgsz, imgsz)
        print(f"  Dummy image saved to {image_path}")
        _dummy_generated = True
    else:
        _dummy_generated = False

    print(f"  Warming up ({warmup} iterations)...")
    for _ in range(warmup):
        measure_inference(model, image_path, imgsz, batch_size)

    print(f"  Benchmarking ({iterations} iterations, batch_size={batch_size})...")
    latencies: list[float] = []
    if _CUDA_AVAILABLE:
        torch.cuda.reset_peak_memory_stats()
    peak_gpu_before = _peak_gpu_memory_mb()

    for _ in range(iterations):
        lat = measure_inference(model, image_path, imgsz, batch_size)
        latencies.append(lat)

    peak_gpu_after = _peak_gpu_memory_mb()
    peak_cpu = _peak_cpu_memory_mb()

    lat_arr = np.array(latencies)
    mean_lat = float(np.mean(lat_arr))
    p50 = float(np.percentile(lat_arr, 50))
    p90 = float(np.percentile(lat_arr, 90))
    p99 = float(np.percentile(lat_arr, 99))
    throughput = 1000.0 * batch_size / mean_lat if mean_lat > 0 else 0.0
    throughput_batch = throughput

    gpu_mem_peak = None
    if peak_gpu_before is not None and peak_gpu_after is not None:
        gpu_mem_peak = peak_gpu_after

    results = {
        "model": model_name,
        "image": str(image_path),
        "imgsz": imgsz,
        "batch_size": batch_size,
        "iterations": iterations,
        "warmup": warmup,
        "mean_latency_ms": round(mean_lat, 3),
        "p50_latency_ms": round(p50, 3),
        "p90_latency_ms": round(p90, 3),
        "p99_latency_ms": round(p99, 3),
        "min_latency_ms": round(float(np.min(lat_arr)), 3),
        "max_latency_ms": round(float(np.max(lat_arr)), 3),
        "std_latency_ms": round(float(np.std(lat_arr)), 3),
        "throughput_fps": round(throughput, 2),
        "throughput_batch_fps": round(throughput_batch, 2),
        "peak_gpu_memory_mb": round(gpu_mem_peak, 2) if gpu_mem_peak is not None else None,
        "peak_cpu_memory_mb": round(peak_cpu, 2) if peak_cpu is not None else None,
        "cuda_available": _CUDA_AVAILABLE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if _dummy_generated:
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            pass
    return results


def print_summary(results: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  Profiling Summary: {results['model']}")
    print("=" * 60)
    print(f"  Image size       : {results['imgsz']}px")
    print(f"  Batch size       : {results['batch_size']}")
    print(f"  Iterations       : {results['iterations']} (warmup: {results['warmup']})")
    print("-" * 60)
    print(f"  Mean latency     : {results['mean_latency_ms']:.2f} ms")
    print(f"  P50 latency      : {results['p50_latency_ms']:.2f} ms")
    print(f"  P90 latency      : {results['p90_latency_ms']:.2f} ms")
    print(f"  P99 latency      : {results['p99_latency_ms']:.2f} ms")
    print(f"  Min / Max        : {results['min_latency_ms']:.2f} / {results['max_latency_ms']:.2f} ms")
    print(f"  Std deviation    : {results['std_latency_ms']:.2f} ms")
    print("-" * 60)
    print(f"  Throughput (FPS) : {results['throughput_fps']:.1f}")
    if results["batch_size"] > 1:
        print(f"  Throughput (batch): {results['throughput_batch_fps']:.1f} FPS")
    print("-" * 60)
    if results["peak_gpu_memory_mb"] is not None:
        print(f"  Peak GPU memory  : {results['peak_gpu_memory_mb']:.1f} MB")
    if results["peak_cpu_memory_mb"] is not None:
        print(f"  Peak CPU memory  : {results['peak_cpu_memory_mb']:.1f} MB")
    print(f"  CUDA available   : {results['cuda_available']}")
    print("=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile detection model FPS, latency, and memory usage.")
    parser.add_argument(
        "--model",
        required=True,
        help="Model filename (searched in models/detection/).",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Optional path to a test image. A dummy image is generated if omitted.",
    )
    parser.add_argument("--iterations", type=int, default=500, help="Benchmark iterations (default: 500).")
    parser.add_argument("--warmup", type=int, default=50, help="Warmup iterations (default: 50).")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size (default: 1).")
    args = parser.parse_args()

    if args.iterations < 1:
        parser.error("--iterations must be >= 1")
    if args.warmup < 0:
        parser.error("--warmup must be >= 0")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")

    image_path = Path(args.image) if args.image else None
    if image_path is not None and not image_path.exists():
        print(f"Error: image not found at {image_path}")
        sys.exit(1)

    results = profile_model(args.model, image_path, args.iterations, args.warmup, args.batch_size)
    print_summary(results)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = args.model.replace(".", "_").replace("/", "_")
    output_path = ROOT_DIR / "results" / f"profile_{safe_model}_{ts}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved to {output_path}")


if __name__ == "__main__":
    main()
