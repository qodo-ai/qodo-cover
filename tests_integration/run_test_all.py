import argparse
import os
import sys

from enum import Enum
from typing import Any, Iterable

import docker
from docker.errors import DockerException
from dotenv import load_dotenv

from cover_agent.CustomLogger import CustomLogger

from run_test_with_docker import run_test


load_dotenv()
logger = CustomLogger.get_logger(__name__)


class CoverageType(Enum):
    LCOV = "lcov"
    COBERTURA = "cobertura"
    JACOCO = "jacoco"


def stream_docker_logs(response: Iterable[bytes|dict[str, str]]) -> None:
    """Stream Docker build/run logs to console."""
    for chunk in response:
        if isinstance(chunk, bytes):
            print(chunk.decode(), end='')
        elif 'stream' in chunk:
            print(chunk['stream'], end='')
        elif 'status' in chunk:
            print(f"{chunk['status']}", end='')
            if 'progress' in chunk:
                print(f": {chunk['progress']}", end='')
            print()
        sys.stdout.flush()


def build_image(client: docker.DockerClient, dockerfile: str, platform: str="linux/amd64") -> None:
    """
    Builds a Docker image from the specified Dockerfile.
    Force build for x86_64 architecture (`linux/amd64`) even for Apple Silicon currently.
    """
    try:
        logger.info(f"Building image from {dockerfile}...")
        response = client.api.build(
            path=".",
            dockerfile=dockerfile,
            tag="cover-agent-installer",
            decode=True,
            platform=platform,
        )
        stream_docker_logs(response)
    except DockerException as e:
        logger.error(f"Error building image: {e}")
        exit(1)


def run_container(
        client: docker.DockerClient, image: str, volumes: dict[str, Any], command: str="/bin/sh -c 'tail -f /dev/null'"
) -> None:
    try:
        logger.info(f"Running container for {image}...")
        container = client.containers.run(
            image,
            command=command,
            remove=True,
            volumes=volumes,
            detach=True,  # Run in background
        )
        
        # Stream output in real-time
        for chunk in container.attach(stdout=True, stderr=True, stream=True, logs=True):
            if chunk:
                print(chunk.decode(), end='')
                sys.stdout.flush()
                
        exit_code = container.wait()['StatusCode']
        if exit_code != 0:
            raise DockerException(f"Container exited with status {exit_code}")
            
    except DockerException as e:
        logger.error(f"Error running container: {e}")
        if 'container' in locals():
            container.remove(force=True)
        exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run all tests with Docker.")
    parser.add_argument("--model", default=os.getenv("MODEL"), help="Model name.")
    parser.add_argument("--run-installer", action="store_true", help="Run the installer within a Docker container.")
    args = parser.parse_args()

    model = args.model
    run_installer = args.run_installer
    client = docker.from_env()

    if run_installer:
        build_image(client, "Dockerfile")
        os.makedirs("dist", exist_ok=True)
        dist_path = os.path.join(os.getcwd(), "dist")
        run_container(
            client, "cover-agent-installer", {dist_path: {"bind": "/app/dist", "mode": "rw"}}, command="make installer"
        )

    tests = [
        # C Calculator Example
        {
            "docker_image": "embeddeddevops/c_cli:latest",
            "source_file_path": "calc.c",
            "test_file_path": "test_calc.c",
            "code_coverage_report_path": "coverage_filtered.info",
            "test_command": r"sh build_and_test_with_coverage.sh",
            "coverage_type": CoverageType.LCOV.value,
            "max_iterations": 4,
            "desired_coverage": 50,
        },
        # C++ Calculator Example
        {
            "docker_image": "embeddeddevops/cpp_cli:latest",
            "source_file_path": "calculator.cpp",
            "test_file_path": "test_calculator.cpp",
            "code_coverage_report_path": "coverage.xml",
            "test_command": r"sh build_and_test_with_coverage.sh",
            "coverage_type": CoverageType.COBERTURA.value,
        },
        # C# Calculator Web Service
        # TODO: Fix test_command here as it fails in macOS
        {
            "docker_image": "embeddeddevops/csharp_webservice:latest",
            "source_file_path": "CalculatorApi/CalculatorController.cs",
            "test_file_path": "CalculatorApi.Tests/CalculatorControllerTests.cs",
            "code_coverage_report_path": "CalculatorApi.Tests/TestResults/coverage.cobertura.xml",
            "test_command": (
                r'dotnet test --collect:"XPlat Code Coverage" CalculatorApi.Tests/ && find . '
                r'-name "coverage.cobertura.xml" -exec mv {} CalculatorApi.Tests/TestResults/coverage.cobertura.xml \;'
            ),
            "coverage_type": CoverageType.COBERTURA.value,
            "desired_coverage": "50",
        },
        # Go Webservice Example
        {
            "docker_image": "embeddeddevops/go_webservice:latest",
            "source_file_path": "app.go",
            "test_file_path": "app_test.go",
            "test_command": (
              r"go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml"
            ),
            "max_iterations": 4,
        },
        # Java Gradle example
        # TODO: Figure out why it fails in macOS with `timed out`
        {
            "docker_image": "embeddeddevops/java_gradle:latest",
            "source_file_path": "src/main/java/com/davidparry/cover/SimpleMathOperations.java",
            "test_file_path": "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy",
            "test_command": r"./gradlew clean test jacocoTestReport",
            "coverage_type": CoverageType.JACOCO.value,
            "code_coverage_report_path": "build/reports/jacoco/test/jacocoTestReport.csv",
        },
        # Java Spring Calculator example
        {
            "docker_image": "embeddeddevops/java_spring_calculator:latest",
            "source_file_path": "src/main/java/com/example/calculator/controller/CalculatorController.java",
            "test_file_path": "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java",
            "test_command": r"mvn verify",
            "coverage_type": CoverageType.JACOCO.value,
            "code_coverage_report_path": "target/site/jacoco/jacoco.csv",
        },
        # VanillaJS Example
        {
            "docker_image": "embeddeddevops/js_vanilla:latest",
            "source_file_path": "ui.js",
            "test_file_path": "ui.test.js",
            "test_command": r"npm run test:coverage",
            "code_coverage_report_path": "coverage/coverage.xml",
        },
        # Python FastAPI Example
        {
            "docker_image": "embeddeddevops/python_fastapi:latest",
            "source_file_path": "app.py",
            "test_file_path": "test_app.py",
            "test_command": r"pytest --cov=. --cov-report=xml --cov-report=term",
            "model": "gpt-4o-mini",
        },
        # React Calculator Example
        {
            "docker_image": "embeddeddevops/react_calculator:latest",
            "source_file_path": "src/modules/Calculator.js",
            "test_file_path": "src/tests/Calculator.test.js",
            "test_command": r"npm run test",
            "code_coverage_report_path": "coverage/cobertura-coverage.xml",
            "desired_coverage": "55",
        },
        # Ruby Sinatra Example
        {
            "docker_image": "embeddeddevops/ruby_sinatra:latest",
            "source_file_path": "app.rb",
            "test_file_path": "test_app.rb",
            "test_command": r"ruby test_app.rb",
            "code_coverage_report_path": "coverage/coverage.xml",
        },
        # TypeScript Calculator Example
        {
            "docker_image": "embeddeddevops/typescript_calculator:latest",
            "source_file_path": "src/modules/Calculator.ts",
            "test_file_path": "tests/Calculator.test.ts",
            "test_command": r"npm run test",
            "code_coverage_report_path": "coverage/cobertura-coverage.xml",
        },
    ]

    for test in tests:
        test_args = argparse.Namespace(
            docker_image=test["docker_image"],
            source_file_path=test["source_file_path"],
            test_file_path=test["test_file_path"],
            code_coverage_report_path=test.get("code_coverage_report_path", "coverage.xml"),
            test_command=test["test_command"],
            coverage_type=test.get("coverage_type", CoverageType.COBERTURA.value),
            max_iterations=test.get("max_iterations", os.getenv("MAX_ITERATIONS")),
            desired_coverage=test.get("desired_coverage", os.getenv("DESIRED_COVERAGE")),
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
