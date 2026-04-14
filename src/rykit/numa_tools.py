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
