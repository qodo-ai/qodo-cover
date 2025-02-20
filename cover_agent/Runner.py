import subprocess
import time

from cover_agent.settings.config_loader import get_settings


class Runner:
    @staticmethod
    def run_command(command, cwd=None):
        """
        Executes a shell command in a specified working directory and returns its output, error, and exit code.

        Parameters:
            command (str): The shell command to execute.
            cwd (str, optional): The working directory in which to execute the command. Defaults to None.

        Returns:
            tuple: A tuple containing the standard output ('stdout'), standard error ('stderr'), exit code ('exit_code'), and the time of the executed command ('command_start_time').
        """
        # Get the current time before running the test command, in milliseconds
        command_start_time = int(round(time.time() * 1000))

        max_allowed_runtime_seconds = get_settings().get(
            "tests.max_allowed_runtime_seconds", 3600
        )
        # Ensure the command is executed with shell=True for string commands
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                text=True,
                capture_output=True,
                timeout=max_allowed_runtime_seconds,
            )

            # Return a dictionary with the desired information
            return result.stdout, result.stderr, result.returncode, command_start_time
        except subprocess.TimeoutExpired:
            # Handle the timeout case
            return "", "Command timed out", -1, command_start_time
