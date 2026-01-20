import subprocess
from typing import Tuple

def _check_return_code(stderr:str,code:int, verbose=False):
    if code == 124 and verbose :  # 124 is timeout exit code
        print("Command timed out as expected.")
    elif code == 0 and verbose:
        print("Command returned 0")
    else:
        print(stderr)
        raise ValueError(f"Command failed with exit code {code}.")
def run_command_read_stderr(cmd: str) -> str:
    """
    Run a shell command and capture stderr output.

    Args:
        cmd (str): The shell command to execute.

    Returns:
        str: The stderr output of the command (perf writes stats here).
    """
    print(f"running cmd: {cmd}")
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output: str = result.stderr  # perf outputs stats to stderr

    _check_return_code(output,result.returncode,True)

    return output


def run_command_read_stdout(cmd: str) -> str:
    """
    Run a shell command and capture stdout output.

    Args:
        cmd (str): The shell command to execute.

    Returns:
        str: The stderr output of the command (perf writes stats here).
    """
    print(f"running cmd: {cmd}")
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    output: str = result.stdout

    _check_return_code(result.stderr,result.returncode)

    return output

Cmd = subprocess.Popen[str]
def run_command_read_stdout_start(cmd:str) -> Cmd:
    """
    Start a shell command to capture future stdout

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
def run_command_read_stderr_start(cmd:str) -> Cmd:
    """
    Start a shell command to capture future stderr

    Args:
        cmd (str): The shell command to execute.

    Returns:
        Cmd: object to use for later reading command output 
    """
    return run_command_read_stdout_start(cmd)

def _cmd_join(proc_data : Cmd) -> Tuple[str,str]:
    proc = proc_data
    proc.wait()
    code = proc.returncode
    assert code is not None, "process did not exit after calling proc.wait()"
    stdout, stderr = proc.communicate()
    _check_return_code(stderr,code)
    return stdout,stderr

def run_command_read_stdout_finish(proc_data : Cmd) -> str:
    """
    Wait till shell command completes, read it's stdout


    Args:
        proc_data (Cmd): command to read

    Returns:
        str: The stdout output of the command 
    """
    stdout, _ = _cmd_join(proc_data)
    return stdout
def run_command_read_stderr_finish(proc_data : Cmd) -> str:
    """
    Wait till shell command completes, read it's stderr


    Args:
        proc_data (Cmd): command to read

    Returns:
        str: The stderr output of the command
    """
    _, stderr = _cmd_join(proc_data)
    return stderr


