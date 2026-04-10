"""Provides tools for PCI device scanning mapping on linux."""

import os
from typing import Dict, List, Tuple

from rykit.cmd import read_file_get_str, run_command_read_stdout
from rykit.linux_tools import get_numa_nodes


def pci_device_str(domain: int, bus: int, device: int, func: int) -> str:
    """Formats PCI device coordinates into a standard identifier string.

    Args:
        domain (int): The PCI domain number.
        bus (int): The PCI bus number.
        device (int): The PCI device number.
        func (int): The PCI function number.

    Returns:
        str: Formatted PCI device string in "DDDD:BB:DD.F" hexadecimal format.
    """
    return f"{domain:04x}:{bus:02x}:{device:02x}.{func:01x}"


def pci_device_get_directory(domain: int, bus: int, device: int, func: int) -> str:
    """Constructs the sysfs directory path for a specific PCI device.

    Args:
        domain (int): The PCI domain number.
        bus (int): The PCI bus number.
        device (int): The PCI device number.
        func (int): The PCI function number.

    Returns:
        str: Absolute path to the device's sysfs directory.
    """
    return "/sys/bus/pci/devices/" + pci_device_str(domain, bus, device, func) + "/"


def pci_device_exists(domain: int, bus: int, device: int, func: int) -> bool:
    """Checks if a PCI device exists in the system.

    Args:
        domain (int): The PCI domain number.
        bus (int): The PCI bus number.
        device (int): The PCI device number.
        func (int): The PCI function number.

    Returns:
        bool: True if the device directory exists in sysfs, False otherwise.
    """
    return os.path.exists(pci_device_get_directory(domain, bus, device, func))


def pci_device_vendor_device(
    domain: int, bus: int, device: int, func: int
) -> Tuple[int, int]:
    """Retrieves the vendor and device IDs for a specific PCI device.

    Args:
        domain (int): The PCI domain number.
        bus (int): The PCI bus number.
        device (int): The PCI device number.
        func (int): The PCI function number.

    Returns:
        Tuple[int, int]: A tuple containing the vendor ID and device ID as integers.
    """
    pcidir = pci_device_get_directory(domain, bus, device, func)
    vendor = int(read_file_get_str(f"{pcidir}/vendor"), 16)
    device = int(read_file_get_str(f"{pcidir}/device"), 16)
    return vendor, device


def pci_device_numa_node(domain: int, bus: int, device: int, func: int) -> int:
    """Get numa node which pci device resides on."""
    pcidir = pci_device_get_directory(domain, bus, device, func)
    # TODO is this hex?
    numa = int(read_file_get_str(f"{pcidir}/numa_node"))
    if numa == -1:
        numa_nodes = get_numa_nodes()
        assert len(numa_nodes) == 1, (
            "pci sysfs should only return -1 if their is only 1 numa node"
        )
        return numa_nodes[0]
    assert numa >= 0
    return numa


def pci_device_list() -> List[Tuple[int, int, int, int]]:
    """Lists the pci devices.

    Note: using some lspci here would be cleaner, but lspci is not installed by
    default always. so the sysfs method is a bit safer.

    Returns:
        List[Tuple[int,int,int,int]]: list of Domain,Bus,Device,Func for each pci device
    """
    devices: List[Tuple[int, int, int, int]] = []
    for pci_device_name in os.listdir("/sys/bus/pci/devices/"):
        try:
            domain_s, bus_s, dev_func_s = pci_device_name.split(":")
            dev_s, func_s = dev_func_s.split(".")
        except ValueError:
            raise AssertionError(
                "Error: /sys/bus/pci/devices had entry not in "
                f"form DOMAIN:BUS:DEVICE.FUNC ({pci_device_name})"
            )
        devices.append(
            (int(domain_s, 16), int(bus_s, 16), int(dev_s, 16), int(func_s, 16))
        )
    return devices


def check_if_valid_pcie(
    domain: int, bus: int, device: int, func: int, offset: int
) -> None:
    """Validates PCI parameters and register offsets against standard limits.

    Raises an AssertionError if any parameter is out of bounds or if
    the device does not exist.

    Args:
        domain (int): The PCI domain number (must be < 2**16).
        bus (int): The PCI bus number (must be <= 0xFF).
        device (int): The PCI device number (must be <= 0x1F).
        func (int): The PCI function number (must be <= 0x7).
        offset (int): The PCIe configuration space offset (must be
            < 2**12 and 4-byte aligned).

    Returns:
        None
    """
    assert domain < 2**16, f"domain {domain} out of bounds"
    assert bus <= 0xFF, f"bus {bus} out of bounds"
    assert device <= 0x1F, f"device {device} out of bounds"
    assert func <= 0x7, f"func {func} out of bounds"
    assert offset < 2**12, f"offset {offset} out of bounds"
    assert (offset % 4) == 0, f"offset {offset} not aligned"

    assert pci_device_exists(domain, bus, device, func)


def pciConfigRead32(domain: int, bus: int, device: int, func: int, offset: int) -> int:
    """Reads a 32-bit value from the PCI configuration space of a device using setpci.

    Args:
        domain (int): The PCI domain number.
        bus (int): The PCI bus number.
        device (int): The PCI device number.
        func (int): The PCI function number.
        offset (int): The configuration space offset to read from.

    Returns:
        int: The 32-bit data read from the specified offset.
    """
    check_if_valid_pcie(domain, bus, device, func, offset)
    addr_str = pci_device_str(domain, bus, device, func)

    offset_str = f"{offset:x}"
    cmd = f"sudo setpci -s {addr_str} {offset_str}.l"
    res = run_command_read_stdout(cmd)
    return int(res, 16)


def pciConfigWrite32(
    domain: int, bus: int, device: int, func: int, offset: int, data: int
) -> None:
    """Writes a 32-bit value to the PCI configuration space of a device using setpci.

    Args:
        domain (int): The PCI domain number.
        bus (int): The PCI bus number.
        device (int): The PCI device number.
        func (int): The PCI function number.
        offset (int): The configuration space offset to write to.
        data (int): The 32-bit value to write.

    Returns:
        None
    """
    check_if_valid_pcie(domain, bus, device, func, offset)

    addr_str = pci_device_str(domain, bus, device, func)

    offset_str = f"{offset:x}"
    data_str = f"{data:x}"
    cmd = f"sudo setpci -s {addr_str} {offset_str}.l={data_str}"
    run_command_read_stdout(cmd)


def get_lspci() -> List[Dict[str, str]]:
    """Parses machine-readable output from lspci into a list of dictionaries.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, where each dictionary represents
        a PCI device and its parsed key-value properties.
    """
    lines = run_command_read_stdout("lspci -vmm").strip().split("\n")
    curr_dev: Dict[str, str] = {}
    devs: List[Dict[str, str]] = []
    for line in lines:
        if ":" not in line:
            continue
        field, val = line.split(":", 1)

        # found a new device
        if field == "Slot":
            # add the last device to list if it had any fields
            if len(curr_dev) > 0:
                devs.append(curr_dev)
            # start reading a new device
            curr_dev = {}

        # add field to current device
        curr_dev[field] = val

    # the final device must be manually added
    if len(curr_dev) > 0:
        devs.append(curr_dev)
    return devs
