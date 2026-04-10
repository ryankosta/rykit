from rykit.linux_tools import (
    get_all_logical_cores,
    get_cache_sibling_groups,
    get_cache_siblings,
    get_socket,
    get_socket_ct,
    get_socket_for_cpu,
    lscpu,
)


def test_lscpu():
    info = lscpu()
    assert len(info) != 0
    assert "Architecture" in info


# TODO TODO these tests are a bit circularly defined
# but generally should find bugs
def test_get_socket_for_cpu():
    for core in get_all_logical_cores():
        skt = get_socket_for_cpu(core)
        cores_in_skt = get_socket(skt)
        assert core in cores_in_skt


def test_get_socket_ct():
    cores = get_all_logical_cores()
    sockets = set(get_socket_for_cpu(c) for c in cores)
    assert len(sockets) == get_socket_ct()


def test_linux_tools_functions_run():
    cores = get_all_logical_cores()
    assert len(cores) > 0
    core = cores[0]
    siblings = get_cache_siblings(core, 0)
    assert core in siblings, "core must be sibling of itself"
    groups = get_cache_sibling_groups(0)
    assert len(groups) > 0
    for group in groups:
        assert len(group) >= 1, "sibling group shouldn't be empty"
