from rykit.cmd import run_command_read_stdout,read_file_get_str
from rykit.linux_tools import lscpu
import os
from typing import List, Dict,Tuple
def pci_device_str(domain:int,bus:int,device:int,func:int) -> str:
    return f"{domain:04x}:{bus:02x}:{device:02x}.{func:01x}"

def pci_device_get_directory(domain:int,bus:int,device:int,func:int) -> str:
    return "/sys/bus/pci/devices/" + pci_device_str(domain,bus,device,func) + "/"

def pci_device_exists(domain:int,bus:int,device:int,func:int) -> bool:
    return os.path.exists(pci_device_get_directory(domain,bus,device,func))


def pci_device_vendor_device(domain:int,bus:int,device:int,func:int) -> Tuple[int,int]:
    pcidir = pci_device_get_directory(domain,bus,device,func)
    vendor = int(read_file_get_str(f"{pcidir}/vendor"),16)
    device = int(read_file_get_str(f"{pcidir}/device"),16)
    return vendor,device



def check_if_valid_pcie(domain:int, bus:int,device:int,func:int,offset:int):
    assert domain < 2**16, f"domain {domain} out of bounds"
    assert bus <= 0xFF, f"bus {bus} out of bounds"
    assert device <= 0x1F, f"device {device} out of bounds"
    assert func <= 0x7, f"func {func} out of bounds"
    assert offset < 2**12, f"offset {offset} out of bounds"
    assert (offset % 4) == 0, f"offset {offset} not aligned"

    assert pci_device_exists(domain,bus,device,func)

def pciConfigRead32(domain:int, bus:int,device:int,func:int,offset:int) -> int:
    check_if_valid_pcie(domain,bus,device,func,offset)
    addr_str = pci_device_str(domain,bus,device,func)

    offset_str = f"{offset:x}"
    cmd = f"sudo setpci -s {addr_str} {offset_str}.l"
    res = run_command_read_stdout(cmd)
    return int(res,16)

def pciConfigWrite32(domain:int, bus:int,device:int,func:int,offset:int,data:int):
    check_if_valid_pcie(domain,bus,device,func,offset)

    addr_str = pci_device_str(domain,bus,device,func)


    offset_str = f"{offset:x}"
    data_str = f"{data:x}"
    cmd = f"sudo setpci -s {addr_str} {offset_str}.l={data_str}"
    run_command_read_stdout(cmd)

def get_lspci() -> List[Dict[str,str]]:
    lines = run_command_read_stdout("lspci -vmm").strip().split("\n")
    curr_dev : Dict[str,str] = {}
    devs : List[Dict[str,str]] = []
    for line in lines:
        if ":" not in line:
            continue
        field,val = line.split(":",1)

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
