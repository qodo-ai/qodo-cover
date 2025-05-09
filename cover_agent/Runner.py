import subprocess
import time


class Runner:
    @staticmethod
    def run_command(command: str, max_run_time_sec: int, cwd: str = None):
        """
        Executes a shell command in a specified working directory and returns its output, error, and exit code.

        Parameters:
            command (str): The shell command to execute.
            max_run_time_sec (int): Maximum allowed runtime in seconds before timeout.
            cwd (str, optional): The working directory in which to execute the command. Defaults to None.

        Returns:
            tuple: A tuple containing the standard output ('stdout'), standard error ('stderr'), exit code ('exit_code'),
                   and the time of the executed command ('command_start_time').
        """
        command_start_time = int(
            time.time() * 1000
        )  # Get the current time in milliseconds

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=max_run_time_sec,
            )
            return result.stdout, result.stderr, result.returncode, command_start_time
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1, command_start_time
