import argparse
import os

from dotenv import load_dotenv

from cover_agent.CustomLogger import CustomLogger
from tests_integration.run_test_with_docker import run_test
from tests_integration.scenarios import TESTS
from cover_agent.settings.config_loader import get_settings
from cover_agent.settings.config_schema import CoverageType


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def main():
    settings = get_settings().get("default")

    parser = argparse.ArgumentParser(description="Args for running tests with Docker.")
    parser.add_argument("--model", default=settings.model, help="Which LLM model to use.")
    parser.add_argument("--record-mode", action="store_true", help="Enable LLM responses record mode for tests.")
    parser.add_argument(
        "--suppress-log-files",
        default=False,
        action="store_true",
        help="Suppress all generated log files (HTML, logs, DB files).",
    )
    args = parser.parse_args()

    model = args.model
    record_mode = args.record_mode

    # Run all tests sequentially
    for test in TESTS:
        suppress_log_files = test.get("suppress_log_files", False)
        test_args = argparse.Namespace(
            record_mode=record_mode,
            docker_image=test["docker_image"],
            source_file_path=test["source_file_path"],
            test_file_path=test["test_file_path"],
            code_coverage_report_path=test.get("code_coverage_report_path", "coverage.xml"),
            test_command=test["test_command"],
            coverage_type=test.get("coverage_type", CoverageType.COBERTURA.value),
            max_iterations=test.get("max_iterations", settings.get("max_iterations")),
            desired_coverage=test.get("desired_coverage", settings.get("desired_coverage")),
            model=test.get("model", model),
            api_base=os.getenv("API_BASE", ""),
            max_run_time_sec=test.get("max_run_time_sec", settings.get("max_run_time_sec")),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            dockerfile=test.get("docker_file_path", ""),
            log_db_path=os.getenv("LOG_DB_PATH", ""),
            suppress_log_files=test.get("suppress_log_files", args.suppress_log_files),
        )
        run_test(test_args)


if __name__ == "__main__":
    main()
