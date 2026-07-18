"""Detection model adapters for MIRA benchmarking pipeline.

Provides abstract base + concrete adapters so third-party models
can be benchmarked alongside YOLO models.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import CLASS_NAMES, DETECTION_DIR, DETECTION_MODEL_LABELS


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[float, float, float, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": list(self.bbox),
        }


@dataclass
class InferenceResult:
    detections: list[Detection]
    latency_ms: float
    model_name: str
    image_path: str | None = None


class DetectionModel(ABC):
    def __init__(self, path: str | Path, name: str):
        self.path = Path(path)
        self.name = name
        self._loaded = False

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def predict(
        self,
        image: str | Path,
        conf: float = 0.25,
        iou: float = 0.45,
    ) -> InferenceResult: ...

    def _parse_yolo_results(self, results, latency_ms: float, image: str | Path, class_names: list[str] | None = None) -> InferenceResult:
        """Parse Ultralytics YOLO results into InferenceResult."""
        names = class_names or CLASS_NAMES
        detections: list[Detection] = []
        boxes = results[0].boxes
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().tolist()
            confs = boxes.conf.cpu().tolist()
            cls_ids = boxes.cls.cpu().tolist()
            for i in range(len(xyxy)):
                cid = int(cls_ids[i])
                detections.append(
                    Detection(
                        class_id=cid,
                        class_name=names[cid] if cid < len(names) else f"class_{cid}",
                        confidence=float(confs[i]),
                        bbox=tuple(xyxy[i]),
                    )
                )
        return InferenceResult(
            detections=detections,
            latency_ms=latency_ms,
            model_name=self.name,
            image_path=str(image),
        )

    def __repr__(self) -> str:
        state = "loaded" if self._loaded else "not loaded"
        return f"{type(self).__name__}({self.name!r}, {state})"


class YOLOAdapter(DetectionModel):
    model_type = "yolo_pt"

    def load(self) -> None:
        from ultralytics import YOLO

        self._model = YOLO(str(self.path))
        self._loaded = True

    def predict(
        self,
        image: str | Path,
        conf: float = 0.25,
        iou: float = 0.45,
    ) -> InferenceResult:
        if not self._loaded:
            self.load()

        start = time.perf_counter()
        results = self._model(str(image), conf=conf, iou=iou, verbose=False)
        latency_ms = (time.perf_counter() - start) * 1000

        return self._parse_yolo_results(results, latency_ms, image)


class YOLOTFLiteAdapter(DetectionModel):
    model_type = "yolo_tflite"

    def load(self) -> None:
        from ultralytics import YOLO

        self._model = YOLO(str(self.path), task="detect")
        self._loaded = True

    def predict(
        self,
        image: str | Path,
        conf: float = 0.25,
        iou: float = 0.45,
    ) -> InferenceResult:
        if not self._loaded:
            self.load()

        if "int8" in self.path.name.lower():
            conf = min(conf, 0.25)

        start = time.perf_counter()
        results = self._model(str(image), conf=conf, iou=iou, verbose=False)
        latency_ms = (time.perf_counter() - start) * 1000

        return self._parse_yolo_results(results, latency_ms, image)


class ThirdPartyAdapter(DetectionModel):
    model_type = "third_party"

    def __init__(
        self,
        path: str | Path,
        name: str,
        model_type: str = "third_party",
        class_names: list[str] | None = None,
    ):
        super().__init__(path, name)
        self.model_type = model_type
        self.class_names = class_names or CLASS_NAMES
        self._model = None

    def load(self) -> None:
        import logging

        log = logging.getLogger(__name__)
        suffix = self.path.suffix.lower()
        if suffix in (".tflite", ".onnx", ".pt"):
            try:
                from ultralytics import YOLO

                task = "detect" if suffix == ".tflite" else None
                self._model = YOLO(str(self.path), task=task)
                self._loaded = True
                log.info("ThirdPartyAdapter loaded %s via ultralytics YOLO", self.path.name)
                return
            except Exception as exc:
                log.warning("Failed to load %s with ultralytics: %s", self.path.name, exc)
        else:
            log.warning(
                "ThirdPartyAdapter cannot auto-load %s (suffix %s). "
                "Subclass ThirdPartyAdapter and override load()/predict().",
                self.path.name,
                suffix,
            )
        self._loaded = False

    def predict(
        self,
        image: str | Path,
        conf: float = 0.25,
        iou: float = 0.45,
    ) -> InferenceResult:
        if not self._loaded:
            self.load()
        if self._model is not None:
            try:
                start = time.perf_counter()
                results = self._model(str(image), conf=conf, iou=iou, verbose=False)
                latency_ms = (time.perf_counter() - start) * 1000
                return self._parse_yolo_results(results, latency_ms, image, self.class_names)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning("ThirdPartyAdapter.predict failed: %s", exc)
        return InferenceResult(detections=[], latency_ms=0.0, model_name=self.name, image_path=str(image))


class ModelRegistry:
    def __init__(self, detection_dir: Path | str | None = None):
        self.detection_dir = Path(detection_dir) if detection_dir else DETECTION_DIR
        self._models: dict[str, dict[str, Any]] = {}
        self._adapters: dict[str, DetectionModel] = {}

    def discover(self) -> int:
        self._models.clear()

        for p in sorted(self.detection_dir.iterdir()):
            if p.suffix.lower() in (".pt", ".pth"):
                label = DETECTION_MODEL_LABELS.get(p.name, p.stem)
                self._models[p.name] = {
                    "path": p,
                    "model_type": "yolo_pt",
                    "label": label,
                    "is_third_party": False,
                }
            elif p.suffix == ".tflite":
                label = DETECTION_MODEL_LABELS.get(p.name, p.stem)
                self._models[p.name] = {
                    "path": p,
                    "model_type": "yolo_tflite",
                    "label": label,
                    "is_third_party": False,
                }
            elif p.suffix == ".yaml":
                self._load_descriptor(p)

        return len(self._models)

    def _load_descriptor(self, yaml_path: Path) -> None:
        import yaml

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        required = ["name", "type"]
        missing = [f for f in required if f not in data]
        if missing:
            print(f"Warning: Model descriptor {yaml_path.name} missing fields: {missing}")
            return

        name = data.get("name", yaml_path.stem)
        model_path = self.detection_dir / data.get("model_file", "")
        if not model_path.exists():
            model_path = Path(data.get("model_file", ""))

        self._models[name] = {
            "path": model_path,
            "model_type": data.get("type", "third_party"),
            "label": data.get("label", name),
            "class_names": data.get("class_names", CLASS_NAMES),
            "is_third_party": True,
        }

    def list_models(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "path": str(info["path"]),
                "model_type": info["model_type"],
                "label": info["label"],
                "exists": info["path"].exists(),
                "size_mb": round(info["path"].stat().st_size / 1_048_576, 1) if info["path"].exists() else None,
            }
            for name, info in self._models.items()
        ]

    def get_model(self, name: str) -> dict[str, Any]:
        if name not in self._models:
            available = ", ".join(self._models.keys())
            raise KeyError(f"Unknown model '{name}'. Available: {available}")
        return self._models[name]

    def load_model(self, name: str) -> DetectionModel:
        if name in self._adapters and self._adapters[name]._loaded:
            return self._adapters[name]

        info = self.get_model(name)
        model_type = info["model_type"]
        path = info["path"]

        if info.get("is_third_party"):
            adapter = ThirdPartyAdapter(
                path=path,
                name=name,
                model_type=model_type,
                class_names=info.get("class_names"),
            )
        elif model_type == "yolo_pt":
            adapter = YOLOAdapter(path=path, name=name)
        elif model_type == "yolo_tflite":
            adapter = YOLOTFLiteAdapter(path=path, name=name)
        else:
            raise ValueError(f"Unknown model_type '{model_type}' for model '{name}'")

        adapter.load()
        self._adapters[name] = adapter
        return adapter
