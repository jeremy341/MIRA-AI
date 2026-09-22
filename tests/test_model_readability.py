import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import torch

from src.pipeline import models


def test_letterbox_preprocess_preserves_scale_padding_and_rgb_tensor():
    image = np.zeros((2, 4, 3), dtype=np.uint8)
    image[:, :, 0] = 10
    image[:, :, 2] = 30
    with patch.object(models.cv2, "imread", return_value=image), patch.object(
        models.cv2, "resize", side_effect=lambda image, size, **kwargs: np.broadcast_to(image[0, 0], (size[1], size[0], 3)).copy()
    ) as resize, patch.object(
        models.cv2, "copyMakeBorder", side_effect=lambda image, top, bottom, left, right, *args, **kwargs: np.pad(image, ((top, bottom), (left, right), (0, 0)), constant_values=114)
    ) as pad:
        tensor, top, bottom, left, right, scale, width, height = models.letterbox_preprocess("frame.png", 8)

    assert resize.call_args.args[1] == (8, 4)
    assert pad.call_args.args[1:5] == (2, 2, 0, 0)
    assert (top, bottom, left, right, scale, width, height) == (2, 2, 0, 0, 2.0, 4, 2)
    assert tensor.shape == (1, 3, 8, 8)
    assert tensor[0, 0, 2, 0].item() == pytest.approx(30 / 255)
    assert tensor[0, 2, 2, 0].item() == pytest.approx(10 / 255)


def test_letterbox_preprocess_reports_unreadable_and_zero_size_images():
    with patch.object(models.cv2, "imread", return_value=None):
        with pytest.raises(FileNotFoundError, match="Cannot read image: missing.png"):
            models.letterbox_preprocess("missing.png", 8)
    with patch.object(models.cv2, "imread", return_value=np.zeros((0, 2, 3), dtype=np.uint8)):
        with pytest.raises(ValueError, match="zero dimension"):
            models.letterbox_preprocess("empty.png", 8)


def test_adjust_boxes_to_original_unpads_scales_and_clips():
    predictions = torch.tensor([[-4.0, 3.0, 30.0, 30.0, 0.9, 2.0]])
    boxes = models.adjust_boxes_to_original(predictions, left=2, top=1, r=2.0, w0=8, h0=6)
    assert boxes.tolist() == [[0.0, 1.0, 7.0, 5.0]]
    assert predictions[0, 0].item() == -4.0


def test_build_inference_result_keeps_nms_options_and_dict_name_fallback():
    captured = {}

    def non_max_suppression(raw, **kwargs):
        captured.update(kwargs)
        return [torch.tensor([[2.0, 4.0, 8.0, 10.0, 0.75, 7.0]])]

    ops = types.ModuleType("ultralytics.utils.ops")
    ops.non_max_suppression = non_max_suppression
    utils = types.ModuleType("ultralytics.utils")
    utils.__path__ = []
    ultralytics = types.ModuleType("ultralytics")
    ultralytics.__path__ = []
    with patch.dict(sys.modules, {"ultralytics": ultralytics, "ultralytics.utils": utils, "ultralytics.utils.ops": ops}), patch.object(
        models, "adjust_boxes_to_original", return_value=torch.tensor([[1.0, 2.0, 3.0, 4.0]])
    ):
        result = models.build_inference_result(
            image="image.png",
            raw_predictions=object(),
            preprocess_info=(1, 2, 3, 4, 0.5, 100, 50),
            confidence=0.4,
            iou=0.6,
            names={0: "known"},
            model_name="detector",
        )

    assert captured == {"conf_thres": 0.4, "iou_thres": 0.6, "max_det": 300, "multi_label": True}
    assert result.model_name == "detector"
    assert result.image_path == "image.png"
    assert result.latency_ms == 0.0
    assert result.detections[0].to_dict() == {
        "class_id": 7,
        "class_name": "class_7",
        "confidence": 0.75,
        "bbox": [1.0, 2.0, 3.0, 4.0],
    }


def test_build_inference_result_caps_confidence_and_supports_name_lists():
    calls = []
    ops = types.ModuleType("ultralytics.utils.ops")
    ops.non_max_suppression = lambda raw, **kwargs: calls.append(kwargs) or [torch.empty((0, 6))]
    utils = types.ModuleType("ultralytics.utils")
    utils.__path__ = []
    ultralytics = types.ModuleType("ultralytics")
    ultralytics.__path__ = []
    with patch.dict(sys.modules, {"ultralytics": ultralytics, "ultralytics.utils": utils, "ultralytics.utils.ops": ops}):
        result = models.build_inference_result(
            image="x", raw_predictions=None, preprocess_info=(0, 0, 0, 0, 1, 1, 1),
            confidence=0.8, iou=0.5, names=["can"], model_name="m", confidence_limit=0.25,
        )
    assert calls[0]["conf_thres"] == 0.25
    assert result.detections == []


def test_yolo_adapter_times_backend_call_and_uses_default_thresholds():
    adapter = models.YOLOAdapter("model.pt", "detector")
    adapter._loaded = True
    adapter._backend = MagicMock(device=torch.device("cpu"))
    adapter._names = {0: "can"}
    adapter._imgsz = 8
    expected_result = models.InferenceResult([], 0.0, "detector", "frame.png")
    with patch.object(models, "letterbox_preprocess", return_value=(torch.zeros((1, 3, 8, 8)), 0, 0, 0, 0, 1.0, 8, 8)), patch.object(
        models, "build_inference_result", return_value=expected_result
    ) as build_result, patch.object(models.time, "perf_counter", side_effect=(10.0, 10.025)):
        result = adapter.predict("frame.png")

    assert result is expected_result
    assert result.latency_ms == pytest.approx(25.0)
    assert build_result.call_args.kwargs["confidence"] == models.DEFAULT_CONF
    assert build_result.call_args.kwargs["iou"] == models.DEFAULT_IOU
    adapter._backend.assert_called_once()


def test_yolo_adapter_rejects_invalid_threshold_before_loading():
    adapter = models.YOLOAdapter("missing.pt", "detector")
    with pytest.raises(ValueError, match=r"conf must be in \[0, 1\]"):
        adapter.predict("frame.png", conf=-0.1)
    assert adapter._loaded is False


def test_model_registry_discovers_sorted_files_and_descriptor_metadata(tmp_path):
    (tmp_path / "z.pt").touch()
    (tmp_path / "a.onnx").touch()
    (tmp_path / "example.yaml").write_text("name: ignored\ntype: yolo_pt\nmodel_file: missing.pt\n", encoding="utf-8")
    (tmp_path / "third.pt").touch()
    (tmp_path / "third.yaml").write_text(
        "name: third\nmodel_type: third_party\nmodel_file: third.pt\ndisplay_name: Third Model\nclass_names: [can]\n",
        encoding="utf-8",
    )
    registry = models.ModelRegistry(tmp_path)

    assert registry.discover() == 3
    assert list(registry._models) == ["third.pt", "a.onnx", "z.pt"]
    assert registry.get_model("folder/third.pt")["label"] == "Third Model"
    assert registry.get_model("third.pt")["class_names"] == ["can"]
    assert [item["name"] for item in registry.list_models()] == ["third.pt", "a.onnx", "z.pt"]


def test_model_registry_rejects_descriptor_paths_outside_detection_dir(tmp_path):
    outside = tmp_path.parent / "outside.pt"
    outside.touch()
    (tmp_path / "escape.yaml").write_text(
        f"name: escape\ntype: yolo_pt\nmodel_file: {outside}\n", encoding="utf-8"
    )
    registry = models.ModelRegistry(tmp_path)
    assert registry._load_descriptor(tmp_path / "escape.yaml") is False
    assert registry._models == {}


def test_model_registry_missing_names_and_adapter_loading_contract(tmp_path):
    registry = models.ModelRegistry(tmp_path)
    with pytest.raises(KeyError, match="Unknown model 'missing.pt'"):
        registry.get_model("missing.pt")
    model_path = tmp_path / "model.pt"
    model_path.touch()
    registry._models["model.pt"] = {"path": model_path, "model_type": "yolo_pt", "label": "model", "is_third_party": False}
    adapter = MagicMock()
    adapter._loaded = True
    with patch("src.pipeline.registry.get_model_adapters", return_value={"yolo_pt": types.SimpleNamespace(adapter_class=lambda **kwargs: adapter)}):
        first = registry.load_model("model.pt")
        second = registry.load_model("model.pt")
    assert first is second is adapter
    adapter.load.assert_called_once_with()


def test_third_party_unsupported_suffix_returns_empty_result_and_remembers_failure(tmp_path):
    path = tmp_path / "model.bin"
    adapter = models.ThirdPartyAdapter(path, "custom")
    result = adapter.predict("frame.png")
    assert result.detections == []
    assert result.latency_ms == 0.0
    assert result.model_name == "custom"
    assert result.image_path == "frame.png"
    assert adapter._load_failed is True
    assert adapter._loaded is False


def test_inference_engine_tflite_uses_native_size_int8_default_and_predict_routing(tmp_path):
    model_path = tmp_path / "model_int8.tflite"
    model_path.touch()
    model = MagicMock()
    model.predict.return_value = ["prediction"]
    with patch("src.inference_engine.DETECTION_DIR", tmp_path), patch("src.inference_engine.YOLO", return_value=model), patch(
        "src.inference_engine.USBCamera"
    ) as camera, patch("src.inference_engine.get_tflite_imgsz", return_value=320):
        from src.inference_engine import InferenceEngine

        inference = InferenceEngine("model_int8.tflite")
        result = inference._infer(np.zeros((2, 2, 3), dtype=np.uint8))
        inference._cleanup()
    assert inference.img_size == 320
    assert inference.conf_threshold == 0.25
    assert inference.enable_tracking is False
    assert result == ["prediction"]
    model.predict.assert_called_once()
    model.track.assert_not_called()
    camera.return_value.release.assert_called_once()
