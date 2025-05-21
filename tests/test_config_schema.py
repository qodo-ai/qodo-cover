import os

from argparse import Namespace
from unittest.mock import patch

import pytest

from cover_agent.settings.config_schema import CoverAgentConfig, CoverageType


class TestCoverAgentConfig:
    """Test suite for CoverAgentConfig class and CoverageType enum."""

    @pytest.fixture
    def sample_args(self):
        """Fixture providing sample command line arguments."""
        return Namespace(
            source_file_path="src/main.py",
            test_file_path="tests/test_main.py",
            project_root="/project",
            test_file_output_path="tests/generated_test.py",
            code_coverage_report_path="coverage.xml",
            test_command="pytest",
            test_command_dir="/project/tests",
            included_files=["src/main.py"],
            coverage_type=CoverageType.COBERTURA,
            report_filepath="report.html",
            desired_coverage=90,
            max_iterations=10,
            max_run_time_sec=300,
            additional_instructions="",
            model="gpt-3.5-turbo",
            api_base="",
            strict_coverage=False,
            run_tests_multiple_times=1,
            log_db_path="logs.db",
            branch="main",
            use_report_coverage_feature_flag=False,
            diff_coverage=False,
            run_each_test_separately=False,
            record_mode=False,
            suppress_log_files=False,
            max_test_files_allowed_to_analyze=20,
            look_for_oldest_unchanged_test_file=False,
            project_language="python",
        )

    def test_coverage_type_enum(self):
        """Test CoverageType enum values."""
        assert CoverageType.LCOV.value == "lcov"
        assert CoverageType.COBERTURA.value == "cobertura"
        assert CoverageType.JACOCO.value == "jacoco"

    def test_config_initialization(self, sample_args):
        """
        Test the initialization of the CoverAgentConfig class.

        This test ensures that the CoverAgentConfig object is correctly initialized
        with the provided arguments and that all attributes are set to their expected values.

        Args:
            self: The test class instance.
            sample_args (Namespace): A fixture providing sample command line arguments.

        Assertions:
            - Verifies that the `source_file_path` attribute matches the expected value.
            - Verifies that the `test_file_path` attribute matches the expected value.
            - Verifies that the `project_root` attribute matches the expected value.
            - Verifies that the `test_command` attribute matches the expected value.
            - Verifies that the `coverage_type` attribute matches the expected value.
            - Verifies that the `test_command_original` attribute is initialized as None.
        """
        config = CoverAgentConfig(**vars(sample_args))

        assert config.source_file_path == "src/main.py"
        assert config.test_file_path == "tests/test_main.py"
        assert config.project_root == "/project"
        assert config.test_command == "pytest"
        assert config.coverage_type == CoverageType.COBERTURA
        assert config.test_command_original is None
        assert config.use_report_coverage_feature_flag is False
        assert config.project_language == "python"

    @patch.dict(os.environ, {"LOG_DB_PATH": "/custom/logs.db"})
    def test_from_cli_args_with_env_var(self, sample_args):
        """
        Test the from_cli_args method when an environment variable is set.

        This test ensures that the `from_cli_args` method correctly prioritizes
        environment variables over CLI arguments when initializing the configuration.

        Args:
            self: The test class instance.
            sample_args (Namespace): A fixture providing sample command line arguments.

        Assertions:
            - Verifies that the `log_db_path` attribute is set to the value from the environment variable.
            - Verifies that the `source_file_path` attribute matches the value from the CLI arguments.
            - Verifies that the `coverage_type` attribute matches the value from the CLI arguments.
        """
        config = CoverAgentConfig.from_cli_args(sample_args)

        assert config.log_db_path == "/custom/logs.db"
        assert config.source_file_path == sample_args.source_file_path
        assert config.coverage_type == sample_args.coverage_type

    def test_from_cli_args_without_env_var(self, sample_args):
        """
        Test the from_cli_args method when no environment variables are set.

        This test ensures that the `from_cli_args` method correctly uses the CLI arguments
        to initialize the configuration when no relevant environment variables are present.

        Args:
            self: The test class instance.
            sample_args (Namespace): A fixture providing sample command line arguments.

        Assertions:
            - Verifies that the `log_db_path` attribute is set to the default value from the CLI arguments.
            - Verifies that the `test_command` attribute matches the value from the CLI arguments.
        """
        with patch.dict(os.environ, {}, clear=True):
            config = CoverAgentConfig.from_cli_args(sample_args)

            assert config.log_db_path == "logs.db"
            assert config.test_command == "pytest"

    @patch("cover_agent.settings.config_schema.get_settings")
    def test_from_cli_args_with_defaults(self, mock_get_settings, sample_args):
        """
        Test the from_cli_args_with_defaults method with default settings.

        This test ensures that the `from_cli_args_with_defaults` method correctly initializes
        the configuration by using default settings when certain CLI arguments are not provided.

        Args:
            self: The test class instance.
            mock_get_settings (MagicMock): Mocked `get_settings` function to provide default settings.
            sample_args (Namespace): A fixture providing sample command line arguments.

        Setup:
            - Mocks the `get_settings` function to return a dictionary of default configuration values.
            - Modifies `sample_args` to set some attributes to `None` to test fallback to defaults.

        Assertions:
            - Verifies that CLI arguments override the default settings.
            - Verifies that default settings are used for attributes set to `None` in the CLI arguments.
        """
        mock_default_config = {
            "source_file_path": "default_src.py",
            "test_file_path": "default_test.py",
            "project_root": "/default/project",
            "test_file_output_path": "default_output.py",
            "code_coverage_report_path": "default_coverage.xml",
            "test_command": "python -m pytest",
            "test_command_dir": "/default/tests",
            "included_files": None,
            "coverage_type": "cobertura",
            "report_filepath": "default_report.html",
            "desired_coverage": 80,
            "max_iterations": 5,
            "max_run_time_sec": 600,
            "additional_instructions": "default instructions",
            "model": "default-model",
            "api_base": "default-api",
            "strict_coverage": True,
            "run_tests_multiple_times": 2,
            "log_db_path": "default_logs.db",
            "branch": "develop",
            "use_report_coverage_feature_flag": True,
            "diff_coverage": True,
            "run_each_test_separately": True,
            "record_mode": True,
            "suppress_log_files": True,
        }

        mock_get_settings.return_value = {"default": mock_default_config}

        # Create args with some values as None to test default fallback
        modified_args = sample_args
        modified_args.model = None
        modified_args.api_base = None

        config = CoverAgentConfig.from_cli_args_with_defaults(modified_args)

        # Check that CLI args override defaults
        assert config.source_file_path == sample_args.source_file_path
        assert config.test_file_path == sample_args.test_file_path

        # Check that defaults are used for None values
        assert config.model == mock_default_config["model"]
        assert config.api_base == mock_default_config["api_base"]

    @patch("cover_agent.settings.config_schema.get_settings")
    def test_from_cli_args_with_defaults_empty_settings(self, mock_get_settings, sample_args):
        """
        Test the from_cli_args_with_defaults method with empty default settings.

        This test ensures that the `from_cli_args_with_defaults` method correctly initializes
        the configuration using only the CLI arguments when the default settings are empty.

        Args:
            self: The test class instance.
            mock_get_settings (MagicMock): Mocked `get_settings` function to provide empty default settings.
            sample_args (Namespace): A fixture providing sample command line arguments.

        Setup:
            - Mocks the `get_settings` function to return an empty dictionary for default settings.

        Assertions:
            - Verifies that the `source_file_path` attribute matches the value from the CLI arguments.
            - Verifies that the `test_file_path` attribute matches the value from the CLI arguments.
            - Verifies that the `project_root` attribute matches the value from the CLI arguments.
        """
        mock_get_settings.return_value = {"default": {}}

        config = CoverAgentConfig.from_cli_args_with_defaults(sample_args)

        assert config.source_file_path == sample_args.source_file_path
        assert config.test_file_path == sample_args.test_file_path
        assert config.project_root == sample_args.project_root
