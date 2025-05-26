# Integration Tests for Cover Agent
This folder contains end-to-end integration tests for Cover Agent.

## Prerequisites
Before running any of these tests, you will need to build the installer package by running the following command from the root of the repository:
```
make installer
```

You will also need [Docker](https://www.docker.com/) installed.

__Note:__ These scripts were written for Linux but have been tested on a Windows system using WSL 2 and Docker for Desktop.

Since the targets live in Linux, you'll need to build the installer in Linux (versus on Windows and MacOS). This can be done automatically by running the `sh tests_integration/build_installer.sh` command.

## How to Run
You can run these example test suites using a locally hosted LLM or in the cloud just as you would normally with Cover Agent.

### Running the Tests
To run the full test suite, simply run the following command from the root of the repository:
```shell
poetry run python tests_integration/run_test_all.py
```
There's a file with sample test scenarios `tests_integration/scenarios.py` where each test maybe adjusted to your needs. All the scenarios will be executed running this command.

Or run each test individually:
#### Python Fast API Example
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --dockerfile "templated_tests/python_fastapi/Dockerfile"\
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --model "gpt-4o-mini"
```

#### Go Webservice Example
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --dockerfile "templated_tests/go_webservice/Dockerfile" \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --model "gpt-4o"
```

#### Java Gradle Example
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --dockerfile "templated_tests/java_gradle/Dockerfile" \
  --source-file-path "src/main/java/com/davidparry/cover/SimpleMathOperations.java" \
  --test-file-path "src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy" \
  --test-command "./gradlew clean test jacocoTestReport" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "build/reports/jacoco/test/jacocoTestReport.csv" \
  --model "gpt-4o"
```

#### Java Spring Calculator Example
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --dockerfile "templated_tests/java_spring_calculator/Dockerfile" \
  --source-file-path "src/main/java/com/example/calculator/controller/CalculatorController.java" \
  --test-file-path "src/test/java/com/example/calculator/controller/CalculatorControllerTest.java" \
  --test-command "mvn verify" \
  --coverage-type "jacoco" \
  --code-coverage-report-path "target/site/jacoco/jacoco.csv" \
  --model "gpt-4o"
```

#### VanillaJS Example
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --dockerfile "templated_tests/js_vanilla/Dockerfile" \
  --source-file-path "ui.js" \
  --test-file-path "ui.test.js" \
  --test-command "npm run test:coverage" \
  --code-coverage-report-path "coverage/coverage.xml" \
  --model "gpt-4o"
```

### Using Different LLMs
You can use a different LLM by passing in the `--model` and `--api-base` parameters. For example, to use a locally hosted LLM with Ollama you can pass in:
```shell
--model "ollama/mistral" --api-base "http://host.docker.internal:11434"
```
For any other LLM that requires more environment variables to be set, you will need to update the shell script and pass in the variables within the Docker command.

### Record & Replay
To save LLM service credits, a response recording mode is available. The starting point is a group hash, generated from the hashes of the source and test files used in each test run. If either file changes, the corresponding LLM responses should be re-recorded. 
Run the following command to execute all tests with LLM response recording enabled:
```shell
poetry run python tests_integration/run_test_all.py --record-mode
```

If you run the same command without the `--record-mode` flag:
```shell
poetry run python tests_integration/run_test_all.py
```
it will use the recorded responses to generate tests without calling the LLM if recordings are available. Otherwise, it will call the LLM to run the tests.

You may also record LLM responses from a separate test run. Run a test as you normally would, and add the `--record-mode` flag to the command:
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --record-mode \
  --docker-image "embeddeddevops/python_fastapi:latest" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --coverage-type "cobertura" \
  --model "gpt-4o-mini" \
  --desired-coverage 70 \
  --max-iterations 3
```

The table below explains the behavior of the test runner depending on whether the `--record-mode` flag is set and whether a recorded file already exists:

|    Flag     | Record File | Result                                |
|:-----------:|:-----------:|:--------------------------------------|
|      ❌      |      ❌      | Regular test run (file not recorded)  |
|      ✅      |      ❌      | Records a new file                    |
|      ✅      |      ✅      | Overwrites an existing file           |
|      ❌      |      ✅      | Replays a recorded file               |

Recorded responses are stored in the `stored_responses` folder. Files are named based on the test name and a hash value that depends on the contents of the source and test files.
```shell
<test_name>_responses_<hash_value>.yml

# i.e.
python_fastapi_responses_a9d9de927a82a7d776889738d2880bec7166c5f69d3518837183a20ef48b2a37.yml
```
A response file corresponding to the same source and test files group hash in a file name is updated during each recording session with new prompt hash entries.
To regenerate it from scratch, you can delete the existing response file and run a new recording session. 


### Suppressing Log Files
You can suppress logs using the `--suppress-log-files` flag. This prevents the creation of the `run.log`, `test_results.html`, and the test results `db` files:
* Running all tests:
```shell
poetry run python tests_integration/run_test_all.py --suppress-log-files
```
* Running a single test:
```shell
poetry run python tests_integration/run_test_with_docker.py \
  --dockerfile "templated_tests/python_fastapi/Dockerfile"\
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --model "gpt-4o-mini" \
  --suppress-log-files
```
* If you run all scenarios, this flag may be added there:
```python
    # Python FastAPI Example
    {
        "docker_image": "embeddeddevops/python_fastapi:latest",
        "source_file_path": "app.py",
        "test_file_path": "test_app.py",
        "test_command": r"pytest --cov=. --cov-report=xml --cov-report=term",
        "model": "gpt-4o-mini",
        "suppress_log_files": True,
    }
```

## When to Run
This test suite is intended to run with real LLMs (either locally hosted or online). If choosing cloud-provided LLMs, keep in mind that there is a cost associated with running these tests.

These tests should **absolutely** be run before a massive refactor or any major changes to the LLM/prompting logic of the code.

## How It Works
The integration tests run within Docker containers to ensure complete isolation from any external or existing environment.

# Increasing Coverage Iteratively
The `increase_coverage.py` script attempts to run Cover Agent for all files within the `cover_agent` directory. You'll need to call a Poetry shell first before running like so:
```
poetry install
poetry shell
poetry run python tests_integration/increase_coverage.py
```

# Analyzing failures
After Cover Agent runs we store the run results in a database (see `docs/database_usage.md` for more details). 

The `analyze_tests.py` script extracts out the metadata from each run and, with the help of an LLM (currently hardcoded to OpenAI's GPT-4o), it analyzes each failed tests and provides feedback on the failure. This report (i.e. what the LLM streams to the command line) is then written to a file (currently hardcoded as `test_results_analysis.md`).

You can then take the report (`test_results_analysis.md`) and either review it or pass it back to an LLM for further analysis (e.g. looking for repeating errors, bad imports, etc.).