import pytest

from cover_agent.runner import Runner


class TestRunner:
    def test_run_command_success(self):
        """Test the run_command method with a command that succeeds."""
        command = 'echo "Hello, World!"'
        stdout, stderr, exit_code, _ = Runner.run_command(command, max_run_time_sec=10)
        assert stdout.strip() == "Hello, World!"
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_with_cwd(self):
        """Test the run_command method with a specified working directory."""
        command = 'echo "Working Directory"'
        stdout, stderr, exit_code, _ = Runner.run_command(command, cwd="/tmp", max_run_time_sec=10)
        assert stdout.strip() == "Working Directory"
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_failure(self):
        """Test the run_command method with a command that fails."""
        # Use a command that is guaranteed to fail
        command = "command_that_does_not_exist"
        stdout, stderr, exit_code, _ = Runner.run_command(command, max_run_time_sec=10)
        assert stdout == ""
        assert (
            "command_that_does_not_exist: not found" in stderr
            or "command_that_does_not_exist: command not found" in stderr
        )
        assert exit_code != 0

    def test_run_command_timeout(self):
        """Test that a command exceeding the max_run_time_sec times out."""
        command = "sleep 2"  # A command that takes longer than the timeout
        stdout, stderr, exit_code, _ = Runner.run_command(command, max_run_time_sec=1)
        assert stdout == ""
        assert stderr == "Command timed out"
        assert exit_code == -1
