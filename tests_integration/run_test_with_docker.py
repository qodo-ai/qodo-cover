import argparse
import io
import os
import sys
import tarfile

from typing import Any

import docker
from docker.errors import APIError, BuildError, DockerException
from docker.models.containers import Container
from dotenv import load_dotenv

import tests_integration.constants as constants
from cover_agent.CustomLogger import CustomLogger


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

    image_tag = build_or_pull_docker_image(client, test_args.dockerfile, test_args.docker_image)
    container_env = {}

    if test_args.openai_api_key:
        container_env["OPENAI_API_KEY"] = test_args.openai_api_key

    if test_args.anthropic_api_key:
        container_env["ANTHROPIC_API_KEY"] = test_args.anthropic_api_key

    container_volumes = {}

    if test_args.log_db_path:
        log_db_name = os.path.basename(test_args.log_db_path)
        container_volumes[test_args.log_db_path] = {"bind": f"/{log_db_name}", "mode": "rw"}

    container = run_docker_container(client, image_tag, container_env, container_volumes)
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


def build_or_pull_docker_image(client: docker.DockerClient, dockerfile: str, docker_image: str) -> str:
    image_tag = "cover-agent-image"

    try:
        if dockerfile:
            logger.info(f"Building the Docker image {docker_image}...")
            dockerfile_dir = os.path.dirname(dockerfile) or "."
            with open(dockerfile, "r") as df:
                image, logs = client.images.build(
                    path=dockerfile_dir,
                    dockerfile=os.path.basename(dockerfile),
                    tag=image_tag,
                    rm=True,
                )

            for log in logs:
                if "stream" in log:
                    print(log["stream"], end="")
        else:
            logger.info(f"Pulling Docker image: {docker_image} ...")
            progress_by_id = {}

            try:
                for line in client.api.pull(docker_image, stream=True, decode=True):
                    if "id" in line:
                        layer_id = line["id"]
                        status = line.get("status", "")
                        progress_by_id[layer_id] = f"{status}"
                    elif "status" in line:
                        logger.info(line["status"])  # catch "Using default tag" or similar

            except docker.errors.APIError as e:
                logger.error(f"Failed to pull image {docker_image}: {e}")
                sys.exit(1)

            # Tag the pulled image
            try:
                image = client.images.get(docker_image)
                image.tag(image_tag)
                logger.info(f"Tagged image {docker_image} as: {image_tag}")
            except docker.errors.ImageNotFound:
                logger.error(f"Pulled image {docker_image} could not be found for tagging.")
                sys.exit(1)

            # Final log output
            logger.info(f"Pull of image `{image_tag}` completed. Summary:")
            for layer_id, status in progress_by_id.items():
                logger.info(f"{layer_id}: {status}")

    except (BuildError, APIError) as e:
        logger.error(f"Docker error: {e}")
        sys.exit(1)

    return image_tag


def run_docker_container(
        client: docker.DockerClient,
        image: str,
        container_env: dict[str, Any],
        volumes: dict[str, Any],
        command: str="/bin/sh -c 'tail -f /dev/null'",  # Keeps container alive
) -> Container:
    try:
        logger.info(f"Running container for image {image}...")
        container = client.containers.run(
            image=image,
            command=command,
            environment=container_env,
            volumes=volumes,
            detach=True,  # Run in background
            tty=True,
        )

        container_info = {
            "Started container": container.id,
            "Container image": container.attrs.get("Config", {}).get("Image"),
            "Container name": container.attrs.get("Name")[1:],
            "Container created at": container.attrs.get("Created"),
            "Cmd": container.attrs.get("Config", {}).get("Cmd"),
        }
        log_multiple_lines(container_info)

    except DockerException as e:
        logger.error(f"Error running container: {e}")
        if "container" in locals():
            container.remove(force=True)
        sys.exit(1)

    return container


def copy_file_to_docker_container(container: Container, src_path: str, dest_path: str) -> None:
    with open(src_path, "rb") as f:
        data = f.read()

    tar_stream = io.BytesIO()

    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tarinfo = tarfile.TarInfo(name=os.path.basename(dest_path))
        tarinfo.size = len(data)
        tarinfo.mode = 0o755  # Make it executable
        tar.addfile(tarinfo, io.BytesIO(data))

    tar_stream.seek(0)
    container.put_archive(path=os.path.dirname(dest_path), data=tar_stream)


def run_command_in_docker_container(container: Container, command: list[str], exec_env: dict[str, Any]) -> None:
    try:
        joined_command = " ".join(command)
        logger.info(f"Running the cover-agent command: {joined_command}")

        exec_create = container.client.api.exec_create(
            container.id,
            cmd=command,
            environment=exec_env if exec_env else None,
        )
        exec_id = exec_create["Id"]

        exec_start = container.client.api.exec_start(
            exec_id,
            stream=True,
            demux=True,  # separates stdout and stderr
        )

        # Stream output in real-time
        for data in exec_start:
            stdout, stderr = data
            if stdout:
                print(stdout.decode(), end="")
            if stderr:
                print(stderr.decode(), end="")

        exec_inspect = container.client.api.exec_inspect(exec_id)
        exit_code = exec_inspect["ExitCode"]

        logger.debug(f"Command finished with exit code: {exit_code}")
        if exit_code != 0:
            logger.error(f"Error running command {joined_command}.")
            logger.error(f"Test failed with exit code {exit_code}.")
            clean_up_docker_container(container)
            sys.exit(exit_code)

        logger.info("Done.")
    except DockerException as e:
        logger.error(f"Failed to execute command in container: {e}")
        sys.exit(1)


def log_test_args(test_args: argparse.Namespace, max_value_len=60) -> None:
    for key, value in vars(test_args).items():
        value_str = str(value)
        if len(value_str) > max_value_len:
            value_str = f"{value_str[:max_value_len]}...{value_str[-5:]}"
        logger.info(f"{key:30}: {value_str}")


def log_multiple_lines(lines: dict[str, Any]) -> None:
    for label, value in lines.items():
        logger.info(f"{label}: {value}")


def clean_up_docker_container(container: Container) -> None:
    logger.info("Cleaning up...")
    logger.info(f"Stop container {container.id}...")
    container.stop()

    logger.info(f"Remove container {container.id}...")
    container.remove()


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
        #default="coverage.xml",
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
