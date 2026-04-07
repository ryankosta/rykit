import pytest
from rykit.cmd import run_command_read_stdout
def test_run_command_read_stdout():
    assert run_command_read_stdout("echo hi") == "hi"
    with pytest.raises(ValueError) as exc_info:
        run_command_read_stdout("false")
    assert str(exc_info.value) == "Command failed with exit code 1."

