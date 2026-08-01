"""Tests for MIRA shared configuration."""

import pathlib
from unittest.mock import MagicMock


def test_root_dir_is_pathlib_path():
    from src.config import ROOT_DIR

    assert isinstance(ROOT_DIR, pathlib.Path)


def test_class_names_has_5_entries():
    from src.config import CLASS_NAMES

    assert CLASS_NAMES == ["glass", "metal", "paper", "plastic", "trash"]
    assert len(CLASS_NAMES) == 5


def test_get_tflite_imgsz_reads_tensor_shape():
    import sys
    from src.config import get_tflite_imgsz

    mock_interpreter = MagicMock()
    mock_interpreter.get_input_details.return_value = [{"shape": [1, 320, 320, 3]}]

    mock_mod = MagicMock()
    mock_mod.Interpreter.return_value = mock_interpreter

    sys.modules["ai_edge_litert.interpreter"] = mock_mod
    try:
        result = get_tflite_imgsz(pathlib.Path("/fake/model.tflite"))
    finally:
        del sys.modules["ai_edge_litert.interpreter"]

    assert result == 320


def test_get_tflite_imgsz_max_of_dims():
    import sys
    from src.config import get_tflite_imgsz

    mock_interpreter = MagicMock()
    mock_interpreter.get_input_details.return_value = [{"shape": [1, 3, 224, 224]}]

    mock_mod = MagicMock()
    mock_mod.Interpreter.return_value = mock_interpreter

    sys.modules["ai_edge_litert.interpreter"] = mock_mod
    try:
        result = get_tflite_imgsz(pathlib.Path("/fake/model.tflite"))
    finally:
        del sys.modules["ai_edge_litert.interpreter"]

    assert result == 224
