"""Helper functions for working with numa nodes."""

from typing import Dict, List

from rykit.cmd import run_command_read_stdout


def show_numactl() -> Dict[str, List[str]]:
    """Show results of numactl command."""
    res = {}
    for line in run_command_read_stdout("numactl --show").strip().split("\n"):
        field, val = line.split(":", 2)
        val_list = val.strip().split(" ")
        res[field] = val_list
    return res


def assert_numactl_bind(cpu_node: int, mem_node: int) -> None:
    """Assert that the process is bound to the expected NUMA nodes.

    Args:
        cpu_node (int): Expected CPU NUMA node.
        mem_node (int): Expected memory NUMA node.

    Raises:
        AssertionError: If the CPU or memory binding does not match.
    """
    bindings = show_numactl()
    assert bindings["cpubind"] == [str(cpu_node)], (
        f"expected CPU NUMA node {cpu_node}, got {bindings['cpubind']}"
    )
    assert bindings["membind"] == [str(mem_node)], (
        f"expected memory NUMA node {mem_node}, got {bindings['membind']}"
    )
