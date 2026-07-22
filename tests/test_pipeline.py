"""Tests for MIRA research pipeline modules."""

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

_project_root = str(Path(__file__).resolve().parent.parent)
_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


# ── Config tests ─────────────────────────────────────────────────────


def test_mira_yaml_exists():
    assert Path(_project_root, "mira.yaml").is_file()


def test_config_loads_classes():
    from src.config import CLASS_NAMES, NUM_CLASSES

    assert CLASS_NAMES == ["glass", "metal", "paper", "plastic", "trash"]
    assert NUM_CLASSES == 5


def test_config_loads_thresholds():
    from src.config import REJECT_THRESHOLD

    assert isinstance(REJECT_THRESHOLD, float)
    assert 0 < REJECT_THRESHOLD < 1


def test_project_config_returns_dict():
    from src.config import get_project_config

    cfg = get_project_config()
    assert isinstance(cfg, dict) or hasattr(cfg, "get")
    assert "classes" in cfg
    assert "training" in cfg
    assert "inference" in cfg


# ── Registry tests ───────────────────────────────────────────────────


def test_register_command():
    from src.pipeline.registry import get_commands, register_command

    @register_command("test_cmd_pytest", "A test command")
    def _dummy(args):
        pass

    commands = get_commands()
    assert "test_cmd_pytest" in commands
    assert commands["test_cmd_pytest"].help_text == "A test command"

    # Clean up to avoid polluting global state
    _cmds = get_commands()
    _cmds.pop("test_cmd_pytest", None)


# ── Dataset Registry tests ──────────────────────────────────────────


def test_discover_loads_yaml_files():
    from src.pipeline.dataset import DatasetRegistry

    reg = DatasetRegistry()
    count = reg.discover()
    assert count >= 3


def test_list_sources_returns_dicts():
    from src.pipeline.dataset import DatasetRegistry

    reg = DatasetRegistry()
    reg.discover()
    sources = reg.list_sources()
    assert len(sources) >= 3
    for s in sources:
        assert "key" in s
        assert "name" in s
        assert "exists" in s
        assert isinstance(s["exists"], bool)


def test_get_source_by_key():
    from src.pipeline.dataset import DatasetRegistry

    reg = DatasetRegistry()
    reg.discover()
    src = reg.get_source("taco_trashnet")
    assert src.key == "taco_trashnet"
    assert src.name == "TACO + TrashNet"


def test_get_source_unknown_raises():
    from src.pipeline.dataset import DatasetRegistry

    reg = DatasetRegistry()
    reg.discover()
    with pytest.raises(KeyError, match="nonexistent"):
        reg.get_source("nonexistent")


def test_yaml_descriptors_valid():
    registry_dir = Path(_project_root) / "datasets" / "registry"
    yaml_files = sorted(registry_dir.glob("*.yaml"))
    assert len(yaml_files) >= 3
    for yf in yaml_files:
        data = yaml.safe_load(yf.read_text())
        assert "key" in data, f"{yf.name} missing 'key'"
        assert "name" in data, f"{yf.name} missing 'name'"
        assert "source_format" in data, f"{yf.name} missing 'source_format'"


# ── Model Registry tests ────────────────────────────────────────────


def test_discover_finds_models():
    from src.pipeline.models import ModelRegistry

    reg = ModelRegistry()
    count = reg.discover()
    assert isinstance(count, int)
    assert count >= 0


def test_detection_dataclass():
    from src.pipeline.models import Detection

    det = Detection(class_id=0, class_name="glass", confidence=0.95, bbox=(10, 20, 100, 200))
    d = det.to_dict()
    assert d["class_id"] == 0
    assert d["class_name"] == "glass"
    assert d["confidence"] == 0.95
    assert d["bbox"] == [10, 20, 100, 200]


def test_third_party_adapter():
    from src.pipeline.models import ThirdPartyAdapter

    with tempfile.NamedTemporaryFile(suffix=".tflite") as f:
        adapter = ThirdPartyAdapter(path=f.name, name="test_model")
        assert adapter.name == "test_model"
        assert adapter.model_type == "third_party"


# ── Benchmark tests ─────────────────────────────────────────────────


def test_per_class_metrics():
    from src.pipeline.benchmark import PerClassMetrics

    m = PerClassMetrics(tp=10, fp=2, fn=3)
    assert abs(m.precision - 10 / 12) < 1e-9
    assert abs(m.recall - 10 / 13) < 1e-9
    expected_f1 = 2 * (10 / 12) * (10 / 13) / ((10 / 12) + (10 / 13))
    assert abs(m.f1 - expected_f1) < 1e-9


def test_per_class_metrics_zero():
    from src.pipeline.benchmark import PerClassMetrics

    m = PerClassMetrics(tp=0, fp=0, fn=0)
    assert m.precision == 0.0
    assert m.recall == 0.0
    assert m.f1 == 0.0


def test_benchmark_result_serialization():
    from src.pipeline.benchmark import BenchmarkResult, PerClassMetrics

    result = BenchmarkResult(
        model_name="test_model",
        model_path="/fake/model.pt",
        model_type=".pt",
        total_images=100,
        per_class={"glass": PerClassMetrics(tp=80, fp=5, fn=10)},
        overall_f1=0.85,
        overall_precision=0.90,
        overall_recall=0.80,
        avg_latency_ms=42.5,
        total_detections=85,
    )
    d = result.to_dict()
    assert d["model_name"] == "test_model"
    assert d["total_images"] == 100
    assert d["per_class"]["glass"]["tp"] == 80
    assert d["overall_f1"] == 0.85
    assert "errors" in d


def test_comparison_table():
    from src.pipeline.benchmark import BenchmarkResult, ModelBenchmark

    results = [
        BenchmarkResult(model_name="model_a", model_path="/a.pt", model_type=".pt", overall_f1=0.9),
        BenchmarkResult(model_name="model_b", model_path="/b.pt", model_type=".pt", overall_f1=0.7),
    ]
    table = ModelBenchmark.comparison_table(results)
    assert isinstance(table, str)
    assert "model_a" in table
    assert "model_b" in table


# ── TrainConfig tests ───────────────────────────────────────────────


def test_default_config():
    from src.pipeline.strategies import TrainConfig

    cfg = TrainConfig()
    assert cfg.model == "yolo11n.pt"
    assert cfg.epochs == 120
    assert cfg.batch_size == 32
    assert cfg.imgsz == 640
    assert cfg.patience == 30
    assert cfg.amp is True


def test_config_from_yaml():
    from src.pipeline.strategies import TrainConfig

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(
            {
                "name": "test_exp",
                "model": "yolov8n.pt",
                "epochs": 50,
                "batch_size": 16,
                "imgsz": 320,
                "dataset": "datasets/test/data.yaml",
            },
            f,
        )
        f.flush()

        cfg = TrainConfig.from_yaml(f.name)
        assert cfg.name == "test_exp"
        assert cfg.model == "yolov8n.pt"
        assert cfg.epochs == 50
        assert cfg.batch_size == 16
        assert cfg.imgsz == 320

    Path(f.name).unlink()


def test_exception_hierarchy():
    from src.exceptions import MiraError, ConfigError, ModelError, DatasetError, CameraError, PipelineError

    assert issubclass(ConfigError, MiraError)
    assert issubclass(ModelError, MiraError)
    assert issubclass(DatasetError, MiraError)
    assert issubclass(CameraError, MiraError)
    assert issubclass(PipelineError, MiraError)
    assert issubclass(ConfigError, Exception)


def test_config_roundtrip():
    from src.pipeline.strategies import TrainConfig

    original = TrainConfig(name="roundtrip", epochs=25, batch_size=8)
    data = {f.name: getattr(original, f.name) for f in original.__dataclass_fields__.values()}
    loaded = TrainConfig(**data)
    assert loaded.name == original.name
    assert loaded.epochs == original.epochs
    assert loaded.batch_size == original.batch_size
    assert loaded.imgsz == original.imgsz
    assert loaded.model == original.model
