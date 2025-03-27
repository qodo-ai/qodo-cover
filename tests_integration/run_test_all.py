import argparse
import os

from enum import Enum

import docker
from docker.errors import DockerException
from dotenv import load_dotenv

from cover_agent.CustomLogger import CustomLogger

from run_test_with_docker import run_test_with_docker


load_dotenv()
logger = CustomLogger.get_logger(__name__)


class CoverageType(Enum):
    LCOV = "lcov"
    COBERTURA = "cobertura"
    JACOCO = "jacoco"


def build_image(client: docker.DockerClient, dockerfile: str) -> None:
    try:
        client.images.build(path=".", dockerfile=dockerfile, tag="cover-agent-installer")
    except DockerException as e:
        logger.error(f"Error building image: {e}")
        exit(1)


def run_container(client: docker.DockerClient, image, volumes) -> None:
    try:
        client.containers.run(image, remove=True, volumes=volumes)
    except DockerException as e:
        logger.error(f"Error running container: {e}")
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
        run_container(client, "cover-agent-installer", {"$(pwd)/dist": {"bind": "/app/dist", "mode": "rw"}})

    tests = [
        # C Calculator Example
        {
            "docker_image": "embeddeddevops/c_cli:latest",
            "source_file_path": "calc.c",
            "test_file_path": "test_calc.c",
            "code_coverage_report_path": "coverage_filtered.info",
            "test_command": "sh build_and_test_with_coverage.sh",
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
            "test_command": "sh build_and_test_with_coverage.sh",
            "coverage_type": CoverageType.COBERTURA.value,
        },
        # C# Calculator Web Service
        # TODO: Fix test_command here as it fails
        {
            "docker_image": "embeddeddevops/csharp_webservice:latest",
            "source_file_path": "CalculatorApi/CalculatorController.cs",
            "test_file_path": "CalculatorApi.Tests/CalculatorControllerTests.cs",
            "code_coverage_report_path": "CalculatorApi.Tests/TestResults/coverage.cobertura.xml",
            "test_command": (
                "dotnet test --collect:\"XPlat Code Coverage\" CalculatorApi.Tests/ && find . "
                "-name \"coverage.cobertura.xml\" -exec mv {} CalculatorApi.Tests/TestResults/coverage.cobertura.xml \;"
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
              "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml"
            ),
            "max_iterations": 4,
        },
        # Java Gradle example
        {
            "docker_image": "embeddeddevops/java_gradle:latest",
            "source_file_path": "src/main/java/com/davidparry/cover/SimpleMathOperations.java",
            "test_file_path": "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy",
            "test_command": "./gradlew clean test jacocoTestReport",
            "coverage_type": CoverageType.JACOCO.value,
            "code_coverage_report_path": "build/reports/jacoco/test/jacocoTestReport.csv",
        },
        # Java Spring Calculator example
        {
            "docker_image": "embeddeddevops/java_spring_calculator:latest",
            "source_file_path": "src/main/java/com/example/calculator/controller/CalculatorController.java",
            "test_file_path": "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java",
            "test_command": "mvn verify",
            "coverage_type": CoverageType.JACOCO.value,
            "code_coverage_report_path": "target/site/jacoco/jacoco.csv",
        },
        # VanillaJS Example
        {
            "docker_image": "embeddeddevops/js_vanilla:latest",
            "source_file_path": "ui.js",
            "test_file_path": "ui.test.js",
            "test_command": "npm run test:coverage",
            "code_coverage_report_path": "coverage/coverage.xml",
        },
        # Python FastAPI Example
        {
            "docker_image": "embeddeddevops/python_fastapi:latest",
            "source_file_path": "app.py",
            "test_file_path": "test_app.py",
            "test_command": "pytest --cov=. --cov-report=xml --cov-report=term",
            "model": "gpt-4o-mini",
        },
        # React Calculator Example
        {
            "docker_image": "embeddeddevops/react_calculator:latest",
            "source_file_path": "src/modules/Calculator.js",
            "test_file_path": "src/tests/Calculator.test.js",
            "test_command": "npm run test",
            "code_coverage_report_path": "coverage/cobertura-coverage.xml",
            "desired_coverage": "55",
        },
        # Ruby Sinatra Example
        {
            "docker_image": "embeddeddevops/ruby_sinatra:latest",
            "source_file_path": "app.rb",
            "test_file_path": "test_app.rb",
            "test_command": "ruby test_app.rb",
            "code_coverage_report_path": "coverage/coverage.xml",
        },
        # TypeScript Calculator Example
        {
            "docker_image": "embeddeddevops/typescript_calculator:latest",
            "source_file_path": "src/modules/Calculator.ts",
            "test_file_path": "tests/Calculator.test.ts",
            "test_command": "npm run test",
            "code_coverage_report_path": "coverage/cobertura-coverage.xml",
        },
    ]

    for test in tests:
        test_args = argparse.Namespace(
            docker_image=test["docker_image"],
            source_file_path=test["source_file_path"],
            test_file_path=test["test_file_path"],
            code_coverage_report_path=test.get("code_coverage_report_path", ""),
            test_command=test["test_command"],
            coverage_type=test.get("coverage_type", "cobertura"),
            max_iterations=test.get("max_iterations", os.getenv("MAX_ITERATIONS")),
            desired_coverage=test.get("desired_coverage", os.getenv("DESIRED_COVERAGE")),
            model=model,
            api_base="",
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            dockerfile="",
            log_db_path=os.getenv("LOG_DB_PATH", ""),
        )

        run_test_with_docker(test_args)


if __name__ == "__main__":
    main()
