from typing import Dict, List, Tuple
from rykit.perf_sample import perf_sample_core_events,interpret_umask
def perf_sample_amd_uncore_event_many(
    cmd: str, unc_events: List[Tuple[str, str]]
) -> Dict[str, int]:
    """
    Run perf sampling for multiple uncore events.

    Args:
        cmd (str): Command to run under perf.
        unc_events (List[Tuple[str,str]]): List of (event, binary umask) pairs.

    Returns:
        Dict[str,Dict[str,int]]: Mapping of event code -> event counter value.
    """
    events = [f"amd_df/event={event},umask={interpret_umask(umask)}/" for event,umask in unc_events]
    return perf_sample_core_events(cmd,events)
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
