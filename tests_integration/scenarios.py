from cover_agent.settings.config_schema import CoverageType


TESTS = [
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
    {
        "docker_image": "embeddeddevops/java_gradle:latest",
        "source_file_path": "src/main/java/com/davidparry/cover/SimpleMathOperations.java",
        "test_file_path": "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy",
        "test_command": r"./gradlew clean test jacocoTestReport",
        "coverage_type": CoverageType.JACOCO.value,
        "code_coverage_report_path": "build/reports/jacoco/test/jacocoTestReport.csv",
        "max_run_time_sec": 240,
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
