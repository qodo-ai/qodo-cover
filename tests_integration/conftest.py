import pytest
from cover_agent.settings.config_loader import get_settings

SETTINGS = get_settings().get("default")

def pytest_configure(config):
    """Add custom markers to pytest configuration."""
    config.addinivalue_line(
        "markers",
        "model: mark test to run with specific model",
    )

def pytest_addoption(parser):
    """Add custom command line options to pytest."""
    parser.addoption(
        "--model",
        action="store",
        default=SETTINGS.get("model"),
        help="Which LLM model to use",
        dest="model",
    )
    parser.addoption(
        "--record-mode",
        action="store_true",
        help="Enable record mode for LLM responses",
        dest="record_mode",
    )
    parser.addoption(
        "--suppress-log-files",
        action="store_true",
        help="Suppress all generated log files (HTML, logs, DB files)",
        dest="suppress_log_files",
    )

@pytest.fixture
def test_model(request):
    """Fixture to get the model from command line option."""
    return request.config.getoption("--model")
