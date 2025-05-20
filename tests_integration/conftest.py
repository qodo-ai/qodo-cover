import logging

from pathlib import Path

import pytest

from cover_agent.settings.config_loader import get_settings


SETTINGS = get_settings().get("default")


def pytest_configure(config: pytest.Config) -> None:
    # Suppress HTTPX logs
    logging.getLogger("httpx").setLevel(logging.WARNING)


def check_cover_agent_binary() -> None:
    """
    Checks if the cover-agent binary exists in the configured path.

    Raises:
        RuntimeError: If the cover-agent binary is not found in the expected location.
    """
    binary_path = Path(SETTINGS.get("cover_agent_host_folder"))
    if not binary_path.exists() or not binary_path.is_file():
        raise RuntimeError(
            f"cover-agent binary not found at {binary_path}. "
            f"Please build the binary using the tests_integration/build_installer.sh script before running tests."
        )
    else:
        logging.info(f"cover-agent binary found at {binary_path}.")


def pytest_sessionstart(session: pytest.Session) -> None:
    """
    Called after the Session object has been created and before performing collection
    and entering the run test loop.
    """
    markers = session.config.getoption("-m")

    # Check if binary exists only if the test is marked with 'e2e_docker'
    if markers == "e2e_docker":
        check_cover_agent_binary()


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Add custom command line options to pytest.

    Args:
        parser (pytest.Parser): The pytest parser object used to define custom command line options.
    """
    arg_definitions = [
        ("--model", dict(type=str, default=SETTINGS.get("model"), help="Which LLM model to use.")),
        ("--record-mode", dict(action="store_true", help="Enable record mode for LLM responses.")),
        (
            "--suppress-log-files",
            dict(action="store_true", help="Suppress all generated log files (HTML, logs, DB files)"),
        ),
    ]

    for name, kwargs in arg_definitions:
        parser.addoption(name, **kwargs)


@pytest.fixture
def llm_model(request: pytest.FixtureRequest) -> str:
    """Fixture to get the LLM model from command line option."""
    return request.config.getoption("--model")
