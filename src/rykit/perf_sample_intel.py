from typing import Dict, List, Tuple
from rykit.perf_sample import interpret_umask, add_zeroes_to_eventcode
from rykit.intel_tools import get_cha_count
from rykit.cmd import run_command_read_stderr




def create_unc_cha_event(chanum: int, event: str, hexmask: str) -> str:
    """
    Create a perf event string for a single CHA.

    Args:
        chanum (int): CHA index.
        event (str): Event code in hexadecimal (e.g., "0xb3").
        hexmask (str): Umask in hexadecimal (e.g., "0x8").

    Returns:
        str: Perf event string for the CHA.
    """
    return f"uncore_cha_{chanum}/event={event},umask={hexmask}/"


def create_unc_cha_events(event: str, hexmask: str) -> List[str]:
    """
    Create perf event strings for all CHAs on the system.

    Args:
        event (str): Event code in hexadecimal.
        hexmask (str): Umask in hexadecimal.

    Returns:
        List[str]: Perf event strings for each CHA.
    """

    num_chas = get_cha_count()
    return [create_unc_cha_event(chanum, event, hexmask) for chanum in range(num_chas)]


def build_perf_sample_uncore_cmd(
    program_cmd: str, unc_events: List[Tuple[str, str]]
) -> str:
    """
    Build a perf command that samples multiple uncore events.

    Args:
        program_cmd (str): Command to run under perf.
        unc_events (List[Tuple[str,str]]): List of (event, binary umask) pairs.

    Returns:
        str: The full perf command string.
    """
    events: List[str] = []
    for event, mask in unc_events:
        hexmask = interpret_umask(mask)
        events += create_unc_cha_events(event, hexmask)
    event_args: List[str] = [f"-e {e}" for e in events]
    event_arg_str = " ".join(event_args)
    return f"sudo perf stat -a {event_arg_str} -- {program_cmd}"


def interpret_uncore_event(output: str, event: str) -> Dict[str, int]:
    """
    Parse perf output for a single uncore event across CHAs.

    Args:
        output (str): Raw stderr output from perf.
        event (str): Event code in hexadecimal.

    Returns:
        Dict[str,int]: Mapping of CHA index (as str) -> event counter value.
    """
    infix = "uncore_cha_"
    number_suffix = f"/event={event}"
    result: Dict[str, int] = {}
    for line in output.split("\n"):
        # check to ensure this is a cha line
        if infix not in line or number_suffix not in line:
            continue
        # Example:
        # ex:     8,795      uncore_cha_1/event=0xb3,umask=0x8/

        # remove name of event
        # ex ->:      8,795
        count_str_with_commas = line.split(infix)[0]

        # remove ,
        # ex ->:      8795
        count_str = count_str_with_commas.replace(",", "")

        count = int(count_str)

        # chanum comes right after infix
        chanum = line.split(infix)[1].split(number_suffix)[0]
        result[chanum] = count
    return result


def interpret_uncore_event_many(
    output: str, events: List[str]
) -> Dict[str, Dict[str, int]]:
    """
    Parse perf output for multiple uncore events.

    Args:
        output (str): Raw stderr output from perf.
        events (List[str]): List of event codes in hexadecimal.

    Returns:
        Dict[str,Dict[str,int]]: Mapping of event code ->
             CHA index (as str) -> event counter value.
    """
    return {e: interpret_uncore_event(output, e) for e in events}


def perf_sample_uncore_event_many(
    program_cmd: str, unc_events: List[Tuple[str, str]]
) -> Dict[str, Dict[str, int]]:
    """
    Run perf sampling for multiple uncore events.

    Args:
        program_cmd (str): Command to run under perf.
        unc_events (List[Tuple[str,str]]): List of (event, binary umask) pairs.

    Returns:
        Dict[str,Dict[str,int]]: Mapping of event code ->
            CHA index (as str) -> event counter value.
    """
    assert isinstance(program_cmd, str), "cmd must be passed as string (passed non-str)"
    assert len(unc_events) <= 4, "can only run upto 4 uncore events at once"

    events = [e for e, _ in unc_events]
    if len(events) != len(set(events)):
        raise ValueError(
            f'this function does not support passing two identical event codes (passed {events})\n\t hint: prepend 0 ie ["0xF", "0x0F","0x00F","0x000F"]'
        )

    for _, mask in unc_events:
        assert isinstance(mask, str), "mask must be a binary string (passed non-str)"
        assert set(mask) <= {"0", "1"}, f"mask must be a binary string (passed {mask})"

    cmd = build_perf_sample_uncore_cmd(program_cmd, unc_events)

    output = run_command_read_stderr(cmd)

    events = [unce[0] for unce in unc_events]

    return interpret_uncore_event_many(output, events)


def perf_sample_uncore_event(program_cmd: str, event: str, mask: str) -> Dict[str, int]:
    """
    Run perf sampling for a single uncore event.

    Args:
        program_cmd (str): Command to run under perf.
        event (str): Event code in hexadecimal.
        mask (str): Umask in binary string form.

    Returns:
        Dict[str,int]: Mapping of CHA index (as str) -> event counter value.
    """
    res = perf_sample_uncore_event_many(program_cmd, [(event, mask)])
    return list(res.values())[0]




def perf_sample_uncore_event_many_named_masks(
    cmd: str, eventcode: str, masks: Dict[str, str]
) -> Dict[str, Dict[str, int]]:
    # create a list of unique eventcodes for each mask by adding zeroes to RHS (ie 0xF, 0x0F, 0x00F, ...) so that we have U  UID for event info from perf
    name_to_code: dict[str, str] = {
        k: add_zeroes_to_eventcode(eventcode, zeroct)
        for zeroct, k in enumerate(masks.keys())
    }
    code_to_name: dict[str, str] = {v: k for k, v in name_to_code.items()}

    uncore_events: List[Tuple[str, str]] = [
        (code, masks[name]) for name, code in name_to_code.items()
    ]

    res_by_event_code: Dict[str, Dict[str, int]] = perf_sample_uncore_event_many(
        cmd, uncore_events
    )
    # convert keys from eventcode to eventname
    res_by_event_name: Dict[str, Dict[str, int]] = {
        code_to_name[code]: ctr for code, ctr in res_by_event_code.items()
    }
    return res_by_event_name
