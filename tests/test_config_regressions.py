from types import SimpleNamespace
import pytest
from src import config
from src.exceptions import CameraError,ConfigError

def test_empty_yaml_is_a_config_error(tmp_path, monkeypatch):
    (tmp_path / "mira.yaml").write_text("", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML mapping"):
        config._load_project_config(tmp_path)


def test_non_mapping_yaml_is_a_config_error(tmp_path):
    (tmp_path / "mira.yaml").write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="YAML mapping"):
        config._load_project_config(tmp_path)


def test_safe_path_still_rejects_traversal(tmp_path):
    with pytest.raises(ConfigError, match="Path traversal"):
        config.resolve_safe_path("../outside.txt", tmp_path)


def test_camera_property_failure_is_reported(monkeypatch):
    class Capture:
        def isOpened(self):
            return True

        def set(self, property_id, value):
            return property_id != 7


    cv2 = SimpleNamespace(
        CAP_PROP_FOURCC=1, CAP_PROP_FRAME_WIDTH=2, CAP_PROP_FRAME_HEIGHT=3,
        CAP_PROP_FPS=4, CAP_PROP_BUFFERSIZE=5, CAP_PROP_AUTOFOCUS=6,
        CAP_PROP_AUTO_EXPOSURE=7, VideoWriter_fourcc=lambda *args: 0,
    )
    monkeypatch.setitem(__import__("sys").modules, "cv2", cv2)
    with pytest.raises(CameraError, match="AUTO_EXPOSURE"):
        config.setup_camera_properties(Capture(), 640, 480)

from types import SimpleNamespace


def test_camera_properties_keep_requested_values_in_order(monkeypatch):
    from src import config

    cv2 = SimpleNamespace(
        CAP_PROP_FOURCC=1,
        CAP_PROP_FRAME_WIDTH=2,
        CAP_PROP_FRAME_HEIGHT=3,
        CAP_PROP_FPS=4,
        CAP_PROP_BUFFERSIZE=5,
        CAP_PROP_AUTOFOCUS=6,
        CAP_PROP_AUTO_EXPOSURE=7,
        VideoWriter_fourcc=lambda *values: "fourcc",
    )
    monkeypatch.setitem(__import__("sys").modules, "cv2", cv2)

    class Capture:
        values = []

        def isOpened(self):
            return True

        def set(self, property_id, value):
            self.values.append((property_id, value))
            return True

    capture = Capture()
    config.setup_camera_properties(capture, 1280, 720, fps=25, autofocus=True, auto_exposure=False)

    assert capture.values == [
        (1, "fourcc"),
        (2, 1280),
        (3, 720),
        (4, 25),
        (5, 1),
        (6, 1),
        (7, 0),
    ]
