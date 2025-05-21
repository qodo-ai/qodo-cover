# Contributing

This document outlines the guidelines and best practices for contributing to the `qodo-cover` repository.

Thanks for taking the time to contribute!

When contributing to this repository, please first discuss the change you wish to make via an issue, email, or any other communication method with the repository maintainers before proceeding. Some issues may already be in progress, so make sure the issue you want to work on is not already assigned or being handled.

If you're new, we encourage you to take a look at issues tagged with "[good first issue](https://github.com/qodo-ai/qodo-cover/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22)".


## Start with the repository

1. Create a personal fork of the project using the GitHub UI.

2. Clone your fork to your local file system:
```bash
git clone git@github.com:<your_github_login>/qodo-cover.git
```

3. Add the original `qodo-cover` repository as the upstream remote:
```bash
git remote add upstream git@github.com:qodo-ai/qodo-cover.git
```

4. Check out the `main` branch:
```bash
git checkout main
```

5. Fetch the latest changes from upstream:
```bash
git fetch upstream
```

6. Reset your local `main` branch to match the upstream `main`:
```bash
git reset --hard upstream/main
```

## Start with an issue

1. Create a new branch based on the `main` branch. Use the GitHub issue number and a short name in the branch name:
```bash
git checkout -b feature/XXX-github-issue-name
```

2. Commit your changes with a clear and concise message explaining what was done:
```bash
git commit -m "Brief explanation of what was done"
```

3. Push the branch to your fork:
```bash
git push origin feature/XXX-github-issue-name
```

4. If another branch was recently merged into `main` and you need those changes, fetch the latest code and rebase your branch:
```bash
git fetch upstream
git rebase upstream/main
```

5. If there are merge conflicts, resolve them, stage the changes, and continue the rebase:
```bash
git add <conflicted_files>
git rebase --continue
```

6. Create a pull request in the GitHub UI. The title should include the feature number and a brief description — for example: `"Feature-331: Add CONTRIBUTING.md file to the project"`. Then, request a review from the appropriate reviewers.


## Pull request
For a better code review experience, provide a full description of what was done, including technical details and any relevant context.
Pull requests should be merged as **a single commit**. Use the “Squash and merge” option in the GitHub UI to do this.

## Versioning
Please don't forget to update the version in the `cover_agent/version.txt` file.  
The version should follow the format `X.Y.Z`, where:
- `X` is the **major version** — incremented for breaking or major changes  
- `Y` is the **minor version** — incremented for new top-level features  
- `Z` is the **patch version** — incremented for each feature improvement or bug fix
