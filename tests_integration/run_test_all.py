import os
import argparse
from enum import Enum

import docker
from docker.errors import DockerException

from cover_agent.CustomLogger import CustomLogger

from run_test_with_docker import run_test_with_docker, parse_args


logger = CustomLogger.get_logger(__name__)


class CoverageType(Enum):
    LCOV = "lcov"
    COBERTURA = "cobertura"
    JACOCO = "jacoco"


def build_image(client, dockerfile):
    try:
        client.images.build(path=".", dockerfile=dockerfile, tag="cover-agent-installer")
    except DockerException as e:
        logger.error(f"Error building image: {e}")
        exit(1)


def run_container(client, image, volumes):
    try:
        client.containers.run(image, remove=True, volumes=volumes)
    except DockerException as e:
        logger.error(f"Error running container: {e}")
        exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run all tests with Docker.")
    parser.add_argument("--model", default="gpt-4o-2024-11-20", help="Model name.")
    parser.add_argument("--run-installer", action="store_true", help="Run the installer within a Docker container.")
    args = parser.parse_args()

    model = args.model
    run_installer = args.run_installer

    client = docker.from_env()

    if run_installer:
        build_image(client, "Dockerfile")
        os.makedirs("dist", exist_ok=True)
        run_container(client, "cover-agent-installer", {"$(pwd)/dist": {"bind": "/app/dist", "mode": "rw"}})

    log_db_arg = f"--log-db-path {os.getenv('LOG_DB_PATH')}" if os.getenv('LOG_DB_PATH') else ""

    tests = [
        {
            "docker_image": "embeddeddevops/c_cli:latest",
            "source_file": "calc.c",
            "test_file": "test_calc.c",
            "coverage_report": "coverage_filtered.info",
            "test_command": "sh build_and_test_with_coverage.sh",
            "coverage_type": CoverageType.LCOV.value,
            "max_iterations": "4",
            "desired_coverage": "50",
        },
        {
            "docker_image": "embeddeddevops/cpp_cli:latest",
            "source_file": "calculator.cpp",
            "test_file": "test_calculator.cpp",
            "coverage_report": "coverage.xml",
            "test_command": "sh build_and_test_with_coverage.sh",
            "coverage_type": CoverageType.COBERTURA.value,
        },
        # {
        #     "docker_image": "embeddeddevops/csharp_webservice:latest",
        #     "source_file": "CalculatorApi/CalculatorController.cs",
        #     "test_file": "CalculatorApi.Tests/CalculatorControllerTests.cs",
        #     "coverage_report": "CalculatorApi.Tests/TestResults/coverage.cobertura.xml",
        #     "test_command": "dotnet test --collect:'XPlat Code Coverage' CalculatorApi.Tests/ && find . -name 'coverage.cobertura.xml' -exec mv {} CalculatorApi.Tests/TestResults/coverage.cobertura.xml \;",
        #     "coverage_type": CoverageType.COBERTURA.value,
        #     "desired_coverage": "50",
        # },
        {
            "docker_image": "embeddeddevops/go_webservice:latest",
            "source_file": "app.go",
            "test_file": "app_test.go",
            "test_command": (
              "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml"
            ),
            "max_iterations": "4",
        },
        {
            "docker_image": "embeddeddevops/java_gradle:latest",
            "source_file": "src/main/java/com/davidparry/cover/SimpleMathOperations.java",
            "test_file": "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy",
            "test_command": "./gradlew clean test jacocoTestReport",
            "coverage_type": CoverageType.JACOCO.value,
            "coverage_report": "build/reports/jacoco/test/jacocoTestReport.csv",
        },
        {
            "docker_image": "embeddeddevops/java_spring_calculator:latest",
            "source_file": "src/main/java/com/example/calculator/controller/CalculatorController.java",
            "test_file": "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java",
            "test_command": "mvn verify",
            "coverage_type": CoverageType.JACOCO.value,
            "coverage_report": "target/site/jacoco/jacoco.csv",
        },
        {
            "docker_image": "embeddeddevops/js_vanilla:latest",
            "source_file": "ui.js",
            "test_file": "ui.test.js",
            "test_command": "npm run test:coverage",
            "coverage_report": "coverage/coverage.xml",
        },
        {
            "docker_image": "embeddeddevops/python_fastapi:latest",
            "source_file": "app.py",
            "test_file": "test_app.py",
            "test_command": "pytest --cov=. --cov-report=xml --cov-report=term",
            "model": "gpt-4o-mini",
        },
        {
            "docker_image": "embeddeddevops/react_calculator:latest",
            "source_file": "src/modules/Calculator.js",
            "test_file": "src/tests/Calculator.test.js",
            "test_command": "npm run test",
            "coverage_report": "coverage/cobertura-coverage.xml",
            "desired_coverage": "55",
        },
        {
            "docker_image": "embeddeddevops/ruby_sinatra:latest",
            "source_file": "app.rb",
            "test_file": "test_app.rb",
            "test_command": "ruby test_app.rb",
            "coverage_report": "coverage/coverage.xml",
        },
        {
            "docker_image": "embeddeddevops/typescript_calculator:latest",
            "source_file": "src/modules/Calculator.ts",
            "test_file": "tests/Calculator.test.ts",
            "test_command": "npm run test",
            "coverage_report": "coverage/cobertura-coverage.xml",
        }
    ]

    for test in tests:
        test_args = argparse.Namespace(
            docker_image=test["docker_image"],
            source_file_path=test["source_file"],
            test_file_path=test["test_file"],
            code_coverage_report_path=test.get("coverage_report", ""),
            test_command=test["test_command"],
            coverage_type=test.get("coverage_type", "cobertura"),
            max_iterations=test.get("max_iterations", "3"),
            desired_coverage=test.get("desired_coverage", "70"),
            model=model,
            api_base="",
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            dockerfile="",
            log_db_path=os.getenv("LOG_DB_PATH", "")
        )
        run_test_with_docker(test_args)


if __name__ == "__main__":
    main()
