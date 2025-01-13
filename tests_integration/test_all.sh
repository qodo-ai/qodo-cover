#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit if any command in a pipeline fails
set -x  # Print commands and their arguments as they are executed

# Default model name
MODEL="gpt-4o"
RUN_INSTALLER=false

# Function to display usage
usage() {
    echo "Usage: $0 [--model model_name] [--run-installer]"
    echo "  --model model_name      Set the model name (default: gpt-3.5-turbo)"
    echo "  --run-installer         Run the installer within a Docker container"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift
            ;;
        --run-installer)
            RUN_INSTALLER=true
            ;;
        *)
            usage
            ;;
    esac
    shift
done

# Build the installer within a Docker container if requested
if [ "$RUN_INSTALLER" = true ]; then
    docker build -t cover-agent-installer -f Dockerfile .

    mkdir -p dist
    docker run --rm --volume "$(pwd)/dist:/app/dist" cover-agent-installer
fi

# Set the log_db_arg variable if LOG_DB_PATH is set
log_db_arg=""
if [ -n "$LOG_DB_PATH" ]; then
    log_db_arg="--log-db-path $LOG_DB_PATH"
fi

# C Calculator Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/c_cli:latest" \
  --source-file-path "calc.c" \
  --test-file-path "test_calc.c" \
  --code-coverage-report-path "coverage_filtered.info" \
  --test-command "sh build_and_test_with_coverage.sh" \
  --coverage-type "lcov" \
  --max-iterations "4" \
  --desired-coverage "50" \
  --model $MODEL \
  $log_db_arg

# C++ Calculator Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/cpp_cli:latest" \
  --source-file-path "calculator.cpp" \
  --test-file-path "test_calculator.cpp" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "sh build_and_test_with_coverage.sh" \
  --coverage-type "cobertura" \
  --model $MODEL \
  $log_db_arg

# C# Calculator Web Service
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/csharp_webservice:latest" \
  --source-file-path "CalculatorApi/CalculatorController.cs" \
  --test-file-path "CalculatorApi.Tests/CalculatorControllerTests.cs" \
  --code-coverage-report-path "CalculatorApi.Tests/TestResults/coverage.cobertura.xml" \
  --test-command "dotnet test --collect:'XPlat Code Coverage' CalculatorApi.Tests/ && find . -name 'coverage.cobertura.xml' -exec mv {} CalculatorApi.Tests/TestResults/coverage.cobertura.xml \;" \
  --coverage-type "cobertura" \
  --desired-coverage "50" \
  --model $MODEL \
  $log_db_arg

# Go Webservice Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/go_webservice:latest" \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --model $MODEL \
  $log_db_arg

# Java Gradle example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/java_gradle:latest" \
  --source-file-path "src/main/java/com/davidparry/cover/SimpleMathOperations.java" \
  --test-file-path "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy" \
  --test-command "./gradlew clean test jacocoTestReport" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "build/reports/jacoco/test/jacocoTestReport.csv" \
  --model $MODEL \
  $log_db_arg

# Java Spring Calculator example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/java_spring_calculator:latest" \
  --source-file-path "src/main/java/com/example/calculator/controller/CalculatorController.java" \
  --test-file-path "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java" \
  --test-command "mvn verify" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "target/site/jacoco/jacoco.csv" \
  --model $MODEL \
  $log_db_arg

# VanillaJS Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/js_vanilla:latest" \
  --source-file-path "ui.js" \
  --test-file-path "ui.test.js" \
  --test-command "npm run test:coverage" \
  --code-coverage-report-path "coverage/coverage.xml" \
  --model $MODEL \
  $log_db_arg

# Python FastAPI Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/python_fastapi:latest" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --model "gpt-3.5-turbo" \
  $log_db_arg

# React Calculator Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/react_calculator:latest" \
  --source-file-path "src/modules/Calculator.js" \
  --test-file-path "src/tests/Calculator.test.js" \
  --test-command "npm run test" \
  --code-coverage-report-path "coverage/cobertura-coverage.xml" \
  --desired-coverage "55" \
  --model $MODEL \
  $log_db_arg

# Ruby Sinatra Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/ruby_sinatra:latest" \
  --source-file-path "app.rb" \
  --test-file-path "test_app.rb" \
  --test-command "ruby test_app.rb" \
  --code-coverage-report-path "coverage/coverage.xml" \
  --model $MODEL \
  $log_db_arg

# TypeScript Calculator Example
sh tests_integration/test_with_docker.sh \
  --docker-image "embeddeddevops/typescript_calculator:latest" \
  --source-file-path "src/modules/Calculator.ts" \
  --test-file-path "tests/Calculator.test.ts" \
  --test-command "npm run test" \
  --code-coverage-report-path "coverage/cobertura-coverage.xml" \
  --model $MODEL \
  $log_db_arg
