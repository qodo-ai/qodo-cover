import argparse
import os
import tempfile

from unittest.mock import MagicMock, mock_open, patch

import pytest

from cover_agent.cover_agent import CoverAgent
from cover_agent.main import parse_args
from cover_agent.settings.config_schema import CoverAgentConfig


class TestCoverAgent:
    """
    Test suite for the CoverAgent class.
    """

    @staticmethod
    def create_config_from_args(args: argparse.Namespace) -> CoverAgentConfig:
        """Helper function to create CoverAgentConfig from argparse.Namespace"""
        return CoverAgentConfig(
            source_file_path=args.source_file_path,
            test_file_path=args.test_file_path,
            project_root=args.project_root,
            test_file_output_path=getattr(args, "test_file_output_path", ""),
            code_coverage_report_path=args.code_coverage_report_path,
            test_command=args.test_command,
            test_command_dir=args.test_command_dir,
            included_files=args.included_files,
            coverage_type=args.coverage_type,
            report_filepath=args.report_filepath,
            desired_coverage=args.desired_coverage,
            max_iterations=args.max_iterations,
            max_run_time_sec=args.max_run_time_sec,
            additional_instructions=getattr(args, "additional_instructions", ""),
            model=getattr(args, "model", ""),
            api_base=getattr(args, "api_base", ""),
            strict_coverage=getattr(args, "strict_coverage", False),
            run_tests_multiple_times=getattr(args, "run_tests_multiple_times", 1),
            log_db_path=getattr(args, "log_db_path", ""),
            branch=getattr(args, "branch", "master"),
            use_report_coverage_feature_flag=getattr(args, "use_report_coverage_feature_flag", False),
            diff_coverage=getattr(args, "diff_coverage", False),
            run_each_test_separately=getattr(args, "run_each_test_separately", False),
            record_mode=getattr(args, "record_mode", False),
            suppress_log_files=args.suppress_log_files,
            max_test_files_allowed_to_analyze=getattr(args, "max_test_files_allowed_to_analyze", 20),
            look_for_oldest_unchanged_test_file=getattr(args, "look_for_oldest_unchanged_test_file", False),
            project_language=getattr(args, "project_language", "python"),
        )

    def test_parse_args(self):
        """
        Test the argument parsing functionality of the `parse_args` function.

        This test ensures that the `parse_args` function correctly parses command-line
        arguments and overrides default settings with the provided values.

        Steps:
        - Mock the settings object to provide default values for configuration.
        - Patch `sys.argv` to simulate command-line arguments.
        - Verify that the parsed arguments match the expected values.

        Assertions:
        - Ensure that each argument is parsed correctly and matches the expected value.

        Args:
            self: The test class instance.
        """

        # Create mock settings with required default values
        mock_settings = MagicMock()
        mock_settings.get.side_effect = lambda x: {
            "included_files": None,
            "coverage_type": "cobertura",
            "report_filepath": "test_results.html",
            "desired_coverage": 90,
            "max_iterations": None,  # Will be overridden by CLI arg
            "model": "gpt-3.5-turbo",
            "api_base": "",
            "max_run_time_sec": 300,
            "run_tests_multiple_times": 1,
            "branch": "master",
            "log_db_path": None,
        }[x]

        with patch(
            "sys.argv",
            [
                "program.py",
                "--source-file-path",
                "test_source.py",
                "--test-file-path",
                "test_file.py",
                "--code-coverage-report-path",
                "coverage_report.xml",
                "--test-command",
                "pytest",
                "--max-iterations",
                "10",
                "--suppress-log-files",
            ],
        ):
            args = parse_args(mock_settings)
            # Assertions to verify correct argument parsing
            assert args.source_file_path == "test_source.py"
            assert args.test_file_path == "test_file.py"
            assert args.project_root == ""
            assert args.code_coverage_report_path == "coverage_report.xml"
            assert args.test_command == "pytest"
            assert args.test_command_dir == os.getcwd()
            assert args.included_files is None
            assert args.coverage_type == "cobertura"
            assert args.report_filepath == "test_results.html"
            assert args.desired_coverage == 90
            assert args.max_iterations == 10
            assert args.suppress_log_files is True

    @patch("cover_agent.cover_agent.UnitTestGenerator")
    @patch("cover_agent.cover_agent.os.path.isfile")
    def test_agent_source_file_not_found(self, mock_isfile, mock_unit_cover_agent):
        """
        Test the behavior when the test file is not found.

        This test ensures that a FileNotFoundError is raised when the test file
        specified in the configuration does not exist. It also verifies that
        the UnitTestGenerator is not called in this scenario.

        Args:
            mock_unit_cover_agent (MagicMock): Mock for UnitTestGenerator to ensure it is not called.
            mock_isfile (MagicMock): Mock for os.path.isfile to simulate file existence.
        """
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            project_root="",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            max_run_time_sec=30,
            suppress_log_files=False,
        )
        parse_args = lambda: args
        mock_isfile.return_value = False

        config = self.create_config_from_args(args)
        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                agent = CoverAgent(config)

        # Assert that the correct error message is raised
        assert str(exc_info.value) == f"Source file not found at {args.source_file_path}"

        mock_unit_cover_agent.assert_not_called()

        assert args.suppress_log_files is False

    @patch("cover_agent.cover_agent.os.path.exists")
    @patch("cover_agent.cover_agent.os.path.isfile")
    @patch("cover_agent.cover_agent.UnitTestGenerator")
    def test_agent_test_file_not_found(self, mock_unit_cover_agent, mock_isfile, mock_exists):
        """
        Test the behavior when the test file is not found.

        This test ensures that a FileNotFoundError is raised when the test file
        specified in the configuration does not exist. It also verifies that
        the UnitTestGenerator is not called in this scenario.

        Args:
            mock_unit_cover_agent (MagicMock): Mock for UnitTestGenerator to ensure it is not called.
            mock_isfile (MagicMock): Mock for os.path.isfile to simulate file existence.
            mock_exists (MagicMock): Mock for os.path.exists to simulate directory existence.
        """
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            project_root="",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            prompt_only=False,
            max_run_time_sec=30,
            suppress_log_files=False,
        )
        parse_args = lambda: args
        mock_isfile.side_effect = [True, False]
        mock_exists.return_value = True

        config = self.create_config_from_args(args)
        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                agent = CoverAgent(config)

        # Assert that the correct error message is raised
        assert str(exc_info.value) == f"Test file not found at {args.test_file_path}"

    @patch("cover_agent.cover_agent.os.path.isfile", return_value=True)
    def test_duplicate_test_file_without_output_path(self, mock_isfile):
        """
        Test the behavior when no output path is provided for the test file.

        This test ensures that if the `test_file_output_path` is not provided,
        the `_duplicate_test_file` method in the `CoverAgent` class sets it
        to the value of `test_file_path`. It also verifies that an
        `AssertionError` is raised when the coverage report is not generated.

        Args:
            mock_isfile (MagicMock): Mock for `os.path.isfile` to simulate
            the existence of files.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file:
                args = argparse.Namespace(
                    source_file_path=temp_source_file.name,
                    test_file_path=temp_test_file.name,
                    project_root="",
                    test_file_output_path="",
                    code_coverage_report_path="coverage_report.xml",
                    test_command="echo hello",
                    test_command_dir=os.getcwd(),
                    included_files=None,
                    coverage_type="cobertura",
                    report_filepath="test_results.html",
                    desired_coverage=90,
                    max_iterations=10,
                    additional_instructions="",
                    model="openai/test-model",
                    api_base="openai/test-api",
                    use_report_coverage_feature_flag=False,
                    log_db_path="",
                    diff_coverage=False,
                    branch="main",
                    run_tests_multiple_times=1,
                    max_run_time_sec=30,
                    record_mode=False,
                    disable_file_generation=False,
                    suppress_log_files=False,
                )

                config = self.create_config_from_args(args)
                with pytest.raises(AssertionError) as exc_info:
                    agent = CoverAgent(config)
                    failed_test_runs = agent.test_validator.get_coverage()
                    agent._duplicate_test_file()

                # Assert that the correct error message is raised
                assert "Fatal: Coverage report" in str(exc_info.value)
                assert config.test_file_output_path == config.test_file_path

        # Clean up the temp files
        os.remove(temp_source_file.name)
        os.remove(temp_test_file.name)

    @patch("cover_agent.cover_agent.os.environ", {})
    @patch("cover_agent.cover_agent.sys.exit")
    @patch("cover_agent.cover_agent.UnitTestGenerator")
    @patch("cover_agent.cover_agent.UnitTestValidator")
    @patch("cover_agent.cover_agent.UnitTestDB")
    def test_run_max_iterations_strict_coverage(
        self,
        mock_test_db,
        mock_unit_test_validator,
        mock_unit_test_generator,
        mock_sys_exit,
    ):
        """
        Test the behavior of the CoverAgent when strict coverage is enabled and the maximum number of iterations is reached.

        This test ensures that:
        - The `sys.exit` method is called with the correct exit code when the desired coverage is not met.
        - The coverage report is dumped to the specified report file.
        - The `UnitTestValidator` and `UnitTestGenerator` are used correctly during the process.

        Args:
            mock_test_db (MagicMock): Mock for the `UnitTestDB` class to verify interactions with the database.
            mock_unit_test_validator (MagicMock): Mock for the `UnitTestValidator` class to simulate coverage validation.
            mock_unit_test_generator (MagicMock): Mock for the `UnitTestGenerator` class to simulate test generation.
            mock_sys_exit (MagicMock): Mock for the `sys.exit` function to verify the exit behavior.
        """
        with (
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_output_file,
        ):
            args = argparse.Namespace(
                source_file_path=temp_source_file.name,
                test_file_path=temp_test_file.name,
                project_root="",
                test_file_output_path=temp_output_file.name,  # Changed this line
                code_coverage_report_path="coverage_report.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="test_results.html",
                desired_coverage=90,
                max_iterations=1,
                additional_instructions="",
                model="openai/test-model",
                api_base="openai/test-api",
                use_report_coverage_feature_flag=False,
                log_db_path="",
                run_tests_multiple_times=False,
                strict_coverage=True,
                diff_coverage=False,
                branch="main",
                max_run_time_sec=30,
                record_mode=False,
                disable_file_generation=False,
                suppress_log_files=False,
            )
            # Mock the methods used in run
            validator = mock_unit_test_validator.return_value
            validator.current_coverage = 0.5  # below desired coverage
            validator.desired_coverage = 90
            validator.get_coverage.return_value = [{}, "python", "pytest", ""]
            generator = mock_unit_test_generator.return_value
            generator.generate_tests.return_value = {"new_tests": [{}]}

            config = self.create_config_from_args(args)
            agent = CoverAgent(config)
            agent.run()

            # Assertions to ensure sys.exit was called
            mock_sys_exit.assert_called_once_with(2)
            mock_test_db.return_value.dump_to_report.assert_called_once_with(args.report_filepath)

    @patch("cover_agent.cover_agent.os.path.isfile", return_value=True)
    @patch("cover_agent.cover_agent.os.path.isdir", return_value=False)
    def test_project_root_not_found(self, mock_isdir, mock_isfile):
        """
        Test the behavior when the project root directory is not found.

        This test ensures that a FileNotFoundError is raised when the specified
        project root directory does not exist. It also verifies that the error
        message contains the correct path.

        Args:
            mock_isdir (MagicMock): Mock for `os.path.isdir` to simulate directory existence.
            mock_isfile (MagicMock): Mock for `os.path.isfile` to simulate file existence.
        """
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            project_root="/nonexistent/path",
            test_file_output_path="",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            max_run_time_sec=30,
            suppress_log_files=False,
        )

        config = self.create_config_from_args(args)
        with pytest.raises(FileNotFoundError) as exc_info:
            agent = CoverAgent(config)

        # Assert that the correct error message is raised
        assert str(exc_info.value) == f"Project root not found at {args.project_root}"

    @patch("cover_agent.cover_agent.UnitTestValidator")
    @patch("cover_agent.cover_agent.UnitTestGenerator")
    @patch("cover_agent.cover_agent.UnitTestDB")
    @patch("cover_agent.cover_agent.CustomLogger")
    def test_run_diff_coverage(self, mock_logger, mock_test_db, mock_test_gen, mock_test_validator):
        """
        Test the behavior of the CoverAgent when diff coverage is enabled.

        This test ensures that:
        - The `UnitTestValidator` correctly calculates the current coverage.
        - The `UnitTestGenerator` generates new tests as expected.
        - The `CustomLogger` logs the current diff coverage percentage.
        - Temporary files are cleaned up after the test.

        Args:
            mock_logger (MagicMock): Mock for the `CustomLogger` class to verify logging behavior.
            mock_test_db (MagicMock): Mock for the `UnitTestDB` class to simulate database interactions.
            mock_test_gen (MagicMock): Mock for the `UnitTestGenerator` class to simulate test generation.
            mock_test_validator (MagicMock): Mock for the `UnitTestValidator` class to simulate coverage validation.
        """
        with (
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_output_file,
        ):

            args = argparse.Namespace(
                source_file_path=temp_source_file.name,
                test_file_path=temp_test_file.name,
                project_root="",
                test_file_output_path=temp_output_file.name,  # Changed to use temp file
                code_coverage_report_path="coverage_report.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="test_results.html",
                desired_coverage=90,
                max_iterations=1,
                additional_instructions="",
                model="openai/test-model",
                api_base="openai/test-api",
                use_report_coverage_feature_flag=False,
                log_db_path="",
                run_tests_multiple_times=False,
                strict_coverage=False,
                diff_coverage=True,
                branch="main",
                max_run_time_sec=30,
                record_mode=False,
                disable_file_generation=False,
                suppress_log_files=False,
            )
            mock_test_validator.return_value.current_coverage = 0.5
            mock_test_validator.return_value.desired_coverage = 90
            mock_test_validator.return_value.get_coverage.return_value = [{}, "python", "pytest", ""]
            mock_test_gen.return_value.generate_tests.return_value = {"new_tests": [{}]}
            config = self.create_config_from_args(args)
            agent = CoverAgent(config)
            agent.run()
            mock_logger.get_logger.return_value.info.assert_any_call(
                f"Current Diff Coverage: {round(mock_test_validator.return_value.current_coverage * 100, 2)}%"
            )

        # Clean up the temp files
        os.remove(temp_source_file.name)
        os.remove(temp_test_file.name)
        os.remove(temp_output_file.name)

    @patch("cover_agent.cover_agent.os.path.isfile", return_value=True)
    @patch("cover_agent.cover_agent.os.path.isdir", return_value=True)
    @patch("cover_agent.cover_agent.shutil.copy")
    @patch("builtins.open", new_callable=mock_open, read_data="# Test content")
    def test_run_each_test_separately_with_pytest(self, mock_open_file, mock_copy, mock_isdir, mock_isfile):
        """
        Test the behavior of the CoverAgent when running each test separately with pytest.

        This test ensures that:
        - The `test_command` is modified correctly to include the specific test file.
        - Temporary files are created and cleaned up properly.
        - The original and modified test commands are stored correctly in the configuration.

        Args:
            mock_open_file (MagicMock): Mock for the `open` function to simulate file operations.
            mock_copy (MagicMock): Mock for `shutil.copy` to simulate file copying.
            mock_isdir (MagicMock): Mock for `os.path.isdir` to simulate directory existence.
            mock_isfile (MagicMock): Mock for `os.path.isfile` to simulate file existence.
        """
        with (
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_output_file,
        ):
            # Create a relative path for the test file
            rel_path = "tests/test_output.py"

            args = argparse.Namespace(
                source_file_path=temp_source_file.name,
                test_file_path=temp_test_file.name,
                project_root="/project/root",
                test_file_output_path="/project/root/" + rel_path,
                code_coverage_report_path="coverage_report.xml",
                test_command="pytest --cov=myapp --cov-report=xml",
                test_command_dir=os.getcwd(),
                included_files=None,
                coverage_type="cobertura",
                report_filepath="test_results.html",
                desired_coverage=90,
                max_iterations=10,
                additional_instructions="",
                model="openai/test-model",
                api_base="openai/test-api",
                use_report_coverage_feature_flag=False,
                log_db_path="",
                diff_coverage=False,
                branch="main",
                run_tests_multiple_times=1,
                run_each_test_separately=True,
                max_run_time_sec=30,
                record_mode=False,
                disable_file_generation=False,
                suppress_log_files=False,
            )

            config = self.create_config_from_args(args)
            agent = CoverAgent(config)  # Create CoverAgent instance to trigger command modification

            # Verify the test command was modified correctly
            assert agent.config.test_command == "pytest tests/test_output.py --cov=myapp --cov-report=xml"
            assert agent.config.test_command_original == "pytest --cov=myapp --cov-report=xml"

            # Clean up temporary files
            os.remove(temp_source_file.name)
            os.remove(temp_test_file.name)
            os.remove(temp_output_file.name)
