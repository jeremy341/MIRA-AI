"""Hyperparameter sweep for YOLO training using Optuna.

Requires: pip install optuna
    (ultralytics is already a project dependency)

Usage:
    py scripts/sweep.py --data datasets/mira_all/dataset.yaml
    py scripts/sweep.py --data datasets/mira_all/dataset.yaml --trials 20 --name sweep_v2
    py scripts/sweep.py --data datasets/mira_all/dataset.yaml --model yolo11s.pt --device 0,1
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

try:
    import optuna
except ImportError:
    sys.exit("Optuna is required for hyperparameter sweeps.\nInstall it with:  pip install optuna")

from ultralytics import YOLO

from config import ROOT_DIR, PROJECT_CONFIG
from logger import get_logger

logger = get_logger(__name__)

TRAINING_DEFAULTS = PROJECT_CONFIG.get("training", {})


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="YOLO hyperparameter sweep via Optuna")
    p.add_argument("--model", type=str, default="yolo11n.pt", help="Base model (default: yolo11n.pt)")
    p.add_argument("--data", type=str, required=True, help="Path to dataset YAML")
    p.add_argument("--name", type=str, default=f"sweep_{datetime.now():%Y%m%d_%H%M%S}", help="Experiment name")
    p.add_argument("--trials", type=int, default=10, help="Number of Optuna trials (default: 10)")
    p.add_argument("--epochs", type=int, default=50, help="Max epochs per trial (default: 50)")
    p.add_argument("--device", type=str, default="0", help="CUDA device (default: 0)")
    p.add_argument("--imgsz", type=int, default=640, help="Image size (default: 640)")
    p.add_argument("--patience", type=int, default=30, help="Early stopping patience (default: 30)")
    p.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    return p.parse_args()


def _build_run_dir(args: argparse.Namespace) -> Path:
    run_dir = ROOT_DIR / "results" / f"sweep_{args.name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _objective_factory(args: argparse.Namespace, run_dir: Path):
    """Create and return the Optuna objective function."""

    def objective(trial: optuna.Trial) -> float:
        lr0 = trial.suggest_float("lr0", 1e-5, 1e-2, log=True)
        batch_size = trial.suggest_categorical("batch_size", [8, 16, 32])
        epochs = trial.suggest_categorical("epochs", [50, 100, 150])
        optimizer = trial.suggest_categorical("optimizer", ["SGD", "Adam", "AdamW"])
        lrf = trial.suggest_float("lrf", 0.01, 0.2)
        momentum = trial.suggest_float("momentum", 0.85, 0.98)
        weight_decay = trial.suggest_float("weight_decay", 1e-5, 1e-3, log=True)

        trial_name = f"trial_{trial.number:03d}"
        trial_dir = run_dir / trial_name

        hparams = {
            "lr0": lr0,
            "batch_size": batch_size,
            "epochs": epochs,
            "optimizer": optimizer,
            "lrf": lrf,
            "momentum": momentum,
            "weight_decay": weight_decay,
        }

        logger.info(
            "Trial %d | lr0=%.6f batch=%d epochs=%d opt=%s lrf=%.4f mom=%.4f wd=%.6f",
            trial.number,
            lr0,
            batch_size,
            epochs,
            optimizer,
            lrf,
            momentum,
            weight_decay,
        )

        try:
            model = YOLO(args.model)

            results = model.train(
                data=args.data,
                epochs=epochs,
                batch=batch_size,
                imgsz=args.imgsz,
                lr0=lr0,
                lrf=lrf,
                momentum=momentum,
                weight_decay=weight_decay,
                optimizer=optimizer,
                patience=args.patience,
                device=args.device,
                workers=4,
                amp=True,
                seed=args.seed,
                project=str(run_dir),
                name=trial_name,
                exist_ok=True,
            )

            map50 = float(getattr(results.box, "map50", 0.0))
            map50_95 = float(getattr(results.box, "map", 0.0))

        except Exception as exc:
            logger.error("Trial %d failed: %s", trial.number, exc)
            return 0.0

        metrics = {"map50": map50, "map50_95": map50_95}

        trial.set_user_attr("map50", map50)
        trial.set_user_attr("map50_95", map50_95)

        trial_result = {
            "trial": trial.number,
            "hyperparameters": hparams,
            "metrics": metrics,
            "best_model": str(trial_dir / "weights" / "best.pt"),
            "duration_seconds": 0,
        }

        with open(trial_dir / "sweep_result.json", "w", encoding="utf-8") as f:
            json.dump(trial_result, f, indent=2, default=str)

        logger.info(
            "Trial %d result | mAP50=%.4f  mAP50-95=%.4f",
            trial.number,
            map50,
            map50_95,
        )

        return map50

    return objective


def main() -> None:
    args = parse_args()
    run_dir = _build_run_dir(args)

    logger.info(
        "Sweep '%s' | model=%s  data=%s  trials=%d  max_epochs=%d  device=%s",
        args.name,
        args.model,
        args.data,
        args.trials,
        args.epochs,
        args.device,
    )
    logger.info("Results will be saved to: %s", run_dir)

    study = optuna.create_study(
        study_name=args.name,
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=args.seed),
    )

    t0 = time.time()
    objective = _objective_factory(args, run_dir)
    study.optimize(objective, n_trials=args.trials)
    elapsed = time.time() - t0

    # ── Summary ──────────────────────────────────────────────────
    best = study.best_trial
    logger.info("=" * 60)
    logger.info("Sweep complete in %.1f min (%d trials)", elapsed / 60, len(study.trials))
    logger.info("Best trial: #%d", best.number)
    logger.info("  mAP50:     %.4f", best.value)
    logger.info("  mAP50-95:  %.4f", best.user_attrs.get("map50_95", 0.0))
    logger.info("  Hyperparameters:")
    for k, v in best.params.items():
        logger.info("    %s: %s", k, v)
    logger.info("=" * 60)

    # ── Persist study-level results ──────────────────────────────
    summary = {
        "study_name": args.name,
        "direction": "maximize",
        "n_trials": len(study.trials),
        "best_trial": best.number,
        "best_value": best.value,
        "best_params": best.params,
        "best_user_attrs": best.user_attrs,
        "elapsed_seconds": round(elapsed, 1),
    }

    summary_path = run_dir / "sweep_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info("Summary saved to %s", summary_path)


if __name__ == "__main__":
    main()
