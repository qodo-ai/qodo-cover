import sys

from os.path import abspath, dirname, exists, join

from dynaconf import Dynaconf


SETTINGS_FILES = [
    "test_generation_prompt.toml",
    "language_extensions.toml",
    "analyze_suite_test_headers_indentation.toml",
    "analyze_suite_test_insert_line.toml",
    "analyze_test_run_failure.toml",
    "analyze_test_against_context.toml",
    "adapt_test_command_for_a_single_test_via_ai.toml",
    "configuration.toml",
]


class SingletonSettings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SingletonSettings, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """
        Initialize the SingletonSettings instance by loading settings from the specified configuration files.
        Check if the 'settings' attribute is not already set, then construct the paths to the settings files based on the current directory.
        Ensure that all settings files exist by checking their presence using the 'os.path.exists' function.
        If any of the settings files are missing, raise a 'FileNotFoundError' with a message indicating the missing file.
        Finally, initialize the 'settings' attribute with a Dynaconf instance using the specified settings files and configuration options.

        Parameters:
            self: SingletonSettings
                The SingletonSettings instance to be initialized.

        Raises:
            FileNotFoundError: If any of the specified settings files are not found.

        Returns:
            None
        """
        if not hasattr(self, "settings"):
            # Determine the base directory for bundled app or normal environment
            base_dir = getattr(sys, "_MEIPASS", dirname(abspath(__file__)))

            settings_files = [join(base_dir, f) for f in SETTINGS_FILES]

            # Ensure all settings files exist
            for file_path in settings_files:
                if not exists(file_path):
                    raise FileNotFoundError(f"Settings file not found: {file_path}")

            self.settings = Dynaconf(
                envvar_prefix=False, merge_enabled=True, settings_files=settings_files
            )


def get_settings() -> Dynaconf:
    return SingletonSettings().settings
