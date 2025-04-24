import argparse
import os

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


class InvalidTestArgsError(Exception):
    """Raised when required test arguments are missing."""


def run_test(test_args: argparse.Namespace) -> None:
    """
    Executes a test inside a Docker container using the provided arguments.

    This function validates the test arguments, sets up the Docker container environment,
    and runs the specified test command inside the container. It also handles errors
    and ensures proper cleanup of the Docker container.

    Args:
        test_args (argparse.Namespace): The arguments required to configure and run the test.
                                         These include paths, Docker configuration, and API keys.

    Raises:
        InvalidTestArgsError: If required test arguments are missing or invalid.
        Exception: For any other errors encountered during test execution.

    Example:
        args = parse_args()
        run_test(args)
    """
    client = docker.from_env()
    container = None

    logger.info("=========== Running test with Docker and these args ================")
    log_test_args(test_args)

    try:
        validate_test_args(test_args)
        container_env = compose_container_env(test_args)
        container_volumes = compose_container_volumes(test_args)
        command = compose_test_command(test_args)
        exec_env = {
            key: value for key, value in container_env.items()
            if key in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
        }

        image_tag = get_docker_image(client, test_args.dockerfile, test_args.docker_image)
        container = run_docker_container(client, image_tag, container_volumes, container_env=container_env)
        copy_file_to_docker_container(container, "dist/cover-agent", "/usr/local/bin/cover-agent")
        run_command_in_docker_container(container, command, exec_env)
    except InvalidTestArgsError as e:
        logger.error(f"Invalid cover-agent arguments: {e}")
        return
    except Exception as e:
        logger.error(f"Error during test execution: {e}")
        raise
    finally:
        if container:
            clean_up_docker_container(container)


def validate_test_args(test_args: argparse.Namespace) -> None:
    """
    Validates the test arguments provided for running a Docker-based test.

    This function checks if the required arguments for the test are present and valid.
    If any required argument is missing, it raises an `InvalidTestArgsError`.

    Args:
        test_args (argparse.Namespace): The arguments required for the test, including
                                         file paths, Docker configuration, and test commands.

    Raises:
        InvalidTestArgsError: If any of the required arguments are missing or invalid.
    """
    if not test_args.source_file_path or not test_args.test_file_path or not test_args.test_command:
        msg = "Missing required parameters: --source-file-path, --test-file-path, or --test-command."
        logger.error(msg)
        raise InvalidTestArgsError(msg)

    if not test_args.dockerfile and not test_args.docker_image:
        msg = "Missing required parameters: either --dockerfile or --docker-image must be provided."
        logger.error(msg)
        raise InvalidTestArgsError(msg)


def compose_container_env(test_args: argparse.Namespace) -> dict:
    """
    Composes the environment variables for the Docker container.

    This function creates a dictionary of environment variables to be passed to the Docker container
    based on the provided test arguments. It includes API keys if they are specified.

    Args:
        test_args (argparse.Namespace): The arguments containing the environment configuration,
                                         including optional API keys.

    Returns:
        dict: A dictionary of environment variables to be used in the Docker container.
              Keys are the variable names, and values are their corresponding values.
    """
    env = {}
    if test_args.openai_api_key:
        env["OPENAI_API_KEY"] = test_args.openai_api_key
    if test_args.anthropic_api_key:
        env["ANTHROPIC_API_KEY"] = test_args.anthropic_api_key
    return env


def compose_container_volumes(test_args: argparse.Namespace) -> dict:
    """
    Composes the volume mappings for the Docker container.

    This function creates a dictionary of volume bindings to be passed to the Docker container
    based on the provided test arguments. If a log database path is specified, it is added
    to the volume mappings.

    Args:
        test_args (argparse.Namespace): The arguments containing the volume configuration,
                                         including the optional log database path.

    Returns:
        dict: A dictionary where keys are host paths and values are dictionaries specifying
              the bind path and access mode inside the container.
    """
    volumes = {}
    if test_args.log_db_path:
        log_db_name = os.path.basename(test_args.log_db_path)
        volumes[test_args.log_db_path] = {
            "bind": f"/{log_db_name}",
            "mode": "rw"
        }
    return volumes


def compose_test_command(test_args: argparse.Namespace) -> list:
    """
    Composes the test command to be executed inside the Docker container.

    This function generates a list of command-line arguments for the `cover-agent` tool
    based on the provided test arguments. It includes mandatory arguments such as file paths,
    test commands, and coverage settings, as well as optional arguments like model, API base,
    and log database path.

    Args:
        test_args (argparse.Namespace): The arguments required to configure the test command,
                                         including file paths, coverage settings, and optional parameters.

    Returns:
        list: A list of strings representing the command-line arguments for the `cover-agent` tool.
    """
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

    return command


def log_test_args(test_args: argparse.Namespace, max_value_len=60) -> None:
    """
    Logs the test arguments, excluding sensitive information.

    This function iterates through the provided test arguments and logs their key-value pairs.
    Sensitive keys, such as API keys, are excluded from logging. If a value exceeds the
    specified maximum length, it is truncated and appended with ellipses.

    Args:
        test_args (argparse.Namespace): The arguments to be logged.
        max_value_len (int): The maximum length of the value to be logged. Defaults to 60.

    Excludes:
        - "openai_api_key"
        - "anthropic_api_key"
    """
    exclude_keys = ("openai_api_key", "anthropic_api_key")
    for key, value in vars(test_args).items():
        if key in exclude_keys:
            continue

        value_str = str(value)
        if len(value_str) > max_value_len:
            value_str = f"{value_str[:max_value_len]}..."
        logger.info(f"{key:30}: {value_str}")


def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for configuring and running tests with Docker.

    This function defines and parses the required and optional arguments needed
    to execute tests inside a Docker container. It includes arguments for file paths,
    Docker configuration, API keys, and other test-related settings.

    Returns:
        argparse.Namespace: An object containing the parsed arguments as attributes.
                            Each attribute corresponds to a command-line argument.

    Command-line Arguments:
        --source-file-path (str, required): Path to the source file.
        --test-file-path (str, required): Path to the input test file.
        --code-coverage-report-path (str, required): Path to the code coverage report file.
        --test-command (str, required): The command to run tests and generate coverage report.
        --coverage-type (str, optional): Type of coverage report. Defaults to "cobertura".
        --desired-coverage (int, optional): The desired coverage percentage. Defaults to a constant.
        --max-iterations (int, optional): The maximum number of iterations. Defaults to a constant.
        --model (str, optional): Which LLM model to use. Defaults to a constant.
        --api-base (str, optional): The API URL to use for Ollama or Hugging Face. Defaults to a constant.
        --log-db-path (str, optional): Path to an optional log database. Defaults to an environment variable.
        --dockerfile (str, optional): Path to the Dockerfile. Defaults to an empty string.
        --docker-image (str, optional): Docker image name. Defaults to an empty string.
        --openai-api-key (str, optional): OpenAI API key. Defaults to an environment variable.
        --anthropic-api-key (str, optional): Anthropic API key. Defaults to an environment variable.
    """
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
