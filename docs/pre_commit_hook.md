# qodo-cover: Pre-commit hooks #

To run additional checks before making commit we use [Pre-commit](https://pre-commit.com/) hooks.

`pre-commit` package is installed with backend requirements, so there is no need of [manual installation](https://pre-commit.com/#install).
But you need to generate the actual git pre-commit hook. It should be done only once:

```bash
poetry run pre-commit install
```

To run pre-commit hooks manually:

```bash
poetry run pre-commit run --all-files
```

Check staged files only:
```bash
poetry run pre-commit run
```

To run specific hook:

```bash
poetry run pre-commit run <hook_id>
```

See more info in official documentation:

* [Usage](https://pre-commit.com/#usage)
* [Adding new hooks](https://pre-commit.com/#plugins)
