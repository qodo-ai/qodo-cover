import argparse
import os
import sys

from typing import Any, Iterable

import docker
from docker.errors import DockerException
from dotenv import load_dotenv

from cover_agent.CustomLogger import CustomLogger

import constants
from run_test_with_docker import run_test
from scenarios import TESTS


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def stream_docker_logs(response: Iterable[bytes|dict[str, str]]) -> None:
    """Stream Docker build/run logs to console."""
    for chunk in response:
        if isinstance(chunk, bytes):
            print(chunk.decode(), end="")
        elif "stream" in chunk:
            print(chunk["stream"], end="")
        elif "status" in chunk:
            print(f": {chunk['status']}", end='')
            if "progress" in chunk:
                print(f": {chunk['progress']}", end='')
            print()
        sys.stdout.flush()


def build_docker_image(client: docker.DockerClient, dockerfile: str, platform: str="linux/amd64") -> None:
    """
    Builds a Docker image from the specified Dockerfile.
    Force build for x86_64 architecture (`linux/amd64`) even for Apple Silicon currently.
    """
    try:
        logger.info(f"Building Docker image from {dockerfile}...")
        response = client.api.build(
            path=".",
            dockerfile=dockerfile,
            tag="cover-agent-installer",
            decode=True,
            platform=platform,
        )
        stream_docker_logs(response)
    except DockerException as e:
        logger.error(f"Error building Docker image: {e}")
        exit(1)


def run_docker_container(
        client: docker.DockerClient,
        image: str,
        volumes: dict[str, Any],
        command: str="/bin/sh -c 'tail -f /dev/null'",
) -> None:
    try:
        logger.info(f"Running Docker container for {image}...")
        container = client.containers.run(
            image=image,
            command=command,
            remove=True,
            volumes=volumes,
            detach=True,  # Run in background
        )
        
        # Stream output in real-time
        for chunk in container.attach(stdout=True, stderr=True, stream=True, logs=True):
            if chunk:
                print(chunk.decode(), end="")
                sys.stdout.flush()
                
        exit_code = container.wait()["StatusCode"]
        if exit_code != 0:
            raise DockerException(f"Docker container exited with status {exit_code}.")
            
    except DockerException as e:
        logger.error(f"Error running Docker container: {e}")
        if "container" in locals():
            container.remove(force=True)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Args for running tests with Docker.")
    parser.add_argument("--model", default=constants.MODEL, help="Which LLM model to use.")
    parser.add_argument("--run-installer", action="store_true", help="Build `cover-agent` binary.")
    args = parser.parse_args()

    model = args.model
    run_installer = args.run_installer
    client = docker.from_env()

    if run_installer:
        # Compile `cover-agent` binary
        build_docker_image(client, "Dockerfile")
        os.makedirs("dist", exist_ok=True)
        dist_path = os.path.join(os.getcwd(), "dist")
        run_docker_container(
            client, "cover-agent-installer", {dist_path: {"bind": "/app/dist", "mode": "rw"}}, command="make installer"
        )

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
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            dockerfile=test.get("docker_file_path", ""),
            log_db_path=os.getenv("LOG_DB_PATH", ""),
        )
        run_test(test_args)


if __name__ == "__main__":
    main()
