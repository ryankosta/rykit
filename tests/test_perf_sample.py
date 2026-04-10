import pytest

from rykit.perf_sample import (
    _process_range,
    add_zeroes_to_eventcode,
    interpret_core_events,
    interpret_per_core_event,
    interpret_umask,
)


def test_process_range():
    assert _process_range("0-3") == (0, 3)
    assert _process_range("5") == (5, 5)

    with pytest.raises(ValueError, match="end < start"):
        _process_range("3-0")


def test_interpret_umask():
    assert interpret_umask("1101") == "0xd"
    assert interpret_umask("0000") == "0x0"
    assert interpret_umask("11111111") == "0xff"

    with pytest.raises(ValueError, match="not a valid binary string"):
        interpret_umask("invalid")

    with pytest.raises(ValueError, match="more then 8 bits"):
        interpret_umask("111111111")


def test_add_zeroes_to_eventcode():
    assert add_zeroes_to_eventcode("0xb3", 2) == "0x00b3"
    assert add_zeroes_to_eventcode("0x1", 0) == "0x1"
    assert add_zeroes_to_eventcode("0xFF", 4) == "0x0000FF"


def test_interpret_core_events():
    output = "   12345 events_a\n  6789 events_b"
    res = interpret_core_events(output, ["events_a", "events_b"])
    assert res["events_a"] == 12345
    assert res["events_b"] == 6789

    # Test with commas
    output_commas = "  12,345 events_c"
    res_commas = interpret_core_events(output_commas, ["events_c"])
    assert res_commas["events_c"] == 12345

    # Test with Byte interpretation (which does integer division by 64)
    output_bytes = "  12,345 Byte events_d"
    res_bytes = interpret_core_events(output_bytes, ["events_d"])
    assert res_bytes["events_d"] == int(12345 / 64)


def test_interpret_per_core_event():
    # fields expected: [S0-D0-C0, ignored, val, ...]
    output = (
        "S0-D0-C0;ignored;12345;event_1\n"
        "S0-D0-C1;ignored;6789;event_1\n"
        "S1-D0-C0;ignored;999;event_1\n"
        "S0-D0-C0;ignored;111;event_other"
    )

    # Check socket 0
    res_s0 = interpret_per_core_event(output, "event_1", 0)
    assert res_s0 == {"0": 12345, "1": 6789}

    # Check socket 1
    res_s1 = interpret_per_core_event(output, "event_1", 1)
    assert res_s1 == {"0": 999}
