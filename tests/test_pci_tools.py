import shutil

import pytest

from rykit.pci_tools import (
    check_if_valid_pcie,
    get_lspci,
    pci_device_exists,
    pci_device_get_directory,
    pci_device_list,
    pci_device_numa_node,
    pci_device_str,
    pci_device_vendor_device,
)


def test_pci_device_str():
    assert pci_device_str(0, 0, 0, 0) == "0000:00:00.0"
    assert pci_device_str(0x1234, 0x56, 0x1A, 0x7) == "1234:56:1a.7"


def test_pci_device_get_directory():
    assert pci_device_get_directory(0, 0, 0, 0) == "/sys/bus/pci/devices/0000:00:00.0/"


def test_check_if_valid_pcie_bounds():
    # test valid bounds logic. pci_device_exists will fail if we use bounds that don't map to a real device.
    # We will test bounds assertions failure.
    with pytest.raises(AssertionError, match="domain .* out of bounds"):
        check_if_valid_pcie(2**16, 0, 0, 0, 0)
    with pytest.raises(AssertionError, match="bus .* out of bounds"):
        check_if_valid_pcie(0, 0x100, 0, 0, 0)
    with pytest.raises(AssertionError, match="device .* out of bounds"):
        check_if_valid_pcie(0, 0, 0x20, 0, 0)
    with pytest.raises(AssertionError, match="func .* out of bounds"):
        check_if_valid_pcie(0, 0, 0, 8, 0)
    with pytest.raises(AssertionError, match="offset .* out of bounds"):
        check_if_valid_pcie(0, 0, 0, 0, 2**12)
    with pytest.raises(AssertionError, match="offset .* not aligned"):
        check_if_valid_pcie(0, 0, 0, 0, 1)


def test_pci_live_sysfs():
    devices = pci_device_list()
    assert isinstance(devices, list)

    if not devices:
        pytest.skip("No PCI devices found on this system, skipping live sysfs tests.")

    domain, bus, device, func = devices[0]

    # Exists check
    assert pci_device_exists(domain, bus, device, func) is True

    # Vendor/Device
    vendor, dev_id = pci_device_vendor_device(domain, bus, device, func)
    assert isinstance(vendor, int)
    assert isinstance(dev_id, int)

    # Numa Node
    numa = pci_device_numa_node(domain, bus, device, func)
    assert isinstance(numa, int)
    assert numa >= -1

    # check_if_valid_pcie on real device
    # This shouldn't raise any errors for offset 0
    check_if_valid_pcie(domain, bus, device, func, 0)


def test_get_lspci_live():
    if not shutil.which("lspci"):
        pytest.skip("lspci not installed, skipping test.")

    devs = get_lspci()
    assert isinstance(devs, list)
    if devs:
        assert isinstance(devs[0], dict)
        assert "Slot" in devs[0] or "Class" in devs[0]  # ensure it parsed something
