import hashlib
import os

import yaml

from pathlib import Path
from typing import Any, Optional

import tests_integration.constants as constants
from cover_agent.CustomLogger import CustomLogger


class RecordReplayManager:
    HASH_DISPLAY_LENGTH = 12

    def __init__(
            self, record_mode: bool, base_dir: str=constants.RESPONSES_FOLDER, logger: Optional[CustomLogger]=None
    ) -> None:
        self.base_dir = Path(base_dir)
        self.record_mode = record_mode
        self.files_hash = None
        self.logger = logger or CustomLogger.get_logger(__name__)

        self.logger.info(
            f"✨ RecordReplayManager initialized in {'Run and Record' if record_mode else 'Run or Replay'} mode."
        )

    def has_response_file(self, source_file: str, test_file: str) -> bool:
        """
        Check if a response file exists for the current configuration.

        Returns:
            bool: True if a response file exists, False otherwise.

        Raises:
            FileNotFoundError: If source_file or test_file is not set
        """
        if not source_file or not test_file:
            raise FileNotFoundError("Source file and test file paths must be set to check response file existence")

        response_file = self._get_response_file_path(source_file, test_file)
        exists = response_file.exists()

        if exists:
            self.logger.debug(f"Found recorded LLM response file: {response_file}")
        else:
            self.logger.debug(f"Recorded LLM response file not found: {response_file}")

        return exists

    def load_recorded_response(
            self, source_file: str, test_file: str, prompt: dict[str, Any]
    ) -> Optional[tuple[str, int, int]]:
        """
        Load a recorded response if available.

        This method retrieves a previously recorded response from a YAML file based on the
        provided source file, test file, and prompt. If the response is found, it returns
        the response text along with the number of tokens in the prompt and the response.

        Args:
            source_file (str): The path to the source file.
            test_file (str): The path to the test file.
            prompt (dict[str, Any]): The prompt data used to generate the response.

        Returns:
            Optional[tuple[str, int, int]]: A tuple containing the response text, the number
            of tokens in the prompt, and the number of tokens in the response, or None if
            no recorded response is found.
        """
        if self.record_mode:
            self.logger.debug("Skipping record loading in record mode.")
            return None

        response_file = self._get_response_file_path(source_file, test_file)
        if not response_file.exists():
            self.logger.debug(f"Recorded response file not found: {response_file}.")
            return None

        try:
            with open(response_file, "r") as f:
                cached_data = yaml.safe_load(f)

            prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
            self.logger.info(f"Looking for prompt hash: {prompt_hash[:self.HASH_DISPLAY_LENGTH]}...")

            if prompt_hash in cached_data:
                self.logger.info(f"Record hit for prompt hash {prompt_hash[:self.HASH_DISPLAY_LENGTH]}.")
                entry = cached_data[prompt_hash]
                return entry["response"], entry["prompt_tokens"], entry["completion_tokens"]

            self.logger.info(f"No record entry found for prompt hash {prompt_hash[:self.HASH_DISPLAY_LENGTH]}.")
        except Exception as e:
            self.logger.error(f"Error loading recorded LLM response {e}", exc_info=True)
        return None

    def record_response(
            self,
            source_file: str,
            test_file: str,
            prompt: dict[str, Any],
            response: str,
            prompt_tokens: int,
            completion_tokens: int,
    ) -> None:
        """
        Record a response to a file.

        This method saves a response, along with its associated prompt and metadata, to a YAML file.
        The file is uniquely identified by a hash of the source and test file paths. If the file already
        exists, the method updates it with the new response data.

        Args:
            source_file (str): The path to the source file.
            test_file (str): The path to the test file.
            prompt (dict[str, Any]): The prompt data used to generate the response.
            response (str): The generated response to be recorded.
            prompt_tokens (int): The number of tokens in the prompt.
            completion_tokens (int): The number of tokens in the response.

        Returns:
            None
        """
        if not self.record_mode:
            self.logger.info("Skipping LLM response record in replay mode.")
            return

        response_file = self._get_response_file_path(source_file, test_file)
        self.logger.info(f"Recording LLM response to {response_file}...")

        # Load existing data or create new
        cached_data = {}

        if response_file.exists():
            try:
                with open(response_file, "r") as f:
                    loaded_data = yaml.safe_load(f)
                    if isinstance(loaded_data, dict):
                        cached_data = loaded_data
                        self.logger.debug(f"Loaded existing LLM record with {len(cached_data)} entries.")
            except yaml.YAMLError:
                self.logger.warning(f"Invalid YAML in {response_file}, starting fresh.")

        # Create entry
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        self.logger.info(f"🔴 Recording new LLM response with prompt hash {prompt_hash[:self.HASH_DISPLAY_LENGTH]}...")

        cached_data[prompt_hash] = {
            "prompt": prompt,
            "response": response,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "files_hash": self._calculate_files_hash(source_file, test_file)
        }

        # Save to file
        with open(response_file, "w") as f:
            yaml.safe_dump(cached_data, f, sort_keys=False)
        self.logger.debug(f"Record file updated successfully.")

    def _calculate_files_hash(self, source_file: str, test_file: str) -> str:
        """
        Calculate the combined SHA-256 hash of the source and test files.

        This method reads the contents of the provided source and test files, computes their
        individual SHA-256 hashes, and combines them to generate a unique hash for both files.
        If the hash has already been calculated, it returns the cached value.

        Args:
            source_file (str): The path to the source file.
            test_file (str): The path to the test file.

        Returns:
            str: The combined SHA-256 hash of the source and test files.
        """
        # Return cached hash if already calculated
        if self.files_hash:
            self.logger.debug(f"Using cached files hash {self.files_hash}.")
            return self.files_hash

        self.logger.debug(f"Calculating hash for files {source_file} and {test_file}...")
        with open(source_file, "rb") as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()
        with open(test_file, "rb") as f:
            test_hash = hashlib.sha256(f.read()).hexdigest()

        self.files_hash = hashlib.sha256((source_hash + test_hash).encode()).hexdigest()
        self.logger.info(f"Generated new files hash {self.files_hash[:self.HASH_DISPLAY_LENGTH]}.")
        return self.files_hash

    def _get_response_file_path(self, source_file: str, test_file: str) -> Path:
        """
        Generate the file path for storing responses based on the source and test files.

        This method creates a subdirectory within the base directory (if it doesn't already exist),
        calculates a unique hash for the source and test files, and constructs the file path
        using the hash and an optional test name from the environment variable `TEST_NAME`.

        Args:
            source_file (str): The path to the source file.
            test_file (str): The path to the test file.

        Returns:
            Path: The absolute path to the response file.
        """
        response_dir = self.base_dir  # Create the subdirectory path
        response_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        files_hash = self._calculate_files_hash(source_file, test_file)  # Calculate the combined hash
        test_name = os.getenv("TEST_NAME", "default")  # Use TEST_NAME env variable or default to "default"

        # For debug needs when running tests not in a container. May be removed in the future.
        if test_name == "default":
            test_name = Path(source_file).parts[-2] if len(Path(source_file).parts) >= 2 else test_name

        # Get the absolute file path
        response_file_path = (self.base_dir / f"{test_name}_responses_{files_hash}.yml").resolve()
        self.logger.info(f"Response file path {response_file_path}.")

        return response_file_path
