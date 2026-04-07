from rykit.linux_tools import lscpu
def test_lscpu():
    info = lscpu()
    assert len(info) != 0
    assert "Architecture" in info
