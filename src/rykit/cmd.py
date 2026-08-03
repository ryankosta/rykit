"""Provide tools to launch shell commands and read their string output."""

import logging
import subprocess
from typing import List, Tuple

logger = logging.getLogger(__name__)


def _check_return_code(
    stderr: str,
    code: int,
    verbose: bool = False,
    log_err_always: bool = False,
) -> None:
    if code == 124:  # GNU timeout uses exit code 124 when the command times out.
        if verbose:
            print("Command timed out as expected.")
    elif code == 0:
        if verbose:
            print("Command returned 0")
    else:
        print("\n\n=== STDERR")
        logger.error("Command stderr: %s", stderr)
        print(stderr)
        print("===\n\n")
        raise ValueError(f"Command failed with exit code {code}.")
    if log_err_always and stderr:
        logger.warning("Command stderr: %s", stderr)


def run_command_read_stderr(cmd: str, log_err_always: bool = False) -> str:
    """Run a shell command and capture stderr output.

    Args:
        cmd (str): The shell command to execute.
        log_err_always (bool): Whether to log nonempty stderr for successful commands.

    Returns:
        str: The stderr output of the command (perf writes stats here).
    """
    print(f"running cmd: {cmd}")
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output: str = result.stderr  # perf outputs stats to stderr

    _check_return_code(
        output,
        result.returncode,
        verbose=True,
        log_err_always=log_err_always,
    )

    return output


def run_command_read_stdout(cmd: str, log_err_always: bool = True) -> str:
    """Run a shell command and capture stdout output.

    Args:
        cmd (str): The shell command to execute.
        log_err_always (bool): Whether to log nonempty stderr for successful commands.

    Returns:
        str: The stdout output of the command.
    """
    print(f"running cmd: {cmd}")
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output: str = result.stdout

    _check_return_code(
        result.stderr,
        result.returncode,
        verbose=False,
        log_err_always=log_err_always,
    )

    return output


Cmd = subprocess.Popen[str]


def run_command_read_stdout_start(cmd: str) -> Cmd:
    """Start a shell command to capture future stdout.

    Args:
        cmd (str): The shell command to execute.

    Returns:
        Cmd: object to use for later reading command output
    """
    print(f"running cmd (in background): {cmd}")
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc


def run_command_read_stderr_start(cmd: str) -> Cmd:
    """Start a shell command to capture future stderr.

    Args:
        cmd (str): The shell command to execute.

    Returns:
        Cmd: object to use for later reading command output
    """
    return run_command_read_stdout_start(cmd)


def _cmd_join(proc_data: Cmd) -> Tuple[str, str]:
    proc = proc_data
    proc.wait()
    code = proc.returncode
    assert code is not None, "process did not exit after calling proc.wait()"
    stdout, stderr = proc.communicate()
    _check_return_code(stderr, code)
    return stdout, stderr


def run_command_read_stdout_finish(proc_data: Cmd) -> str:
    """Wait till shell command completes, read it's stdout.

    Args:
        proc_data (Cmd): command to read

    Returns:
        str: The stdout output of the command
    """
    stdout, _ = _cmd_join(proc_data)
    return stdout


def run_command_read_stderr_finish(proc_data: Cmd) -> str:
    """Wait till shell command completes, read it's stderr.

    Args:
        proc_data (Cmd): command to read

    Returns:
        str: The stderr output of the command
    """
    _, stderr = _cmd_join(proc_data)
    return stderr


def read_file_get_str(pathstr: str) -> str:
    """Read file and return string of contents.

    Args:
        pathstr (str): path of file
    Returns:
        str: Contents of file
    """
    with open(pathstr, "r") as f:
        return f.read().strip()


def read_file_get_lines(pathstr: str) -> List[str]:
    """Read file and return each line of file as a seperate str.

    Args:
        pathstr (str): path of file
    Returns:
        List[str]: List of lines of file
    """
    return read_file_get_str(pathstr).split("\n")
