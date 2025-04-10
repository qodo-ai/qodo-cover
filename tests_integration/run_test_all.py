import argparse
import os

import docker
from dotenv import load_dotenv

import tests_integration.constants as constants

from cover_agent.CustomLogger import CustomLogger
from tests_integration.docker_utils import (
    build_docker_image,
    clean_up_docker_container,
    run_command_in_docker_container,
    run_docker_container,
)
from tests_integration.run_test_with_docker import run_test
from tests_integration.scenarios import TESTS


load_dotenv()
logger = CustomLogger.get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Args for running tests with Docker.")
    parser.add_argument("--model", default=constants.MODEL, help="Which LLM model to use.")
    parser.add_argument("--run-installer", action="store_true", help="Build `cover-agent` binary.")
    args = parser.parse_args()

    model = args.model
    run_installer = args.run_installer
    client = docker.from_env()

    if run_installer:
        logger.info(f"Compiling cover-agent binary...")
        image_tag = "cover-agent-installer"

        logger.info(f"Building the Docker image {image_tag}...")
        build_docker_image(client, "Dockerfile", image_tag=image_tag)

        os.makedirs("dist", exist_ok=True)
        dist_path = os.path.join(os.getcwd(), "dist")
        logger.info(f"Defined dist_path: {dist_path}")

        logger.info(f"Running the Docker container with image {image_tag}...")
        container = run_docker_container(client, image_tag, volumes={dist_path: {"bind": "/app/dist", "mode": "rw"}})

        logger.info(f"Running command in the Docker container {container.name}...")
        run_command_in_docker_container(container, ["/bin/sh", "-c", "cd /app && make installer"], {})

        logger.info(f"Cleaning-up the Docker container {container.name}...")
        clean_up_docker_container(container)


        logger.info(f"Compiling of cover-agent binary completed.")

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
