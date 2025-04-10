import argparse
import os
import sys

import docker
from dotenv import load_dotenv


from cover_agent.CustomLogger import CustomLogger
import tests_integration.constants as constants
from tests_integration.docker_utils import (
    clean_up_docker_container,
    copy_file_to_docker_container,
    get_docker_image,
    run_command_in_docker_container,
    run_docker_container,
)


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def run_test(test_args: argparse.Namespace) -> None:
    client = docker.from_env()

    logger.info("===== Running test with Docker and these args =====")
    log_test_args(test_args)

    if not test_args.source_file_path or not test_args.test_file_path or not test_args.test_command:
        logger.error("Missing required parameters: --source-file-path, --test-file-path, or --test-command.")
        sys.exit(1)

    if not test_args.dockerfile and not test_args.docker_image:
        logger.error("Missing required parameters: either --dockerfile or --docker-image must be provided.")
        sys.exit(1)

    image_tag = get_docker_image(client, test_args.dockerfile, test_args.docker_image)
    container_env = {}

    if test_args.openai_api_key:
        container_env["OPENAI_API_KEY"] = test_args.openai_api_key

    if test_args.anthropic_api_key:
        container_env["ANTHROPIC_API_KEY"] = test_args.anthropic_api_key

    container_volumes = {}

    if test_args.log_db_path:
        log_db_name = os.path.basename(test_args.log_db_path)
        container_volumes[test_args.log_db_path] = {"bind": f"/{log_db_name}", "mode": "rw"}

    container = run_docker_container(client, image_tag, container_volumes, container_env=container_env)
    copy_file_to_docker_container(container, "dist/cover-agent", "/usr/local/bin/cover-agent")

    command = [
        "/usr/local/bin/cover-agent",
        "--source-file-path", test_args.source_file_path,
        "--test-file-path", test_args.test_file_path,
        "--code-coverage-report-path", test_args.code_coverage_report_path,
        "--test-command", test_args.test_command,
        "--coverage-type", test_args.coverage_type,
        "--desired-coverage", str(test_args.desired_coverage),
        "--max-iterations", str(test_args.max_iterations),
        "--max-run-time", str(test_args.max_run_time),
        "--strict-coverage",
    ]

    if test_args.model:
        command.extend(["--model", test_args.model])

    if test_args.api_base:
        command.extend(["--api-base", test_args.api_base])

    if test_args.log_db_path:
        log_db_name = os.path.basename(test_args.log_db_path)
        command.extend(["--log-db-path", f"/{log_db_name}"])

    exec_env = {}

    if test_args.openai_api_key:
        exec_env["OPENAI_API_KEY"] = test_args.openai_api_key

    if test_args.anthropic_api_key:
        exec_env["ANTHROPIC_API_KEY"] = test_args.anthropic_api_key

    run_command_in_docker_container(container, command, exec_env)

    clean_up_docker_container(container)


def log_test_args(test_args: argparse.Namespace, max_value_len=60) -> None:
    exclude_keys = ("openai_api_key", "anthropic_api_key")
    for key, value in vars(test_args).items():
        if key in exclude_keys:
            continue

        value_str = str(value)
        if len(value_str) > max_value_len:
            value_str = f"{value_str[:max_value_len]}..."
        logger.info(f"{key:30}: {value_str}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test with Docker.")
    parser.add_argument(
        "--source-file-path", required=True, help="Path to the source file."
    )
    parser.add_argument(
        "--test-file-path", required=True, help="Path to the input test file."
    )
    parser.add_argument(
        "--code-coverage-report-path",
        required=True,
        help="Path to the code coverage report file.",
    )
    parser.add_argument(
        "--test-command",
        required=True,
        help="The command to run tests and generate coverage report.",
    )
    parser.add_argument(
        "--coverage-type",
        default="cobertura",
        help="Type of coverage report.",
    )
    parser.add_argument(
        "--desired-coverage",
        type=int,
        default=constants.DESIRED_COVERAGE,
        help="The desired coverage percentage.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=constants.MAX_ITERATIONS,
        help="The maximum number of iterations.",
    )
    parser.add_argument(
        "--model",
        default=constants.MODEL,
        help="Which LLM model to use.",
    )
    parser.add_argument(
        "--api-base",
        default=constants.API_BASE,
        help="The API url to use for Ollama or Hugging Face.",
    )
    parser.add_argument(
        "--log-db-path",
        default=os.getenv("LOG_DB_PATH", ""),
        help="Path to optional log database.",
    )

    parser.add_argument(
        "--dockerfile",
        default="",
        help="Path to Dockerfile.",
    )
    parser.add_argument(
        "--docker-image",
        default="",
        help="Docker image name.",
    )
    parser.add_argument(
        "--openai-api-key",
        default=os.getenv("OPENAI_API_KEY", ""),
        help="OpenAI API key.",
    )
    parser.add_argument(
        "--anthropic-api-key",
        default=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Anthropic API key.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_test(args)
