from typing import Dict,List,Optional
from rykit.cmd import run_command_read_stdout,run_command_read_stdout_start,run_command_read_stdout_finish,Cmd
import pandas as pd
import io
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
    """
    Generates a command which binds CPU execution and memory allocation
    to a single NUMA node.

    Args:
        node (int): NUMA node to bind to 

    Returns:
        str: numactl command prefix to prepend to a command.

    Raises:
        RuntimeError: If numactl is not installed.
    """
    if shutil.which('numactl') is None:
        raise RuntimeError("numactl should be installed")
    return f"numactl --cpunodebind={node} --membind={node} "
def numactl_pin_mem(node:int) -> str:
    """
    Generates a command which binds memory allocation to a NUMA node
    without restricting CPU placement.

    Args:
        node (int): NUMA node for memory allocation

    Returns:
        str: numactl command prefix to prepend to a command.

    Raises:
        RuntimeError: If numactl is not installed.
    """
    if shutil.which('numactl') is None:
        raise RuntimeError("numactl should be installed")
    return f"numactl --membind={node} "


def numactl_pin_cpu(cpus:List[int],mem_node:Optional[int]) -> str:
    """
    Generates a command which binds execution to specific CPUs and
    binds memory to a NUMA node.

    Args:
        cpus (List[int]): CPU IDs the process is allowed to run on.
        mem_node (Optional[int]): NUMA node for memory allocation. If None,
                                  the NUMA node of cpus[0] is used.

    Returns:
        str: numactl command prefix to prepend to a command.

    Raises:
        RuntimeError: If numactl is not installed.
        AssertionError: If cpus is empty.
    """
    assert len(cpus) > 0
    if shutil.which('numactl') is None:
        raise RuntimeError("numactl should be installed")

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
def _build_msr_command(write:bool,ignore:Optional[List[int]]=None,include:Optional[List[int]]=None) -> str:
    assert not ((ignore is not None) and (include is not None)),"cannot provide both ignore and include"
    if ignore is not None and len(ignore) > 0:
        conds = [f"(args->msr!={hex(v)})" for v in ignore]
        cond = "&&".join(conds)
    elif include is not None and len(include) > 0:
        conds = [f"args->msr=={hex(v)}" for v in include]
        cond = "||".join(conds)
    else:
        cond = "1"
    event = "tracepoint:msr:write_msr" if write else "tracepoint:msr:read_msr"
    cmd = "bpftrace -e "
    cmd += "' "
    cmd += event
    cmd += "{ "
    cmd += f"if({cond})"
    cmd += '{printf("%d,\\"%x\\",\\"%lx\\"\\n", cpu, args->msr, args->val);}'
    cmd += " }"
    cmd += " '"
    return cmd

def start_profile_msr_verbose(write:bool,time_sec:int,ignore:Optional[List[int]]=None,include:Optional[List[int]]=None) -> Cmd:
    base_cmd = _build_msr_command(write,ignore,include)
    cmd = f"sudo timeout {time_sec} {base_cmd}"
    return run_command_read_stdout_start(cmd)

def stop_profile_msr(proc_data:Cmd) -> pd.DataFrame:
    res = run_command_read_stdout_finish(proc_data)
    #remove first line
    print(res)
    res = "\n".join(res.strip().splitlines()[1:])

    df = pd.read_csv(io.StringIO(res),header=None,names=["cpu","msr","val"])
    return df

