"""Tests for CLI argument parsing, command registry, defaults, and validation."""

import argparse
import io
import pathlib
import sys
import tempfile

import pytest

import src.cli  # noqa: F401

_MOCK_KEYS = [
    "ultralytics",
    "ultralytics.nn",
    "ultralytics.nn.autobackend",
    "ultralytics.utils",
    "ultralytics.utils.ops",
    "ultralytics.utils.torch_utils",
    "torchvision",
    "tensorflow",
    "tensorflow.keras",
    "uvicorn",
    "psutil",
    "torch",
    "cv2",
]


def _build_parser(add_args_func, extra_subs_for=None):
    """Create an argparse instance with the given add_args registered."""
    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers(dest="command")
    sub = subs.add_parser("test_cmd")
    if extra_subs_for:
        inner = sub.add_subparsers(dest=extra_subs_for)
        return parent, sub, inner
    if add_args_func:
        add_args_func(sub)
    return parent, sub, None


def _parse(add_args_func, cmd_args, extra_subs_for=None):
    parent, _, _ = _build_parser(add_args_func, extra_subs_for=extra_subs_for)
    return parent.parse_args(["test_cmd"] + cmd_args)


EXPECTED_COMMANDS = {
    "train",
    "export",
    "eval-yolo",
    "live",
    "download",
    "merge",
    "datasets",
    "validate",
    "doctor",
    "config",
    "models",
    "experiments",
    "benchmark",
    "generate",
    "dashboard",
    "wizard",
}


def test_all_commands_registered():
    from src.pipeline.registry import get_commands

    cmds = get_commands()
    found = set(cmds.keys())
    missing = EXPECTED_COMMANDS - found
    assert not missing, f"Missing commands: {missing}"
    extra = found - EXPECTED_COMMANDS
    if extra:
        print(f"  Info: Additional commands found: {extra}")
    assert len(found) >= 16, f"Expected >= 16 commands, got {len(found)}"


def test_commands_have_help_text():
    from src.pipeline.registry import get_commands

    for name, entry in get_commands().items():
        assert entry.help_text, f"Command '{name}' has empty help text"
        assert isinstance(entry.help_text, str), f"Command '{name}' help is not str"
        assert len(entry.help_text) > 3, f"Command '{name}' help too short: {entry.help_text!r}"
        assert callable(entry.fn), f"Command '{name}' fn is not callable"


def test_train_parsing():
    from src.cli.train import _add_train_args

    args = _parse(_add_train_args, ["--epochs", "50", "--batch-size", "16", "--task", "classifier"])
    assert args.epochs == 50
    assert args.batch_size == 16
    assert args.task == "classifier"
    assert args.dry_run is False
    assert args.auto is False
    assert args.base_model == "mobilenetv2"


def test_export_parsing():
    from src.cli.train import _add_export_args

    args = _parse(_add_export_args, ["--model", "test.pt", "--dry-run", "--formats", "onnx", "tflite_fp32"])
    assert args.model == "test.pt"
    assert args.dry_run is True
    assert args.formats == ["onnx", "tflite_fp32"]


def test_live_parsing_defaults():
    from src.cli.inference import _add_live_args

    args = _parse(_add_live_args, ["--model", "mira_exp014_int8.tflite", "--conf", "0.7", "--camera", "1"])
    assert args.model == "mira_exp014_int8.tflite"
    assert args.conf == 0.7
    assert args.camera == 1
    assert args.reject == 0.25
    assert args.target_latency == 1000


def test_merge_parsing():
    from src.cli.data import _add_merge_args

    args = _parse(_add_merge_args, ["--sources", "taco", "trashnet", "--output", "datasets/merged", "--dry-run"])
    assert args.sources == ["taco", "trashnet"]
    assert args.output == "datasets/merged"
    assert args.dry_run is True


def test_benchmark_parsing():
    from src.cli.system import _add_benchmark_args

    args = _parse(
        _add_benchmark_args,
        [
            "--models",
            "mira_exp014.pt",
            "mira_exp016.pt",
            "--dataset",
            "datasets/ds.yaml",
            "--max-images",
            "50",
            "--output",
            "report.json",
        ],
    )
    assert args.models == ["mira_exp014.pt", "mira_exp016.pt"]
    assert args.max_images == 50
    assert args.dataset == "datasets/ds.yaml"
    assert args.output == "report.json"
    assert args.conf == 0.5  # DEFAULT_CONF from mira.yaml


def test_dashboard_parsing():
    from src.cli.dashboard import _add_dashboard_args

    args = _parse(_add_dashboard_args, ["--host", "0.0.0.0", "--port", "9000"])
    assert args.host == "0.0.0.0"
    assert args.port == 9000

    args_default = _parse(_add_dashboard_args, [])
    assert args_default.host == "127.0.0.1"
    assert args_default.port == 8000


def test_download_parsing():
    from src.cli.inference import _add_download_args

    args = _parse(_add_download_args, ["--list"])
    assert args.list_only is True
    assert args.all is False

    args2 = _parse(_add_download_args, ["mira_exp014.pt"])
    assert args2.model_name == "mira_exp014.pt"


def test_config_validate_flag():
    from src.cli.system import _add_config_args

    args = _parse(_add_config_args, ["--validate"])
    assert args.validate is True

    args2 = _parse(_add_config_args, [])
    assert args2.validate is False


def test_wizard_parsing():
    from src.cli.wizard import _add_wizard_args

    args = _parse(_add_wizard_args, ["--auto-start"])
    assert args.auto_start is True


def test_generate_kaggle_parsing():
    from src.cli.generate import _add_generate_args

    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers(dest="command")
    sub = subs.add_parser("generate")
    _add_generate_args(sub)
    args = parent.parse_args(["generate", "kaggle", "--config", "experiments/exp001.yaml", "--output", "out.ipynb"])
    assert args.target == "kaggle"
    assert args.config == "experiments/exp001.yaml"
    assert args.output == "out.ipynb"


def test_merge_missing_required():
    from src.cli.data import _add_merge_args

    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers(dest="command")
    sub = subs.add_parser("merge")
    _add_merge_args(sub)
    with pytest.raises(SystemExit):
        parent.parse_args(["merge"])


def test_export_missing_model():
    from src.cli.train import _add_export_args

    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers(dest="command")
    sub = subs.add_parser("export")
    _add_export_args(sub)
    with pytest.raises(SystemExit):
        parent.parse_args(["export"])


def test_benchmark_missing_models():
    from src.cli.system import _add_benchmark_args

    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers(dest="command")
    sub = subs.add_parser("benchmark")
    _add_benchmark_args(sub)
    with pytest.raises(SystemExit):
        parent.parse_args(["benchmark"])


def test_validate_missing_dataset():
    from src.cli.data import _add_validate_args

    parent = argparse.ArgumentParser()
    subs = parent.add_subparsers(dest="command")
    sub = subs.add_parser("validate")
    _add_validate_args(sub)
    with pytest.raises(SystemExit):
        parent.parse_args(["validate"])


def test_resolve_safe_path_blocks_traversal():
    from src.config import resolve_safe_path
    from src.exceptions import ConfigError

    with tempfile.TemporaryDirectory() as tmpdir:
        base = pathlib.Path(tmpdir)
        subdir = base / "sub"
        subdir.mkdir()

        # Valid path stays inside base
        resolved = resolve_safe_path("sub/file.txt", base_dir=base)
        assert resolved == subdir / "file.txt"

        # Traversal blocked
        with pytest.raises(ConfigError, match="Path traversal"):
            resolve_safe_path("../outside/file.txt", base_dir=base)

        with pytest.raises(ConfigError):
            resolve_safe_path("..", base_dir=base)


def test_trainconfig_yaml_not_found():
    from src.pipeline.strategies import TrainConfig
    from src.exceptions import ConfigError

    with pytest.raises(ConfigError, match="Config file not found"):
        TrainConfig.from_yaml("nonexistent_abcdef_test.yaml")


def test_trainconfig_invalid_yaml():
    from src.pipeline.strategies import TrainConfig
    from src.exceptions import ConfigError

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("broken: [ : yaml } invalid\n")
        bad_path = f.name

    try:
        with pytest.raises(ConfigError, match="parse"):
            TrainConfig.from_yaml(bad_path)
    finally:
        pathlib.Path(bad_path).unlink(missing_ok=True)


def test_trainconfig_minimal_yaml_uses_defaults():
    from src.pipeline.strategies import TrainConfig

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("name: minimal_test\nmodel: custom.pt\nepochs: 5\n")
        minimal = f.name

    try:
        config = TrainConfig.from_yaml(minimal)
        assert config.name == "minimal_test"
        assert config.model == "custom.pt"
        assert config.epochs == 5
        # Other fields use defaults from PROJECT_CONFIG (mira.yaml)
        assert config.batch_size == 32
        assert config.imgsz == 640
    finally:
        pathlib.Path(minimal).unlink(missing_ok=True)


def test_mira_yaml_defaults_in_config_module():
    from src.config import DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_IOU, REJECT_THRESHOLD

    assert DEFAULT_CONF == 0.5
    assert DEFAULT_IOU == 0.45
    assert DEFAULT_IMGSZ == 640
    assert REJECT_THRESHOLD == 0.55


def test_trainconfig_defaults_from_project_config():
    from src.pipeline.strategies import TrainConfig
    from src.config import PROJECT_CONFIG

    training = PROJECT_CONFIG["training"]
    c = TrainConfig()
    assert c.model == training["default_model"]
    assert c.epochs == training["default_epochs"]
    assert c.batch_size == training["default_batch_size"]
    assert c.imgsz == training["default_imgsz"]
    assert c.lr0 == training["default_lr"]


def test_project_config_validate_returns_empty_for_valid():
    from src.config import validate_config

    assert validate_config() == []


def test_project_config_validate_detects_errors():
    from src.config import _validate_project_config

    errors = _validate_project_config({"classes": {}, "training": {}, "inference": {}})
    assert len(errors) > 0
    assert any("classes.names" in e for e in errors)

    # Bad training values
    bad = {
        "classes": {"names": ["a", "b", "c"], "count": 3},
        "training": {"default_epochs": 0, "default_lr": -1},
        "inference": {"reject_threshold": 2.0},
    }
    errors2 = _validate_project_config(bad)
    assert len(errors2) >= 3


def test_help_flag_per_command():
    from src.pipeline.registry import get_commands

    for name, entry in get_commands().items():
        parent = argparse.ArgumentParser()
        subs = parent.add_subparsers(dest="command")
        sub = subs.add_parser(name, help=entry.help_text)
        if entry.add_args:
            entry.add_args(sub)

        old_stdout = sys.stdout
        try:
            sys.stdout = io.StringIO()
            with pytest.raises(SystemExit):
                parent.parse_args([name, "--help"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert output, f"Command '{name}' produced no help output"
        assert (
            "usage" in output.lower()
            or name.lower() in output.lower()
            or "positional arguments" in output.lower()
            or "options" in output.lower()
        ), f"Help for '{name}' missing expected content"


def test_version_flag():
    from src.version import __version__

    parent = argparse.ArgumentParser()
    parent.add_argument("--version", action="version", version=f"MIRA {__version__}")

    with pytest.raises(SystemExit):
        parent.parse_args(["--version"])

    assert __version__ == "1.0.2"


def test_doctor_healthy(capsys):
    from src.cli.system import cmd_doctor

    cmd_doctor(argparse.Namespace())
    out = capsys.readouterr().out
    assert "MIRA Doctor" in out
    assert "HEALTHY" in out


def test_config_validate_command(capsys):
    from src.cli.system import cmd_config

    cmd_config(argparse.Namespace(validate=True))
    out = capsys.readouterr().out
    assert "mira.yaml is valid" in out
    assert "Classes:" in out


def test_models_command(capsys):
    from src.cli.system import cmd_models

    cmd_models(argparse.Namespace())
    out = capsys.readouterr().out
    assert isinstance(out, str)


def test_experiments_command(capsys):
    from src.cli.system import cmd_experiments

    cmd_experiments(argparse.Namespace())
    out = capsys.readouterr().out
    assert isinstance(out, str)


def test_datasets_command(capsys):
    from src.cli.data import cmd_datasets

    cmd_datasets(argparse.Namespace())
    out = capsys.readouterr().out
    assert isinstance(out, str)


def test_config_display_command(capsys):
    from src.cli.system import cmd_config

    cmd_config(argparse.Namespace(validate=False))
    out = capsys.readouterr().out
    assert "mira.yaml" in out


def test_download_list_command(capsys):
    from src.cli.inference import cmd_download

    cmd_download(argparse.Namespace(list_only=True, all=False, model_name=None))
    out = capsys.readouterr().out
    assert "Models bundled with mira-ai" in out
    assert "mira_exp014.pt" in out


def test_train_name_validation():
    from src.cli.train import _validate_name

    assert _validate_name("exp_001") == "exp_001"
    assert _validate_name("test-run") == "test-run"

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_name("has spaces")

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_name("path/traversal")
