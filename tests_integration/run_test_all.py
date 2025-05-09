import argparse
import os

from dotenv import load_dotenv

from cover_agent import constants
from cover_agent.CustomLogger import CustomLogger
from tests_integration.run_test_with_docker import run_test
from tests_integration.scenarios import TESTS


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Args for running tests with Docker.")
    parser.add_argument("--model", default=constants.MODEL, help="Which LLM model to use.")
    parser.add_argument("--record-mode", action="store_true", help="Enable LLM responses record mode for tests.")
    args = parser.parse_args()

    model = args.model
    record_mode = args.record_mode

    # Run all tests sequentially
    for test in TESTS:
        test_args = argparse.Namespace(
            record_mode=record_mode,
            docker_image=test["docker_image"],
            source_file_path=test["source_file_path"],
            test_file_path=test["test_file_path"],
            code_coverage_report_path=test.get("code_coverage_report_path", "coverage.xml"),
            test_command=test["test_command"],
            coverage_type=test.get("coverage_type", constants.CoverageType.COBERTURA.value),
            max_iterations=test.get("max_iterations", constants.MAX_ITERATIONS),
            desired_coverage=test.get("desired_coverage", constants.DESIRED_COVERAGE),
            model=test.get("model", model),
            api_base=os.getenv("API_BASE", ""),
            max_run_time=test.get("max_run_time", constants.MAX_RUN_TIME_SEC),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            dockerfile=test.get("docker_file_path", ""),
            log_db_path=os.getenv("LOG_DB_PATH", ""),
        )
        run_test(test_args)


if __name__ == "__main__":
    main()
