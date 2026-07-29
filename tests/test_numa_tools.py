import pytest

from rykit import numa_tools
from tests.helpers import stub_run_command_read_stdout


def test_show_numactl(monkeypatch):
    stub_run_command_read_stdout(
        monkeypatch,
        numa_tools,
        {
            "numactl --show": (
                "policy: bind\ncpubind: 1\nnodebind: 1\nmembind: 3\n"
            )
        },
    )

    assert numa_tools.show_numactl() == {
        "policy": ["bind"],
        "cpubind": ["1"],
        "nodebind": ["1"],
        "membind": ["3"],
    }


def test_assert_numactl_bind(monkeypatch):
    monkeypatch.setattr(
        numa_tools,
        "show_numactl",
        lambda: {"cpubind": ["1"], "membind": ["3"]},
    )

    numa_tools.assert_numactl_bind(1, 3)


def test_assert_numactl_bind_cpu_mismatch(monkeypatch):
    monkeypatch.setattr(
        numa_tools,
        "show_numactl",
        lambda: {"cpubind": ["0"], "membind": ["3"]},
    )

    with pytest.raises(AssertionError, match="expected CPU NUMA node 1"):
        numa_tools.assert_numactl_bind(1, 3)


def test_assert_numactl_bind_mem_mismatch(monkeypatch):
    monkeypatch.setattr(
        numa_tools,
        "show_numactl",
        lambda: {"cpubind": ["1"], "membind": ["0"]},
    )

    with pytest.raises(AssertionError, match="expected memory NUMA node 3"):
        numa_tools.assert_numactl_bind(1, 3)
