"""
This script runs all tests sequentially using Docker. It's intended to be run from the command line manually.
It accepts command line arguments and produces extensive logging output and LLM streams.
"""

import argparse
import os

from dotenv import load_dotenv

from cover_agent.custom_logger import CustomLogger
from cover_agent.settings.config_loader import get_settings
from tests_integration.run_test_with_docker import run_test
from tests_integration.scenarios import TESTS


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def main():
    settings = get_settings().get("default")

    parser = argparse.ArgumentParser(description="Args for running tests with Docker.")

    arg_definitions = [
        (
            "--model",
            dict(type=str, default=settings.get("model"), help="Which LLM model to use. Default: %(default)s."),
        ),
        ("--record-mode", dict(action="store_true", help="Enable record mode for LLM responses. Default: False.")),
        (
            "--suppress-log-files",
            dict(action="store_true", help="Suppress all generated log files (HTML, logs, DB files)."),
        ),
    ]

    for name, kwargs in arg_definitions:
        parser.add_argument(name, **kwargs)

    args = parser.parse_args()

    # Run all tests sequentially
    for test in TESTS:
        test_args = argparse.Namespace(
            dockerfile=test.get("docker_file_path", ""),
            docker_image=test["docker_image"],
            source_file_path=test["source_file_path"],
            test_file_path=test["test_file_path"],
            test_command=test["test_command"],
            coverage_type=test.get("coverage_type", settings.get("coverage_type")),
            code_coverage_report_path=test.get("code_coverage_report_path", "coverage.xml"),
            model=args.model or test.get("model"),
            desired_coverage=test.get("desired_coverage", settings.get("desired_coverage")),
            max_iterations=test.get("max_iterations", settings.get("max_iterations")),
            max_run_time_sec=test.get("max_run_time_sec", settings.get("max_run_time_sec")),
            api_base=settings.get("api_base", ""),
            log_db_path=settings.get("log_db_path", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            record_mode=args.record_mode,
            suppress_log_files=test.get("suppress_log_files", args.suppress_log_files),
        )
        run_test(test_args)


if __name__ == "__main__":
    main()
