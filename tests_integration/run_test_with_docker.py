import argparse
import os
import sys

from pathlib import Path

import docker

from dotenv import load_dotenv
from dynaconf import Dynaconf

from cover_agent.custom_logger import CustomLogger
from cover_agent.main import parse_args
from cover_agent.settings.config_loader import get_settings
from tests_integration.docker_utils import (
    clean_up_docker_container,
    copy_file_to_docker_container,
    get_docker_image,
    get_docker_image_workdir,
    get_short_docker_image_name,
    run_command_in_docker_container,
    run_docker_container,
)


load_dotenv()
logger = CustomLogger.get_logger(__name__)

SETTINGS = get_settings().get("default")


class InvalidTestArgsError(Exception):
    """Raised when required test arguments are missing."""


def run_test(test_args: argparse.Namespace) -> None:
    """
    Executes a test inside a Docker container using the provided arguments.

    Args:
        test_args: Configuration for the test run including paths and Docker settings.

    Raises:
        InvalidTestArgsError: If required arguments are missing.
        Exception: For any other errors during execution.
    """
    logger.info("=========== Running test with Docker and these args ================")
    log_test_args(test_args)
    logger.info("====================================================================")

    client = docker.from_env()
    container = None

    try:
        validate_test_args(test_args)

        image_tag = get_docker_image(client, test_args.dockerfile, test_args.docker_image)
        container_config = prepare_container_config(test_args, image_tag, client)

        container = run_docker_container(
            client,
            image_tag,
            container_config["volumes"],
            container_env=container_config["env"],
        )

        execute_test_in_container(container, container_config["command"], container_config["exec_env"])
    except InvalidTestArgsError as e:
        logger.error(f"Invalid cover-agent arguments: {e}")
        return
    except Exception as e:
        logger.error(f"Error during test execution: {e}")
        raise
    finally:
        if container:
            clean_up_docker_container(container)


def prepare_container_config(test_args: argparse.Namespace, image_tag: str, client: docker.DockerClient) -> dict:
    """
    Prepares the configuration for a Docker container.

    This function generates the environment variables, volume mappings, and command
    required to run a Docker container based on the provided test arguments. It also
    handles additional configuration for record mode if enabled.

    Args:
        test_args (argparse.Namespace): The arguments required to configure the container,
                                         including paths, Docker settings, and environment variables.
        image_tag (str): The tag of the Docker image to be used for the container.
        client (docker.DockerClient): The Docker client instance used to interact with Docker.

    Returns:
        dict: A dictionary containing the following keys:
            - "volumes" (dict): Volume mappings for the container.
            - "env" (dict): Environment variables for the container.
            - "command" (list): The command to be executed inside the container.
            - "exec_env" (dict): A subset of environment variables for executing the test command.
    """
    container_env = compose_container_env(test_args)
    container_volumes = compose_container_volumes(test_args)

    container_volumes.update(prepare_record_mode_volume(test_args, image_tag, client))

    test_name = get_short_docker_image_name(test_args.docker_image)
    logger.info(f"Test name: {test_name}")
    container_env.update({"TEST_NAME": test_name})

    return {
        "volumes": container_volumes,
        "env": container_env,
        "command": compose_test_command(test_args),
        "exec_env": {k: v for k, v in container_env.items() if k in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}},
    }


def prepare_record_mode_volume(test_args: argparse.Namespace, image_tag: str, client: docker.DockerClient) -> dict:
    """
    Prepares the volume configuration for record mode in a Docker container.

    This function determines the working directory of the Docker image, constructs
    the paths for binding a folder inside the container to a local folder, and logs
    the binding information. The volume mapping is then returned for use in the
    container configuration.

    Args:
        test_args (argparse.Namespace): The arguments required for the test, including
                                         paths and record mode settings.
        image_tag (str): The tag of the Docker image to inspect for the working directory.
        client (docker.DockerClient): The Docker client instance used to interact with Docker.

    Returns:
        dict: A dictionary representing the volume mapping. The key is the host folder path,
              and the value is a dictionary specifying the bind path and access mode inside
              the container.
    """
    container_workdir = get_docker_image_workdir(client, image_tag)
    bind_folder = f"{container_workdir}/{SETTINGS.responses_folder}"
    host_folder_path = f"{Path(__file__).resolve().parents[1]}/{SETTINGS.responses_folder}"

    logger.info(
        f"Binding a container folder {bind_folder} to local folder {host_folder_path} for storing "
        f"recorded LLM responses..."
    )

    return {host_folder_path: {"bind": bind_folder, "mode": "rw"}}


def execute_test_in_container(container, command: list, exec_env: dict) -> None:
    """
    Executes a test command inside a Docker container.

    This function copies the `cover-agent` binary to the container and runs the specified
    test command within the container using the provided execution environment.

    Args:
        container: The Docker container instance where the test will be executed.
        command (list): The command to be executed inside the container.
        exec_env (dict): A dictionary of environment variables to be used during the command execution.

    Returns:
        None
    """
    copy_file_to_docker_container(container, SETTINGS.cover_agent_host_folder, SETTINGS.cover_agent_container_folder)
    run_command_in_docker_container(container, command, exec_env)


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
        volumes[test_args.log_db_path] = {"bind": f"/{log_db_name}", "mode": "rw"}
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
        "--source-file-path",
        test_args.source_file_path,
        "--test-file-path",
        test_args.test_file_path,
        "--code-coverage-report-path",
        test_args.code_coverage_report_path,
        "--test-command",
        test_args.test_command,
        "--coverage-type",
        test_args.coverage_type,
        "--desired-coverage",
        str(test_args.desired_coverage),
        "--max-iterations",
        str(test_args.max_iterations),
        "--max-run-time-sec",
        str(test_args.max_run_time_sec),
        "--strict-coverage",
    ]

    if test_args.model:
        command.extend(["--model", test_args.model])

    if test_args.api_base:
        command.extend(["--api-base", test_args.api_base])

    if test_args.log_db_path:
        log_db_name = os.path.basename(test_args.log_db_path)
        command.extend(["--log-db-path", f"{log_db_name}"])

    if test_args.record_mode:
        command.extend(["--record-mode"])

    if test_args.suppress_log_files:
        command.extend(["--suppress-log-files"])
        logger.info("Suppressed all generated log files for this test run.")

    return command


def log_test_args(test_args: argparse.Namespace, max_value_len=65) -> None:
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
        logger.info(f"{key:35}: {value_str}")


def parse_extra_args(settings: Dynaconf) -> argparse.Namespace:
    """
    Parses additional command-line arguments specific to Docker and combines them with base arguments.

    This function first defines and parses Docker-specific arguments, then uses the `parse_args` function
    to parse the base arguments. The two sets of arguments are combined into a single `argparse.Namespace`.

    Args:
        settings (Dynaconf): Configuration settings object used for parsing base arguments.

    Returns:
        argparse.Namespace: A namespace containing both base and Docker-specific arguments.
    """
    logger.info("Starting to parse extra arguments...")
    parent_args_parser = argparse.ArgumentParser(add_help=False)
    extra_args_parser = argparse.ArgumentParser(parents=[parent_args_parser])

    extra_args_definitions = [
        ("--dockerfile", dict(type=str, default="", help="Path to Dockerfile.")),
        ("--docker-image", dict(type=str, default="", help="Docker image name.")),
        ("--openai-api-key", dict(type=str, default=os.getenv("OPENAI_API_KEY", ""), help="OpenAI API key.")),
        ("--anthropic-api-key", dict(type=str, default=os.getenv("ANTHROPIC_API_KEY", ""), help="Anthropic API key.")),
    ]

    for name, kwargs in extra_args_definitions:
        extra_args_parser.add_argument(name, **kwargs)

    extra_args, base_args = extra_args_parser.parse_known_args()

    # Set up sys.argv for base args parsing
    original_argv = sys.argv
    sys.argv = [sys.argv[0]] + base_args
    logger.info(f"Modified sys.argv for base argument parsing: {sys.argv}.")

    try:
        base_args = parse_args(settings)
        logger.info("Base arguments successfully parsed.")

        # Combine both sets of args
        combined_dict = {**vars(base_args), **vars(extra_args)}
        logger.info("Successfully combined Docker-specific and base arguments.")
        return argparse.Namespace(**combined_dict)
    finally:
        # Restore original argv
        logger.debug(f"Restoring original sys.argv: {original_argv}...")
        sys.argv = original_argv


if __name__ == "__main__":
    args = parse_extra_args(SETTINGS)
    run_test(args)
