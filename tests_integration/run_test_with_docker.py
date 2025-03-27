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

from cover_agent.CustomLogger import CustomLogger


load_dotenv()
logger = CustomLogger.get_logger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test with Docker.")
    parser.add_argument("--model", default=os.getenv("MODEL"), help="Model name.")
    parser.add_argument("--api-base", default="", help="API base URL.")
    parser.add_argument("--openai-api-key", default=os.getenv("OPENAI_API_KEY", ""), help="OpenAI API key.")
    parser.add_argument("--dockerfile", default="", help="Path to Dockerfile.")
    parser.add_argument("--docker-image", default="", help="Docker image name.")
    parser.add_argument("--source-file-path", default="", help="Path to source file.")
    parser.add_argument("--test-file-path", default="", help="Path to test file.")
    parser.add_argument("--test-command", default="", help="Command to run tests.")
    parser.add_argument("--coverage-type", default="cobertura", help="Coverage type.")
    parser.add_argument("--code-coverage-report-path", default="coverage.xml", help="Path to code coverage report.")
    parser.add_argument(
        "--max-iterations", type=int, default=os.getenv("MAX_ITERATIONS"), help="Maximum number of iterations."
    )
    parser.add_argument(
        "--desired-coverage", type=int, default=os.getenv("DESIRED_COVERAGE"), help="Desired code coverage percentage."
    )
    parser.add_argument("--log-db-path", default=os.getenv("LOG_DB_PATH", ""), help="Path to log DB.")
    return parser.parse_args()


def build_or_pull_image(client: docker.DockerClient, dockerfile: str, docker_image: str) -> str:
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
                    logger.info(log["stream"], end="")
        else:
            logger.info(f"Pulling the Docker image {docker_image}...")
            image = client.images.pull(docker_image)
            image.tag(image_tag)
    except (BuildError, APIError) as e:
        logger.error(f"Docker error: {e}")
        sys.exit(1)

    return image_tag


def start_container(
        client: docker.DockerClient, image_tag: str, container_env: dict[str, Any], container_volumes: dict[str, Any]
) -> Container:
    container_name = "cover-agent-container"

    try:
        # Check if a container with the same name already exists and remove it
        existing_container = client.containers.list(filters={"name": container_name})

        if existing_container:
            logger.info(f"Removing existing container with name {container_name}...")
            existing_container[0].remove(force=True)

        container = client.containers.run(
            image=image_tag,
            command="tail -f /dev/null",  # Keeps container alive
            environment=container_env,
            volumes=container_volumes,
            detach=True,
            tty=True,
            name=container_name,
        )
    except DockerException as e:
        logger.error(f"Failed to start the container: {e}")
        sys.exit(1)

    return container


def copy_to_container(container: Container, src_path: str, dest_path: str) -> None:
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


def run_command_in_container(container: Container, command: list[str], exec_env: dict[str, Any]) -> None:
    try:
        exec_result = container.exec_run(
            cmd=command,
            environment=exec_env if exec_env else None,
            stream=True,
            demux=True,  # separates stdout and stderr
        )
        for stdout, stderr in exec_result.output:
            if stdout:
                print(stdout.decode(), end="")
            if stderr:
                print(stderr.decode(), end="")
    except DockerException as e:
        logger.error(f"Failed to execute command in container: {e}")
        sys.exit(1)


def run_test_with_docker(args: argparse.Namespace) -> None:
    client = docker.from_env()

    if not args.source_file_path or not args.test_file_path or not args.test_command:
        logger.error("Missing required parameters: --source-file-path, --test-file-path, or --test-command.")
        sys.exit(1)

    if not args.dockerfile and not args.docker_image:
        logger.error("Missing required parameters: either --dockerfile or --docker-image must be provided.")
        sys.exit(1)

    image_tag = build_or_pull_image(client, args.dockerfile, args.docker_image)
    container_env = {}

    if args.openai_api_key:
        container_env["OPENAI_API_KEY"] = args.openai_api_key

    if ANTHROPIC_API_KEY:
        container_env["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

    container_volumes = {}

    if args.log_db_path:
        log_db_name = os.path.basename(args.log_db_path)
        container_volumes[args.log_db_path] = {"bind": f"/{log_db_name}", "mode": "rw"}

    container = start_container(client, image_tag, container_env, container_volumes)
    copy_to_container(container, "dist/cover-agent", "/usr/local/bin/cover-agent")
    command = [
        "/usr/local/bin/cover-agent",
        "--source-file-path", args.source_file_path,
        "--test-file-path", args.test_file_path,
        "--code-coverage-report-path", args.code_coverage_report_path,
        "--test-command", args.test_command,
        "--coverage-type", args.coverage_type,
        "--desired-coverage", str(args.desired_coverage),
        "--max-iterations", str(args.max_iterations),
        "--strict-coverage",
    ]

    if args.model:
        command += ["--model", args.model]

    if args.api_base:
        command += ["--api-base", args.api_base]

    if args.log_db_path:
        log_db_name = os.path.basename(args.log_db_path)
        command += ["--log-db-path", f"/{log_db_name}"]

    exec_env = {}

    if args.openai_api_key:
        exec_env["OPENAI_API_KEY"] = args.openai_api_key

    if ANTHROPIC_API_KEY:
        exec_env["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

    run_command_in_container(container, command, exec_env)
    container.stop()
    container.remove()


if __name__ == "__main__":
    args = parse_args()
    run_test_with_docker(args)
