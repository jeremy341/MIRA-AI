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