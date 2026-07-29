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

import cv2
import numpy as np

from ..config import (
    CLASS_NAMES,
    DEFAULT_CONF,
    DEFAULT_IMGSZ,
    DEFAULT_IOU,
    DETECTION_DIR,
    TFLITE_INT8_CONF,
    get_tflite_imgsz,
)
from ..exceptions import ModelError
from ..logger import get_logger

log = get_logger(__name__)


def letterbox_preprocess(
    image_path: str | Path,
    imgsz: int,
) -> tuple[np.ndarray, int, int, int, int, float, int, int]:
    """Load and preprocess an image for YOLO inference.

    Returns (tensor, top, bottom, left, right, scale, orig_w, orig_h).
    """
    import torch

    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    h0, w0 = img_bgr.shape[:2]
    if h0 == 0 or w0 == 0:
        raise ValueError(f"Image has zero dimension ({w0}x{h0}): {image_path}")
    r = min(imgsz / h0, imgsz / w0)
    new_h, new_w = int(h0 * r), int(w0 * r)
    dh = imgsz - new_h
    dw = imgsz - new_w
    top = dh // 2
    bottom = dh - top
    left = dw // 2
    right = dw - left
    im = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    im_tensor = torch.from_numpy(im.transpose(2, 0, 1)[::-1].copy()).float() / 255.0
    im_tensor = im_tensor.unsqueeze(0)
    return im_tensor, top, bottom, left, right, r, w0, h0


def adjust_boxes_to_original(
    preds,
    left: int,
    top: int,
    r: float,
    w0: int,
    h0: int,
):
    """Convert letterbox-adjusted box coords back to original image space."""
    import torch

    boxes = preds[:, :4].clone()
    boxes[:, 0] -= left
    boxes[:, 1] -= top
    boxes[:, 2] -= left
    boxes[:, 3] -= top
    boxes = torch.clamp(boxes / r, 0)
    boxes[:, 0::2] = torch.clamp(boxes[:, 0::2], 0, w0 - 1)
    boxes[:, 1::2] = torch.clamp(boxes[:, 1::2], 0, h0 - 1)
    return boxes


def _get_device(backend: Any):
    """Get the torch device from a model backend."""
    import torch

    if hasattr(backend, "device"):
        return backend.device
    if hasattr(backend, "parameters"):
        params = list(backend.parameters())
        if params:
            return next(backend.parameters()).device
    return torch.device("cpu")


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
        conf: float | None = None,
        iou: float | None = None,
    ) -> InferenceResult: ...

    def _parse_yolo_results(
        self, results, latency_ms: float, image: str | Path, class_names: list[str] | None = None
    ) -> InferenceResult:
        names = class_names or CLASS_NAMES
        detections: list[Detection] = []
        boxes = results[0].boxes
        if boxes is not None and len(boxes) > 0:
            xyxy = boxes.xyxy.cpu().tolist()
            confs = boxes.conf.cpu().tolist()
            cls_ids = boxes.cls.cpu().tolist()
            for i in range(len(xyxy)):
                cid = int(cls_ids[i])
                bbox = tuple(xyxy[i])
                detections.append(
                    Detection(
                        class_id=cid,
                        class_name=names[cid] if cid < len(names) else f"class_{cid}",
                        confidence=float(confs[i]),
                        bbox=bbox,
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
        from ultralytics.nn.autobackend import AutoBackend
        from ultralytics.utils.torch_utils import select_device

        if not self.path.exists():
            raise ModelError(f"Model file not found: {self.path}")
        self._model = YOLO(str(self.path))
        if callable(self._model.model):
            self._backend = self._model.model
            if hasattr(self._backend, "eval"):
                self._backend.eval()
        else:
            self._backend = AutoBackend(
                model=str(self.path),
                device=select_device("auto"),
                dnn=False,
                data=None,
                fp16=False,
            )
        self._names = self._model.names if hasattr(self._model, "names") else {}
        try:
            if callable(self._model.model):
                self._imgsz = (
                    self._model.args.get("imgsz", DEFAULT_IMGSZ) if hasattr(self._model, "args") else DEFAULT_IMGSZ
                )
            else:
                self._imgsz = DEFAULT_IMGSZ
                if hasattr(self._backend, "backend") and hasattr(self._backend.backend, "get_input_details"):
                    inp = self._backend.backend.get_input_details()
                    self._imgsz = inp[0]["shape"][-1] if inp else DEFAULT_IMGSZ
        except (IndexError, KeyError, AttributeError, TypeError):
            self._imgsz = DEFAULT_IMGSZ
        self._loaded = True

    def predict(
        self,
        image: str | Path,
        conf: float | None = None,
        iou: float | None = None,
    ) -> InferenceResult:
        if conf is None:
            conf = DEFAULT_CONF
        if iou is None:
            iou = DEFAULT_IOU
        if not (0.0 <= conf <= 1.0):
            raise ValueError(f"conf must be in [0, 1], got {conf}")
        if not (0.0 <= iou <= 1.0):
            raise ValueError(f"iou must be in [0, 1], got {iou}")
        if not self._loaded:
            self.load()

        import torch

        from ultralytics.utils.ops import non_max_suppression as _nms

        im_tensor, top, bottom, left, right, r, w0, h0 = letterbox_preprocess(image, self._imgsz)
        dev = _get_device(self._backend)
        im_tensor = im_tensor.to(dev)

        start = time.perf_counter()
        with torch.no_grad():
            raw_preds = self._backend(im_tensor)
        latency_ms = (time.perf_counter() - start) * 1000

        preds = _nms(raw_preds, conf_thres=conf, iou_thres=iou, max_det=300, multi_label=True)[0]

        detections: list[Detection] = []
        if len(preds) > 0:
            boxes = adjust_boxes_to_original(preds, left, top, r, w0, h0)
            for i in range(len(preds)):
                cid = int(preds[i, 5].item())
                detections.append(
                    Detection(
                        class_id=cid,
                        class_name=self._names.get(cid, f"class_{cid}"),
                        confidence=float(preds[i, 4].item()),
                        bbox=tuple(boxes[i].cpu().tolist()),
                    )
                )

        return InferenceResult(
            detections=detections,
            latency_ms=latency_ms,
            model_name=self.name,
            image_path=str(image),
        )


class YOLOTFLiteAdapter(DetectionModel):
    model_type = "yolo_tflite"

    def load(self) -> None:
        from ultralytics import YOLO
        from ultralytics.nn.autobackend import AutoBackend
        from ultralytics.utils.torch_utils import select_device

        if not self.path.exists():
            raise ModelError(f"Model file not found: {self.path}")
        self._model = YOLO(str(self.path), task="detect")
        self._backend = AutoBackend(
            model=str(self.path),
            device=select_device("cpu"),
            dnn=False,
            data=None,
            fp16=False,
        )
        self._names = self._model.names if hasattr(self._model, "names") else {}
        # Detect correct input size from model
        if hasattr(self._backend, "backend") and hasattr(self._backend.backend, "interpreter"):
            self._imgsz = get_tflite_imgsz(self.path)
        else:
            self._imgsz = (
                self._model.args.get("imgsz", DEFAULT_IMGSZ) if hasattr(self._model, "args") else DEFAULT_IMGSZ
            )
        self._loaded = True

    def predict(
        self,
        image: str | Path,
        conf: float | None = None,
        iou: float | None = None,
    ) -> InferenceResult:
        if conf is None:
            conf = DEFAULT_CONF
        if iou is None:
            iou = DEFAULT_IOU
        if not (0.0 <= conf <= 1.0):
            raise ValueError(f"conf must be in [0, 1], got {conf}")
        if not (0.0 <= iou <= 1.0):
            raise ValueError(f"iou must be in [0, 1], got {iou}")
        if not self._loaded:
            self.load()
        tflite_conf = min(conf, TFLITE_INT8_CONF) if "int8" in self.path.name.lower() else conf

        import torch

        from ultralytics.utils.ops import non_max_suppression as _nms

        im_tensor, top, bottom, left, right, r, w0, h0 = letterbox_preprocess(image, self._imgsz)
        dev = getattr(self._backend, "device", torch.device("cpu"))
        im_tensor = im_tensor.to(dev)

        start = time.perf_counter()
        with torch.no_grad():
            raw_preds = self._backend(im_tensor)
        latency_ms = (time.perf_counter() - start) * 1000

        preds = _nms(
            raw_preds, conf_thres=tflite_conf, iou_thres=iou, max_det=300, multi_label=True
        )[0]

        detections: list[Detection] = []
        if len(preds) > 0:
            boxes = adjust_boxes_to_original(preds, left, top, r, w0, h0)
            for i in range(len(preds)):
                cid = int(preds[i, 5].item())
                detections.append(
                    Detection(
                        class_id=cid,
                        class_name=self._names.get(cid, f"class_{cid}"),
                        confidence=float(preds[i, 4].item()),
                        bbox=tuple(boxes[i].cpu().tolist()),
                    )
                )

        return InferenceResult(
            detections=detections,
            latency_ms=latency_ms,
            model_name=self.name,
            image_path=str(image),
        )


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
        self._load_failed = False

    def load(self) -> None:
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
                self._loaded = False
                raise RuntimeError(f"Failed to load model {self.path.name}: {exc}") from exc
        else:
            log.warning(
                "ThirdPartyAdapter cannot auto-load %s (suffix %s). "
                "Subclass ThirdPartyAdapter and override load()/predict().",
                self.path.name,
                suffix,
            )
            self._load_failed = True
        self._loaded = False

    def predict(
        self,
        image: str | Path,
        conf: float | None = None,
        iou: float | None = None,
    ) -> InferenceResult:
        if conf is None:
            conf = DEFAULT_CONF
        if iou is None:
            iou = DEFAULT_IOU
        if not (0.0 <= conf <= 1.0):
            raise ValueError(f"conf must be in [0, 1], got {conf}")
        if not (0.0 <= iou <= 1.0):
            raise ValueError(f"iou must be in [0, 1], got {iou}")
        if not self._loaded and not self._load_failed:
            self.load()
        if self._model is None:
            log.warning("ThirdPartyAdapter.predict() called before load() — returning empty result")
            return InferenceResult(detections=[], latency_ms=0.0, model_name=self.name, image_path=str(image))

        import torch

        from ultralytics.utils.ops import non_max_suppression as _nms

        try:
            imgsz = self._model.args.get("imgsz", DEFAULT_IMGSZ) if hasattr(self._model, "args") else DEFAULT_IMGSZ
            im_tensor, top, bottom, left, right, r, w0, h0 = letterbox_preprocess(image, imgsz)

            device = _get_device(self._model.model) if hasattr(self._model, "model") else torch.device("cpu")
            if isinstance(device, torch.device):
                im_tensor = im_tensor.to(device)

            start = time.perf_counter()
            with torch.no_grad():
                raw_preds = self._model.model(im_tensor)
            latency_ms = (time.perf_counter() - start) * 1000

            preds = _nms(raw_preds, conf_thres=conf, iou_thres=iou, max_det=300, multi_label=True)[0]

            detections: list[Detection] = []
            if len(preds) > 0:
                boxes = adjust_boxes_to_original(preds, left, top, r, w0, h0)
                names = self.class_names
                for i in range(len(preds)):
                    cid = int(preds[i, 5].item())
                    detections.append(
                        Detection(
                            class_id=cid,
                            class_name=names[cid] if cid < len(names) else f"class_{cid}",
                            confidence=float(preds[i, 4].item()),
                            bbox=tuple(boxes[i].cpu().tolist()),
                        )
                    )

            return InferenceResult(
                detections=detections,
                latency_ms=latency_ms,
                model_name=self.name,
                image_path=str(image),
            )
        except Exception as e:
            log.error(f"Prediction failed: {type(e).__name__}: {e}")
            log.exception("ThirdPartyAdapter.predict failed for %s", image)
            return InferenceResult(detections=[], latency_ms=0.0, model_name=self.name, image_path=str(image))


class ModelRegistry:
    def __init__(self, detection_dir: Path | str | None = None):
        self.detection_dir = Path(detection_dir) if detection_dir else DETECTION_DIR
        self._models: dict[str, dict[str, Any]] = {}
        self._adapters: dict[str, DetectionModel] = {}

    def discover(self) -> int:
        self._models.clear()
        self._adapters.clear()

        if not self.detection_dir.exists():
            return 0

        loaded_sidecars: set[str] = set()
        sidecar_meta: dict[str, dict] = {}

        for p in sorted(self.detection_dir.iterdir()):
            if p.suffix in (".yaml", ".yml") and not p.name.startswith("example"):
                registered = self._load_descriptor(p)
                name = p.stem
                if registered:
                    loaded_sidecars.add(name)
                else:
                    meta = self._load_sidecar_meta(p)
                    if meta:
                        sidecar_meta[name] = meta

        for name, meta in sidecar_meta.items():
            pt_path = self.detection_dir / f"{name}.pt"
            if pt_path.exists():
                self._models[f"{name}.pt"] = {
                    "path": pt_path,
                    "model_type": "yolo_pt",
                    "label": meta.get("display_name", meta.get("label", name)),
                    "is_third_party": False,
                    "class_names": meta.get("class_names"),
                    "tags": meta.get("tags", []),
                    "metrics": meta.get("metrics", {}),
                }
                tflite_path = self.detection_dir / f"{name}_int8.tflite"
                if tflite_path.exists():
                    self._models[f"{name}_int8.tflite"] = {
                        "path": tflite_path,
                        "model_type": "yolo_tflite",
                        "label": f"{meta.get('display_name', name)} INT8",
                        "is_third_party": False,
                    }
                onnx_path = self.detection_dir / f"{name}.onnx"
                if onnx_path.exists():
                    self._models[f"{name}.onnx"] = {
                        "path": onnx_path,
                        "model_type": "yolo_onnx",
                        "label": f"{meta.get('display_name', name)} ONNX",
                        "is_third_party": False,
                    }

        for p in sorted(self.detection_dir.iterdir()):
            stem = p.stem
            if stem in loaded_sidecars:
                continue
            if p.suffix.lower() in (".pt", ".pth"):
                if f"{p.name}" in self._models:
                    continue
                self._models[p.name] = {
                    "path": p,
                    "model_type": "yolo_pt",
                    "label": p.stem,
                    "is_third_party": False,
                }
            elif p.suffix == ".tflite":
                base_name = stem.replace("_int8", "").replace("_fp32", "")
                if base_name in loaded_sidecars:
                    continue
                if f"{p.name}" in self._models:
                    continue
                self._models[p.name] = {
                    "path": p,
                    "model_type": "yolo_tflite",
                    "label": p.stem,
                    "is_third_party": False,
                }

        return len(self._models)

    def _load_sidecar_meta(self, yaml_path: Path) -> dict | None:
        import yaml

        try:
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                return None
            return data
        except Exception as exc:
            log.warning("Failed to load sidecar %s: %s", yaml_path.name, exc)
            return None

    def _load_descriptor(self, yaml_path: Path) -> bool:
        import yaml

        try:
            with open(yaml_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            return False

        if not data or not isinstance(data, dict):
            return False

        # Support both "type" and "model_type" as the type field
        if "model_type" in data and "type" not in data:
            data["type"] = data["model_type"]

        required = ["name", "type"]
        missing = [f for f in required if f not in data]
        if missing:
            log.warning("Model descriptor %s missing fields: %s", yaml_path.name, missing)
            return False

        name = data.get("name", yaml_path.stem)
        model_file = data.get("model_file", "")
        if not model_file:
            return False

        model_path = (self.detection_dir / model_file).resolve()
        try:
            model_path.relative_to(self.detection_dir.resolve())
        except ValueError:
            log.warning(
                "Model file %s for %s escapes detection directory, skipping",
                model_file,
                name,
            )
            return False
        if not model_path.exists():
            raw = Path(model_file).expanduser()
            if not raw.is_absolute():
                raw = (self.detection_dir / raw).resolve()
            else:
                raw = raw.resolve()
            try:
                raw.relative_to(self.detection_dir.resolve())
            except ValueError:
                log.warning(
                    "Model file %s for %s escapes detection directory, skipping",
                    model_file,
                    name,
                )
                return False
            model_path = raw
        if not model_path.exists():
            log.warning("Model file %s for %s not found, skipping", model_file, name)
            return False

        self._models[name] = {
            "path": model_path,
            "model_type": data.get("type", "third_party"),
            "label": data.get("display_name", data.get("label", name)),
            "class_names": data.get("class_names", CLASS_NAMES),
            "is_third_party": True,
        }
        return True

    def list_models(self) -> list[dict[str, Any]]:
        def _safe_stat(p: Path) -> float | None:
            try:
                return round(p.stat().st_size / 1_048_576, 1) if p.exists() else None
            except (OSError, FileNotFoundError):
                return None

        return [
            {
                "name": name,
                "path": str(info["path"]),
                "model_type": info["model_type"],
                "label": info["label"],
                "exists": info["path"].exists(),
                "size_mb": _safe_stat(info["path"]),
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
        else:
            try:
                from .registry import get_model_adapters

                adapters = get_model_adapters()
                if model_type in adapters:
                    cls = adapters[model_type].adapter_class
                    adapter = cls(path=path, name=name)
                else:
                    raise KeyError(model_type)
            except (ImportError, KeyError):
                if model_type == "yolo_pt" or model_type == "yolo_onnx":
                    adapter = YOLOAdapter(path=path, name=name)
                elif model_type == "yolo_tflite":
                    adapter = YOLOTFLiteAdapter(path=path, name=name)
                else:
                    raise ValueError(f"Unknown model_type '{model_type}' for model '{name}'") from None

        adapter.load()
        self._adapters[name] = adapter
        return adapter
