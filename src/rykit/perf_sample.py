from rykit.cmd import run_command_read_stdout
from rykit.cmd import run_command_read_stderr
from typing import List, Dict 

def set_perf_event_paranoid(level: int):
    """
    Sets the kernel's perf_event_paranoid level.

    The perf_event_paranoid setting controls the restrictions on
    performance monitoring for non-root users:
        -1 : No restrictions
         0 : Normal access, but system-wide tracepoints may be restricted
         1 : Restricted access to CPU performance events
         2 : Disallow CPU performance events for unprivileged users
         3 : Maximum restriction (default on many systems)

    Args:
        level (int): The desired paranoid level (-1 to 3).

    Raises:
        AssertionError: If level is not an int or not in the allowed range.
    """
    assert type(level) == int
    assert -1 <= level and level <= 3, f"tried to set perf_event_paranoid to {level}, allowed values are -1 through 3"
    cmd = f"sudo sysctl -w kernel.perf_event_paranoid={level}"
    run_command_read_stdout(cmd)


def interpret_umask(binval: str) -> str:
    """
    Convert a binary string umask into its hexadecimal representation.

    Args:
        binval (str): A string representing a binary number (e.g., "1101").

    Returns:
        str: The hexadecimal representation of the binary umask
             (e.g., "0xd" for "1101").

    Raises:
        ValueError: If `binval` is not a valid binary string.
    """
    try:
        val: int = int(binval, 2)
    except:
        raise ValueError(f"mask {binval} was not a valid binary string")

    if val > 255:
        raise ValueError(f"{binval} was more then 8 bits")

    hex_str = str(hex(val))
    return hex_str




def interpret_core_events(output: str, core_events: List[str]) -> Dict[str, int]:
    """
    Parse perf output for core events.

    Args:
        output (str): Raw stderr output from perf.
        core_events (List[str]): List of event names to extract.

    Returns:
        Dict[str,int]: Mapping of event name -> event counter value.
    """
    lines = output.split("\n")
    res: Dict[str, int] = {}
    for line in lines:
        for event in core_events:
            if event in line:
                # remove name of event
                valstr = line.split(event)[0]
                valstr = valstr.strip()

                # remove commas
                valstr = valstr.replace(",", "")

                if "Byte" in valstr:

                    valstr = valstr.split("Byte")[0]

                    # TODO this is debatable whether you want this,
                    # Many events which are labeled byte
                    # cast from cache line to byte (ie: *64)
                    # so casting back (ie /64) is natural in most cases
                    val = int(int(valstr) / 64)
                else:
                    val = int(valstr)
                res[event] = val
    return res
def interpret_per_core_event(output:str,event:str,socket:int) -> Dict[str,int]:
    data : Dict[int,Dict[str,int]] = {skt:{} for skt in range(2)}
    for line in output.split("\n"):
        if event not in line:
            continue
        fields : List[str] = [x for x in line.split(";") if x != ""]
        #print(fields)
        #[S0,D0,C0]
        core_code = fields[0].split("-")
        socket_num = int(core_code[0][1:])
        core = core_code[2][1:]
        ctr = int(fields[2])
        data[socket_num][core] = ctr
    #print(data[socket])
    return data[socket]
def perf_sample_per_core_event(cmd:str,event:str,socket:int) -> Dict[str,int]:
    perf_cmd = f"sudo perf stat --per-core -x \\; -a -e {event} {cmd}"
    output = run_command_read_stderr(perf_cmd)
    return interpret_per_core_event(output,event,socket)
def perf_sample_per_core_events(cmd:str,events:List[str],socket:int) -> Dict[str,Dict[str,int]]:
    eventstr = " ".join([f"-e {event}" for event in events])
    perf_cmd = f"sudo perf stat --per-core -x \\; -a {eventstr} {cmd}"
    output = run_command_read_stderr(perf_cmd)
    return {event:interpret_per_core_event(output,event,socket) for event in events}
def perf_normalize_per_core_events(cmd:str,events:List[str],socket:int) -> Dict[str,Dict[str,float]]:
    events += ["cycles"]
    res = perf_sample_per_core_events(cmd,events,socket)
    cycles = res["cycles"]
    normalized_res = {event:{core:ctr/cycles[core] for core,ctr in percore.items()} for event,percore in res.items()}
    return normalized_res







def add_zeroes_to_eventcode(eventcode: str, zeroct: int):
    raw_hex_str = eventcode.split("0x")[1]
    return "0x" + ("0" * zeroct) + raw_hex_str

def perf_sample_core_events(cmd: str, core_events: List[str]) -> Dict[str, int]:
    """
    Run perf sampling for core events.

    Args:
        cmd (str): Command to run under perf.
        core_events (List[str]): List of core event names.

    Returns:
        Dict[str,int]: Mapping of event name -> event counter value.
    """

    event_flags = [f"-e {e}" for e in core_events]
    event_flag_str = " ".join(event_flags)

    output = run_command_read_stderr(f"sudo perf stat {event_flag_str} {cmd}")
    return interpret_core_events(output, core_events)
def perf_sample_core_event(cmd: str, core_event: str) -> int:
    """
    Run perf sampling for core event.

    Args:
        cmd (str): Command to run under perf.
        core_event (str):  core event name.

    Returns:
        int: core event value 
    """
    return perf_sample_core_events(cmd,[core_event])[core_event]
