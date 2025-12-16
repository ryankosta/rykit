from typing import Dict, List, Tuple
from rykit.perf_sample import perf_sample_core_events,interpret_umask,get_perf_event_paranoid
def perf_sample_amd_uncore_event_many(
        cmd: str, unc_events: List[Tuple[str, str]], sudo: bool=True
) -> Dict[str, int]:
    """
    Run perf sampling for multiple uncore events.

    Args:
        cmd (str): Command to run under perf.
        unc_events (List[Tuple[str,str]]): List of (event, binary umask) pairs.

    Returns:
        Dict[str,Dict[str,int]]: Mapping of event code -> event counter value.
    """

    paranoid = get_perf_event_paranoid()
    assert sudo or (paranoid <= 0), f"amd uncore sampling requires sudo or perf event paranoid of <= 0 (current is {paranoid})"

    events = [f"amd_df/event={event},umask={interpret_umask(umask)}/" for event,umask in unc_events]
    return perf_sample_core_events(cmd,events,sudo=sudo)
