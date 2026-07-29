from types import ModuleType
from typing import Callable, Dict

import pytest


def _stub_run_command(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    method: str,
    outputs: Dict[str, str],
) -> Callable[[str], str]:
    def run_command(cmd: str) -> str:
        assert cmd in outputs, f"unexpected command: {cmd}"
        return outputs[cmd]

    monkeypatch.setattr(module, method, run_command)
    return run_command


def stub_run_command_read_stdout(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    outputs: Dict[str, str],
) -> Callable[[str], str]:
    return _stub_run_command(monkeypatch, module, "run_command_read_stdout", outputs)


def stub_run_command_read_stderr(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    outputs: Dict[str, str],
) -> Callable[[str], str]:
    return _stub_run_command(monkeypatch, module, "run_command_read_stderr", outputs)
