import os
import pytest
from argparse import Namespace
from dotenv import load_dotenv

from cover_agent.CustomLogger import CustomLogger
from cover_agent.settings.config_loader import get_settings
from tests_integration.run_test_with_docker import run_test
from tests_integration.scenarios import TESTS

load_dotenv()
logger = CustomLogger.get_logger(__name__)

SETTINGS = get_settings().get("default")


def get_test_args(test_config: dict, pytest_config) -> Namespace:
    """Create test arguments namespace from test configuration and pytest options."""
    return Namespace(
        dockerfile=test_config.get("docker_file_path", ""),
        docker_image=test_config["docker_image"],
        source_file_path=test_config["source_file_path"],
        test_file_path=test_config["test_file_path"],
        test_command=test_config["test_command"],
        coverage_type=test_config.get("coverage_type", SETTINGS.get("coverage_type")),
        code_coverage_report_path=test_config.get("code_coverage_report_path", "coverage.xml"),
        model=pytest_config.getoption("--model") or test_config.get("model"),
        desired_coverage=test_config.get("desired_coverage", SETTINGS.get("desired_coverage")),
        max_iterations=test_config.get("max_iterations", SETTINGS.get("max_iterations")),
        max_run_time_sec=test_config.get("max_run_time_sec", SETTINGS.get("max_run_time_sec")),
        api_base=SETTINGS.get("api_base", ""),
        log_db_path=SETTINGS.get("log_db_path", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        record_mode=pytest_config.getoption("--record-mode"),
        suppress_log_files=test_config.get("suppress_log_files", pytest_config.getoption("--suppress-log-files")),
    )


def get_test_id(test_config):
    """Generate a readable test ID from the test configuration."""
    image_name = test_config["docker_image"].split("/")[-1].split(":")[0]
    source_file = test_config["source_file_path"].split("/")[-1]
    return f"{image_name}-{source_file}"


@pytest.mark.parametrize("test_config", TESTS, ids=get_test_id)
def test_docker_scenario(test_config, pytestconfig, test_model):
    """
    Execute Docker-based test scenarios using parameterization.

    Args:
        test_config: Dictionary containing test configuration from scenarios.py
        pytestconfig: Pytest configuration object containing command line options
        test_model: Model name from command line option
    """
    logger.info(f"Running test scenario for {test_config['docker_image']}")
    test_args = get_test_args(test_config, pytestconfig)
    run_test(test_args)
