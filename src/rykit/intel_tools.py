import glob
def get_cha_count() -> int:
    """
    Return the number of CHA devices under /sys/devices.

    Returns:
        int: Count of directories matching 'uncore_cha_*'.
    """
    cha_paths = glob.glob("/sys/devices/uncore_cha_*")
    return len(cha_paths)
