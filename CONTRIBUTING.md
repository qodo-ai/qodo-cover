## Contributing

This document outlines the guidelines and best practices for contributing to the `qodo-cover` repository.

Thanks for taking the time to contribute!

When contributing to this repository, please first discuss the change you wish to make via an issue, email, or any other communication method with the repository maintainers before proceeding. Some issues may already be in progress, so make sure the issue you want to work on is not already assigned or being handled.

If you're new, we encourage you to take a look at issues tagged with "[good first issue](https://github.com/qodo-ai/qodo-cover/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22)".

### Table of Contents
* [Start With the Repository](#start-with-the-repository)
* [Start With an Issue](#start-with-an-issue)
* [Pull Request](#pull-request)
* [Versioning](#versioning)
* [Running Tests](#running-tests)
* [Running the App Locally From Source](#running-the-app-locally-from-source)
* 

### Start With the Repository

1. Create a personal fork of the `qodo-cover` project using the GitHub UI.

2. Execute these steps with the forked code:

```bash
# Clone your fork to your local file system
git clone git@github.com:<your_github_login>/qodo-cover.git

# Add the original `qodo-cover` repository as the upstream remote
git remote add upstream git@github.com:qodo-ai/qodo-cover.git

# Check out the `main` branch
git checkout main

# Fetch the latest changes from upstream
git fetch upstream

# Reset your local `main` branch to match the upstream `main`
git reset --hard upstream/main
```

### Start With an Issue

1. Create a new branch based on the `main` branch. Use the GitHub issue number and a short name in the branch name:
```bash
git checkout -b feature/XXX-github-issue-name
```

2. Stage your changes for commit using one of these commands:
```bash
# Stage all modified and new files
git add .

# Stage specific files
git add path/to/file1 path/to/file2

# Interactive staging
git add -p
```

3. Commit your changes with a clear and concise message explaining what was done:
```bash
git commit -m "Brief explanation of what was done"
```

4. Push the branch to your fork:
```bash
git push origin feature/XXX-github-issue-name
```

5. If another branch was recently merged into `main` and you need those changes, fetch the latest code and rebase your branch:
```bash
git fetch upstream
git rebase upstream/main
```

6. If there are merge conflicts, resolve them, stage the changes, and continue the rebase:
```bash
git add <conflicted_files>
git rebase --continue
```

7. Create a pull request in the GitHub UI. The title should include the feature number and a brief description — for example: `"Feature-331: Add CONTRIBUTING.md file to the project"`. Then, request a review from the appropriate reviewers.

### Pull Request
For a better code review experience, provide a full description of what was done, including technical details and any relevant context.
Pull requests should be merged as **a single commit**. Use the “Squash and merge” option in the GitHub UI to do this.

### Versioning
Before merging to main make sure to manually increment the version number in `cover_agent/version.txt` at the root of the repository.

### Running Tests
Set up your development environment by running the `poetry install` command as you did above. 

Note: for older versions of Poetry you may need to include the `--dev` option to install Dev dependencies.

After setting up your environment run the following command:
```shell
poetry run pytest --junitxml=testLog.xml --cov=templated_tests --cov=cover_agent --cov-report=xml --cov-report=term --log-cli-level=INFO
```
This will also generate all logs and output reports that are generated in `.github/workflows/ci_pipeline.yml`.

### Running the App Locally From Source

#### Prerequisites
- Python 3.x
- Poetry

#### Steps
1. If not already done, install the dependencies
```shell
poetry install
```

2. Let Poetry manage / create the environment
```shell
poetry shell
```

3. Run the app
```shell
poetry run cover-agent \
 --source-file-path <path_to_source_file> \
 [other_options...]
```

Notice that you're prepending `poetry run` to your `cover-agent` command. Replace `<path_to_your_source_file>` with the
actual path to your source file. Add any other necessary options as described in
the [Running the Code](#running-the-code) section.

### Building the binary locally
You can build the binary locally simply by invoking the `make installer` command. This will run PyInstaller locally on your machine. Ensure that you have set up the poetry project first (i.e. running `poetry install`).
