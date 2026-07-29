"""Helper functions for working with numa nodes."""

from typing import Dict, List, Optional

from rykit.cmd import run_command_read_stdout


def show_numactl() -> Dict[str, List[str]]:
    """Show results of numactl command."""
    res = {}
    for line in run_command_read_stdout("numactl --show").strip().split("\n"):
        field, val = line.split(":", 2)
        val_list = val.strip().split(" ")
        res[field] = val_list
    return res


def get_numactl_bound_cpu() -> Optional[int]:
    """Get the CPU NUMA node bound to the process, if exactly one is bound."""
    cpu_nodes = show_numactl().get("cpubind", [])
    if len(cpu_nodes) != 1:
        return None
    return int(cpu_nodes[0])


def get_numactl_bound_mem() -> Optional[int]:
    """Get the memory NUMA node bound to the process, if exactly one is bound."""
    mem_nodes = show_numactl().get("membind", [])
    if len(mem_nodes) != 1:
        return None
    return int(mem_nodes[0])


def assert_numactl_bind(cpu_node: int, mem_node: int) -> None:
    """Assert that the process is bound to the expected NUMA nodes.

    Args:
        cpu_node (int): Expected CPU NUMA node.
        mem_node (int): Expected memory NUMA node.

    Raises:
        AssertionError: If the CPU or memory binding does not match.
    """
    bound_cpu_node = get_numactl_bound_cpu()
    bound_mem_node = get_numactl_bound_mem()
    assert bound_cpu_node == cpu_node, (
        f"expected CPU NUMA node {cpu_node}, got {bound_cpu_node}"
    )
    assert bound_mem_node == mem_node, (
        f"expected memory NUMA node {mem_node}, got {bound_mem_node}"
    )
