from rykit import linux_tools, msrhelper, pci_tools, perf_sample, perf_sample_intel
from tests.helpers import (
    stub_run_command_read_stderr,
    stub_run_command_read_stdout,
)


def test_linux_tools_stdout_callers(monkeypatch):
    stub_run_command_read_stdout(
        monkeypatch,
        linux_tools,
        {
            "lscpu": "Architecture: x86_64\nNUMA node(s): 2",
            "lscpu -C": (
                "NAME ONE-SIZE ALL-SIZE WAYS TYPE LEVEL SETS PHY-LINE "
                "COHERENCY-SIZE\nL1d 48K 96K 12 Data 1 64 1 64"
            ),
        },
    )

    assert linux_tools.lscpu()["Architecture"] == "x86_64"
    assert linux_tools.lscpu_cache()["L1d"]["ONE-SIZE"] == "48K"


def test_msrhelper_stdout_callers(monkeypatch):
    monkeypatch.setattr(msrhelper, "check_msr_tools_installed", lambda: True)
    monkeypatch.setattr(msrhelper, "check_msr_dev_exists", lambda: True)
    stub_run_command_read_stdout(
        monkeypatch,
        msrhelper,
        {
            "sudo wrmsr -a 0x10 0x20": "",
            "sudo wrmsr -p 2 0x10 0x20": "",
            "sudo rdmsr -p 2 0x10": "20\n",
        },
    )

    msrhelper.wrmsr_broadcast(0x10, 0x20)
    msrhelper.wrmsr(0x10, 0x20, cpu=2)
    assert msrhelper.rdmsr(0x10, cpu=2) == 0x20


def test_pci_tools_stdout_callers(monkeypatch):
    monkeypatch.setattr(pci_tools, "check_if_valid_pcie", lambda *args: None)
    stub_run_command_read_stdout(
        monkeypatch,
        pci_tools,
        {
            "sudo setpci -s 0000:01:02.3 10.l": "1234abcd\n",
            "sudo setpci -s 0000:01:02.3 10.l=1234abcd": "",
            "lspci -vmm": (
                "Slot:\t0000:01:02.3\nClass:\tEthernet controller\n"
                "Vendor:\tExample\n"
            ),
        },
    )

    assert pci_tools.pciConfigRead32(0, 1, 2, 3, 0x10) == 0x1234ABCD
    pci_tools.pciConfigWrite32(0, 1, 2, 3, 0x10, 0x1234ABCD)
    assert pci_tools.get_lspci() == [
        {
            "Slot": "\t0000:01:02.3",
            "Class": "\tEthernet controller",
            "Vendor": "\tExample",
        }
    ]


def test_set_perf_event_paranoid(monkeypatch):
    stub_run_command_read_stdout(
        monkeypatch,
        perf_sample,
        {"sudo sysctl -w kernel.perf_event_paranoid=1": ""},
    )

    perf_sample.set_perf_event_paranoid(1)


def test_perf_sample_stderr_callers(monkeypatch):
    per_core_output = (
        "S0-D0-C0;ignored;10;event_a\n"
        "S0-D0-C0;ignored;20;event_b\n"
    )
    stub_run_command_read_stderr(
        monkeypatch,
        perf_sample,
        {
            "sudo perf stat --per-core -x \\; -a -e event_a work": per_core_output,
            (
                "sudo perf stat --per-core -x \\; -a "
                "-e event_a -e event_b work"
            ): per_core_output,
            "sudo perf stat -a -e event_a work": "123 event_a\n",
        },
    )

    assert perf_sample.perf_sample_per_core_event("work", "event_a", 0) == {
        "0": 10
    }
    assert perf_sample.perf_sample_per_core_events(
        "work", ["event_a", "event_b"], 0
    ) == {"event_a": {"0": 10}, "event_b": {"0": 20}}
    assert perf_sample.perf_sample_core_events(
        "work", ["event_a"], flags=["a"]
    ) == {"event_a": 123}


def test_perf_sample_intel_stderr_caller(monkeypatch):
    monkeypatch.setattr(perf_sample_intel, "get_cha_count", lambda: 1)
    cmd = "sudo perf stat -a -e uncore_cha_0/event=0xb3,umask=0x1/ -- work"
    stub_run_command_read_stderr(
        monkeypatch,
        perf_sample_intel,
        {cmd: "42 uncore_cha_0/event=0xb3,umask=0x1/\n"},
    )

    assert perf_sample_intel.perf_sample_uncore_event_many(
        "work", [("0xb3", "1")]
    ) == {"0xb3": {"0": 42}}
