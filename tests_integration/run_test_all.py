import argparse
import os

from dotenv import load_dotenv

import tests_integration.constants as constants

from cover_agent.CustomLogger import CustomLogger
from tests_integration.run_test_with_docker import run_test
from tests_integration.scenarios import TESTS


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Args for running tests with Docker.")
    parser.add_argument("--model", default=constants.MODEL, help="Which LLM model to use.")
    args = parser.parse_args()

    model = args.model

    # Run all tests sequentially
    for test in TESTS:
        test_args = argparse.Namespace(
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
            max_run_time=test.get("max_run_time", constants.MAX_RUN_TIME),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            dockerfile=test.get("docker_file_path", ""),
            log_db_path=os.getenv("LOG_DB_PATH", ""),
        )
        run_test(test_args)


if __name__ == "__main__":
    main()
