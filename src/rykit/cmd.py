import subprocess
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
    if result.returncode == 124:  # 124 is timeout exit code
        print("Command timed out as expected.")
    elif result.returncode != 0:
        # output is stderr
        print(output)
        raise ValueError(f"Command failed with exit code {result.returncode}.")
    else:
        print("command returned 0")
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
    if result.returncode == 124:  # 124 is timeout exit code
        print("Command timed out as expected.")
    elif result.returncode != 0:
        print(result.stderr)
        raise ValueError(f"Command failed with exit code {result.returncode}.")
    return output
