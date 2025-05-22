



<div align="center">
<div align="center">

 <picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.qodo.ai/wp-content/uploads/2025/02/QodoCover-Light.png" width="330">
  <source media="(prefers-color-scheme: light)" srcset="https://www.qodo.ai/wp-content/uploads/2025/02/QodoCover-Dark.png" width="330">
  <img src="https://www.codium.ai/images/cover-agent/cover-agent-light.png" alt="logo" width="330"> 

</picture>
<br/><br/>
Qodo Cover aims to help efficiently increase code coverage, by automatically generating qualified tests to extend code coverage. Qodo Cover can run in your GitHub CI workflow or locally as a CLI tool.
</div>

[![GitHub license](https://img.shields.io/badge/License-AGPL_3.0-blue.svg)](https://github.com/qodo-ai/qodo-cover/blob/main/LICENSE)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.gg/cYsvFJJbdM)
[![Twitter](https://img.shields.io/twitter/follow/qodoai)](https://twitter.com/qodoai)
    <a href="https://github.com/Codium-ai/cover-agent/commits/main">
    <img alt="GitHub" src="https://img.shields.io/github/last-commit/qodo-ai/qodo-cover/main?style=for-the-badge" height="20">
    </a><br>
    <a href="https://trendshift.io/repositories/10328" target="_blank"><img src="https://trendshift.io/api/badge/repositories/10328" alt="Codium-ai/cover-agent | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</div>

## Table of Contents
* [News and Updates](#news-and-updates)
* [Overview](#overview)
* [Installation and Usage](#installation-and-usage)
* [Contributing](#contributing)
* [Documentation](#documentation)
* [Roadmap](#roadmap)


## News and Updates

### 2024-12-04:
New mode - [Run Qodo Cover Pro in your GitHub CI workflow](https://github.com/qodo-ai/qodo-ci). Currently in preview and available for free for a limited time for Python projects, leveraging your own LLM API key from your favorite LLM provider. It's a practical way to improve code quality and reliability. For more details, reach out to the [Qodo team](https://www.qodo.ai/book-a-demo).

### 2024-11-05:
New mode - scan an entire repo, auto identify the test files, auto collect context for each test file, and extend the test suite with new tests.
See more details [here](docs/repo_coverage.md).


# Qodo-Cover
Welcome to Qodo-Cover. This focused project utilizes Generative AI to automate and enhance the generation of tests (currently mostly unit tests), aiming to streamline development workflows. Qodo-Cover can run via a terminal, and is planned to be integrated into popular CI platforms.

We invite the community to collaborate and help extend the capabilities of Qodo Cover, continuing its development as a cutting-edge solution in the automated unit test generation domain. We also wish to inspire researchers to leverage this open-source tool to explore new test-generation techniques.


## Overview
This tool is part of a broader suite of utilities designed to automate the creation of unit tests for software projects. Utilizing advanced Generative AI models, it aims to simplify and expedite the testing process, ensuring high-quality software development. The system comprises several components:
1. **Test Runner:** Executes the command or scripts to run the test suite and generate code coverage reports.
2. **Coverage Parser:** Validates that code coverage increases as tests are added, ensuring that new tests contribute to the overall test effectiveness.
3. **Prompt Builder:** Gathers necessary data from the codebase and constructs the prompt to be passed to the Large Language Model (LLM).
4. **AI Caller:** Interacts with the LLM to generate tests based on the prompt provided.


## Installation and Usage
### Requirements
Before you begin, make sure you have the following:
- `OPENAI_API_KEY` set in your environment variables, which is required for calling the OpenAI API.
- Code Coverage tool: A Cobertura XML code coverage report is required for the tool to function correctly.
  - For example, in Python one could use `pytest-cov`. Add the `--cov-report=xml` option when running Pytest.
  - Note: We are actively working on adding more coverage types but please feel free to open a PR and contribute to `cover_agent/CoverageProcessor.py`

If running directly from the repository you will also need:
- Python installed on your system.
- Poetry installed for managing Python package dependencies. Installation instructions for Poetry can be found at [https://python-poetry.org/docs/](https://python-poetry.org/docs/).

### Standalone Runtime
Qodo Cover can be installed as a Python Pip package or run as a standalone executable.

#### Python Pip
To install the Python Pip package directly via GitHub run the following command:
```shell
pip install git+https://github.com/qodo-ai/qodo-cover.git
```

#### Binary
The binary can be run without any Python environment installed on your system (e.g. within a Docker container that does not contain Python). You can download the release for your system by navigating to the project's [release page](https://github.com/qodo-ai/qodo-cover/releases).

### Repository Setup
Run the following command to install all the dependencies and run the project from source:
```shell
poetry install
```

### Running the Code
After downloading the executable or installing the Pip package you can run the Cover Agent to generate and validate unit tests. Execute it from the command line by using the following command:
```shell
cover-agent \
  --source-file-path "<path_to_source_file>" \
  --test-file-path "<path_to_test_file>" \
  --project-root "<path_to_project_root>" \
  --code-coverage-report-path "<path_to_coverage_report>" \
  --test-command "<test_command_to_run>" \
  --test-command-dir "<directory_to_run_test_command>" \
  --coverage-type "<type_of_coverage_report>" \
  --desired-coverage <desired_coverage_between_0_and_100> \
  --max-iterations <max_number_of_llm_iterations> \
  --included-files "<optional_list_of_files_to_include>"
```

You can use the example code below to try out the Cover Agent.
(Note that the [usage_examples](docs/usage_examples.md) file provides more elaborate examples of how to use the Cover Agent)

#### Python

Follow the steps in the README.md file located in the `templated_tests/python_fastapi/` directory to setup an environment, then return to the root of the repository, and run the following command to add tests to the **python fastapi** example:
```shell
cover-agent \
  --source-file-path "templated_tests/python_fastapi/app.py" \
  --test-file-path "templated_tests/python_fastapi/test_app.py" \
  --project-root "templated_tests/python_fastapi" \
  --code-coverage-report-path "templated_tests/python_fastapi/coverage.xml" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --test-command-dir "templated_tests/python_fastapi" \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 10
```

#### Go
For an example using **go** `cd` into `templated_tests/go_webservice`, set up the project following the `README.md`.
To work with coverage reporting, you need to install `gocov` and `gocov-xml`. Run the following commands to install these tools:
```shell
go install github.com/axw/gocov/gocov@v1.1.0
go install github.com/AlekSi/gocov-xml@v1.1.0
```
and then run the following command:
```shell
cover-agent \
  --source-file-path "app.go" \
  --test-file-path "app_test.go" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml" \
  --test-command-dir $(pwd) \
  --coverage-type "cobertura" \
  --desired-coverage 70 \
  --max-iterations 1
```

#### Java
For an example using **java** `cd` into `templated_tests/java_gradle`, set up the project following the [README.md](templated_tests/java_gradle/README.md).
To work with jacoco coverage reporting, follow the [README.md](templated_tests/java_gradle/README.md) Requirements section:
and then run the following command:
```shell
cover-agent \
  --source-file-path="src/main/java/com/davidparry/cover/SimpleMathOperations.java" \
  --test-file-path="src/test/groovy/com/davidparry/cover/SimpleMathOperationsSpec.groovy" \
  --code-coverage-report-path="build/reports/jacoco/test/jacocoTestReport.csv" \
  --test-command="./gradlew clean test jacocoTestReport" \
  --test-command-dir=$(pwd) \
  --coverage-type="jacoco" \
  --desired-coverage=70 \
  --max-iterations=1
```

### Record & Replay Feature
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
  --docker-image "embeddeddevops/python_fastapi:latest" \
  --source-file-path "app.py" \
  --test-file-path "test_app.py" \
  --code-coverage-report-path "coverage.xml" \
  --test-command "pytest --cov=. --cov-report=xml --cov-report=term" \
  --coverage-type "cobertura" \
  --model "gpt-4o-mini" \
  --record-mode
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

### Outputs
A few debug files will be outputted locally within the repository (that are part of the `.gitignore`)
* `run.log`: A copy of the logger that gets dumped to your `stdout`
* `test_results.html`: A results table that contains the following for each generated test:
  * Test status
  * Failure reason (if applicable)
  * Exit code, 
  * `stderr`
  * `stdout`
  * Generated test

You can suppress logs using the `--suppress-log-files` flag. This prevents the creation of the `run.log`, `test_results.html`, and the test results `db` files.

### Additional logging
If you set an environment variable `WANDB_API_KEY`, the prompts, responses, and additional information will be logged to [Weights and Biases](https://wandb.ai/).

### Using other LLMs
This project uses LiteLLM to communicate with OpenAI and other hosted LLMs (supporting 100+ LLMs to date). To use a different model other than the OpenAI default you'll need to:
1. Export any environment variables needed by the supported LLM [following the LiteLLM instructions](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms).
2. Call the name of the model using the `--model` option when calling Cover Agent.

For example (as found in the [LiteLLM Quick Start guide](https://litellm.vercel.app/docs/proxy/quick_start#supported-llms)):
```shell
export VERTEX_PROJECT="hardy-project"
export VERTEX_LOCATION="us-west"

cover-agent \
  ...
  --model "vertex_ai/gemini-pro"
```

#### OpenAI Compatible Endpoint
```shell
export OPENAI_API_KEY="<your api key>" # If <your-api-base> requires an API KEY, set this value.

cover-agent \
  ...
  --model "openai/<your model name>" \
  --api-base "<your-api-base>"
```

#### Azure OpenAI Compatible Endpoint
```shell
export AZURE_API_BASE="<your api base>" # azure api base
export AZURE_API_VERSION="<your api version>" # azure api version (optional)
export AZURE_API_KEY="<your api key>" # azure api key

cover-agent \
  ...
  --model "azure/<your deployment name>"
```


## Contributing
See [Contributing](CONTRIBUTING.md) for more information on how to contribute to this project.

## Documentation
* [Instructions for Adding Another Coverage Type to the `CoverageProcessor` Class](docs/add_new_coverage_type_instructions.md)
* [Using a Test Database with Cover Agent](docs/database_usage.md)
* [Cover Agent Feature Flags](docs/features.md)
* [Repo Coverage](docs/repo_coverage.md)
* [Top Level Sequence Diagram](docs/top_level_sequence_diagram.md)
* [Usage Examples](docs/usage_examples.md)


## Roadmap
Below is the roadmap of planned features, with the current implementation status:

- [x] Automatically generates unit tests for your software projects, utilizing advanced AI models to ensure comprehensive test coverage and quality assurance. (similar to Meta)
  - [x] Being able to generate tests for different programming languages
  - [ ] Being able to deal with a large variety of testing scenarios
  - [ ] Generate a behavior analysis for the code under test, and generate tests accordingly
  - [x] Check test flakiness, e.g. by running 5 times as suggested by TestGen-LLM
- [ ] Cover more test generation pains
  - [ ] Generate new tests that are focused on the PR changeset
  - [ ] Run over an entire repo/code-base and attempt to enhance all existing test suites
- [ ] Improve usability
  - [ ] Connectors for GitHub Actions, Jenkins, CircleCI, Travis CI, and more
  - [ ] Integrate into databases, APIs, OpenTelemetry and other sources of data to extract relevant i/o for the test generation
  - [ ] Add a setting file


## QodoAI
QodoAI's mission is to enable busy dev teams to increase and maintain their code integrity.
We offer various tools, including "Pro" versions of our open-source tools, which are meant to handle enterprise-level code complexity and are multi-repo codebase aware.

**Try the pro version of [Qodo Cover in a GitHub Action](https://github.com/qodo-ai/qodo-ci)!**
