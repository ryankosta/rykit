from rykit.linux_tools import lscpum,get_all_logical_cores,get_cache_siblings,get_cache_sibling_groups
def test_lscpu():
    info = lscpu()
    assert len(info) != 0
    assert "Architecture" in info
def test_linux_tools_functions_run():
    cores = get_all_logical_cores()
    assert len(cores) > 0
    core = cores[0]
    siblings = get_cache_siblings(core,0)
    assert core in siblings, "core must be sibling of itself"
    groups = get_cache_sibling_groups(0)
    assert len(groups) > 0
    for group in groups:
        assert len(group) >= 1, "sibling group shouldn't be empty"

