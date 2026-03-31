from rykit.cmd import run_command_read_stdout
from typing import Optional
import os
import shutil
def check_msr_dev_exists() -> bool:
    """Checks if the MSR device file exists.

    Returns:
        bool: True if /dev/cpu/0/msr exists, False otherwise.
    """
    return os.path.exists("/dev/cpu/0/msr")
def check_msr_tools_installed() -> bool:
    """Checks if the msr-tools package is installed in the system PATH.

    Returns:
        bool: True if the 'wrmsr' executable is found, False otherwise.
    """
    return shutil.which("wrmsr") is not None
def wrmsr_broadcast(msr:int,val:int) -> None:
    """Writes a value to a Model-Specific Register (MSR) across all CPUs.

    Args:
        msr (int): The MSR address to write to.
        val (int): The value to write to the MSR.

    Returns:
        None
    """
    assert check_msr_tools_installed()
    assert check_msr_dev_exists()
    run_command_read_stdout(f"sudo wrmsr -a 0x{msr:X} 0x{val:X}")

def wrmsr(msr:int,val:int,cpu:Optional[int]=None) -> None:
    """Writes a value to a Model-Specific Register (MSR) across all CPUs.

    Args:
        msr (int): The MSR address to write to.
        val (int): The value to write to the MSR.
        cpu (Optional[int]): cpu to write from, if none then randomly chose
                             (likely cpu0 by default)

    Returns:
        None
    """
    assert check_msr_tools_installed()
    assert check_msr_dev_exists()
    flags = ""
    if cpu is not None:
        flags = f"-p {cpu}"
    run_command_read_stdout(f"sudo wrmsr {flags} 0x{msr:X} 0x{val:X}")


def rdmsr(msr:int,cpu:Optional[int]=None) -> int:
    """Reads a value from a Model-Specific Register (MSR).

    Args:
        msr (int): The MSR address to read from.
        cpu (Optional[int]): cpu to read from, if none then randomly chose
                             (likely cpu0 by default)

    Returns:
        int: The 64-bit integer value read from the MSR.
    """
    assert check_msr_tools_installed()
    assert check_msr_dev_exists()
    flags = ""
    if cpu is not None:
        flags = f"-p {cpu}"

    val = run_command_read_stdout(f"sudo rdmsr {flags} 0x{msr:X}").strip()
    return int(val,16)

