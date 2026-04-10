import pytest

from rykit.cmd import (
    read_file_get_lines,
    read_file_get_str,
    run_command_read_stderr,
    run_command_read_stderr_finish,
    run_command_read_stderr_start,
    run_command_read_stdout,
    run_command_read_stdout_finish,
    run_command_read_stdout_start,
)

def test_run_command_read_stdout():

    assert run_command_read_stdout("echo hi").strip() == "hi"

    with pytest.raises(ValueError) as exc_info:
        run_command_read_stdout("false")
    assert str(exc_info.value) == "Command failed with exit code 1."


def test_run_command_read_stderr():
    assert "error" in run_command_read_stderr("echo error 1>&2")

    with pytest.raises(ValueError):
        run_command_read_stderr("false")


def test_run_command_start_finish():
    proc_out = run_command_read_stdout_start("echo out")
    assert run_command_read_stdout_finish(proc_out).strip() == "out"

    proc_err = run_command_read_stderr_start("echo err 1>&2")
    assert "err" in run_command_read_stderr_finish(proc_err)


def test_read_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\n")

    assert read_file_get_str(str(test_file)) == "line1\nline2"
    assert read_file_get_lines(str(test_file)) == ["line1", "line2"]
