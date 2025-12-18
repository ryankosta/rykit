from typing import Dict,List,Optional
from rykit.cmd import run_command_read_stdout
import shutil
def lscpu() -> Dict[str, str]:
    """
    Parse the output of `lscpu` into a dictionary.

    Returns:
        Dict[str, str]: Mapping of lscpu fields to their values.
    """
    res = {}
    for line in run_command_read_stdout("lscpu").split("\n"):
        if ":" not in line:
            continue
        segments = [x.strip() for x in line.split(":")]
        res[segments[0]] = segments[1]
    return res


def normalize(x: str, units: Dict[str, int], default: str):
    """
    Normalize a string containing a number and a unit into the default unit.

    Args:
        x (str): Input string, e.g., "64KB".
        units (Dict[str, int]): Dictionary mapping unit strings to their scale factors.
        default (str): The default unit to normalize to.

    Returns:
        int: The value converted to the default unit.

    Raises:
        AssertionError: If the default unit is not in the units dictionary.
        ValueError: If the input string does not contain a recognized unit.
    """
    assert default in units
    units_longest_first = sorted(list(units.keys()), key=len, reverse=True)
    for unit in units_longest_first:
        if unit in x:
            val = int(x.split(unit)[0].strip())
            scale_factor = units[unit] / units[default]
            return int(val * scale_factor)
    raise ValueError(
        f"{x} did not contain a valid unit out of choices {units_longest_first}"
    )
def numactl_pin(node:int) -> str:
    if shutil.which('numactl') is None:
        raise RuntimeError("numactl should be installed")
    return f"numactl --cpunodebind={node} --membind={node} "
def numactl_pin_mem(node:int) -> str:
    if shutil.which('numactl') is None:
        raise RuntimeError("numactl should be installed")
    return f"numactl --membind={node} "


def numactl_pin_cpu(cpus:List[int],mem_node:Optional[int]) -> str:
    assert len(cpus) > 0
    if mem_node is None:
        mem_node = get_socket_for_cpu(cpus[0]) 
    cpustr = ",".join([str(x) for x in cpus]) 
    return f"numactl --membind={mem_node} --physcpubind={cpustr} " 


def lscpu_cache() -> Dict[str, Dict[str, str]]:
    """
    Parse `lscpu -C` output to get per-CPU cache and CPU info.

    Returns:
        Dict[str, Dict[str, str]]: Mapping from CPU ID to its properties.
    """
    rows = run_command_read_stdout("lscpu -C").split("\n")
    col_names = rows[0].split()
    res = {}
    for row in rows[1:]:
        cells = row.split()
        if len(cells) < 1:
            continue
        key = cells[0]
        val = {k: v for k, v in zip(col_names[1:], cells[1:])}
        res[key] = val
    return res


def parse_range_list(s: str) -> List[int]:
    """
    Convert a string representing ranges into a list of integers.

    Args:
        s (str): Range string, e.g., "0-3,5,7-8".

    Returns:
        List[int]: Expanded list of integers from the range string.
    """
    result = []
    for part in s.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return result

def get_socket_ct():
    info = lscpu()
    return int(info["NUMA node(s)"])

def get_socket(skt: int) -> List[int]:
    """
    Get the list of CPU IDs belonging to a specific NUMA socket.

    Args:
        skt (int): NUMA socket index (0-based).

    Returns:
        List[int]: List of CPU IDs for the socket.

    Raises:
        AssertionError: If the socket index is invalid.
    """
    assert skt >= 0
    assert skt < get_socket_ct()
    info = lscpu()
    nodestr = info[f"NUMA node{skt} CPU(s)"]

    return parse_range_list(nodestr)
def get_socket_for_cpu(cpu:int):
    for socket in range(get_socket_ct()):
        if cpu in get_socket(socket):
            return socket
    raise ValueError(f"{cpu} not in any socket")
