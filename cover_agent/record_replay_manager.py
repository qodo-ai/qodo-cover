import hashlib
import os

import yaml

from pathlib import Path
from typing import Any, Optional

from fuzzywuzzy import fuzz

from cover_agent.CustomLogger import CustomLogger
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import truncate_hash



class RecordReplayManager:
    """
    A manager class for recording and replaying responses.

    This class handles the logic for recording responses to YAML files and replaying them
    based on a hash of the source file, test file, and prompt. It supports both "record"
    and "replay" modes and ensures consistent hash truncation for file names and YAML keys.

    Attributes:
        HASH_DISPLAY_LENGTH (int): The length to which hashes are truncated for display and storage.
        base_dir (Path): The base directory where response files are stored.
        record_mode (bool): Indicates whether the manager is in record mode.
        files_hash (Optional[str]): Cached hash of the source and test files.
        logger (CustomLogger): Logger instance for logging messages.
    """
    SETTINGS = get_settings().get("default")
    HASH_DISPLAY_LENGTH = SETTINGS.record_replay_hash_display_length

    def __init__(
        self,
        record_mode: bool,
        base_dir: str=SETTINGS.responses_folder,
        logger: Optional[CustomLogger]=None,
        generate_log_files: bool=True,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.record_mode = record_mode
        self.files_hash = None
        self.logger = logger or CustomLogger.get_logger(__name__, generate_log_files=generate_log_files)

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
        self,
        source_file: str,
        test_file: str,
        prompt: dict[str, Any],
        caller_name: str="unknown_caller",
        fuzzy_lookup: bool=True,
    ) -> tuple[str, int, int] | None:
        """
        Load a recorded response if available.

        This method retrieves a previously recorded response from a YAML file based on the
        provided source file, test file, and prompt. If the response is found, it returns
        the response text along with the number of tokens in the prompt and the response.

        Args:
            source_file (str): The path to the source file.
            test_file (str): The path to the test file.
            prompt (dict[str, Any]): The prompt data used to generate the response.
            caller_name (str): The name of the caller.
            fuzzy_lookup (bool): If True, the fuzzy lookup will be applied.

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
            self.logger.debug(f"Recorded LLM response file not found: {response_file}.")
            return None

        try:
            with open(response_file, "r") as f:
                cached_data = yaml.safe_load(f)

            # Check if caller_name exists
            if caller_name not in cached_data:
                self.logger.info(f"No records found for caller {caller_name}.")
                return None

            caller = f"{caller_name}()"
            prompt_hash = truncate_hash(hashlib.sha256(str(prompt).encode()).hexdigest(), self.HASH_DISPLAY_LENGTH)
            self.logger.info(f"Do a direct hash lookup for prompt hash {prompt_hash} under caller {caller}...")

            # Look for the prompt hash in the caller's records
            if prompt_hash in cached_data[caller_name]:
                self.logger.info(f"Record hit for caller {caller_name}() with prompt hash {prompt_hash}.")
                entry = cached_data[caller_name][prompt_hash]
                return entry["response"], entry["prompt_tokens"], entry["completion_tokens"]

            self.logger.info(
                f"No record entry found for prompt hash {prompt_hash} under caller {caller}."
            )

            if fuzzy_lookup:
                self.logger.info(f"Trying fuzzy lookup for prompt hash {prompt_hash} under caller {caller}...")
                prompts = {k: v["prompt"]["user"] for k, v in cached_data[caller_name].items()}
                fuzzy_prompt_hash = self._find_closest_prompt_match(prompt["user"], prompts)
                if fuzzy_prompt_hash:
                    self.logger.info(f"Found fuzzy match for prompt hash {fuzzy_prompt_hash} under caller {caller}.")
                    entry = cached_data[caller_name][fuzzy_prompt_hash]

                    return entry["response"], entry["prompt_tokens"], entry["completion_tokens"]
                else:
                    self.logger.warning(
                        f"No record entry found for prompt hash {fuzzy_prompt_hash} under caller {caller} "
                        f"after fuzzy lookup."
                    )

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
        caller_name: str="unknown_caller",
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
            caller_name (str): The name of the caller.

        Returns:
            None
        """
        if not self.record_mode:
            self.logger.info("Skipping LLM response record in replay mode.")
            return

        response_file = self._get_response_file_path(source_file, test_file)
        self.logger.info(f"Recording LLM response to {response_file}...")

        # Load existing data or create new
        meta_key_name = "metadata"
        files_hash = truncate_hash(self._calculate_files_hash(source_file, test_file), self.HASH_DISPLAY_LENGTH)
        cached_data = {meta_key_name: {"files_hash": files_hash}}

        if response_file.exists():
            try:
                with open(response_file, "r") as f:
                    loaded_data = yaml.safe_load(f)
                    if isinstance(loaded_data, dict):
                        # Preserve metadata and merge other data
                        cached_data.update({k: v for k, v in loaded_data.items() if k != meta_key_name})
                        self.logger.debug(f"Loaded existing LLM record with {len(cached_data) - 1} entries.")
            except yaml.YAMLError:
                self.logger.warning(f"Invalid YAML in {response_file}, starting fresh.")

        # Create entry
        prompt_hash = truncate_hash(hashlib.sha256(str(prompt).encode()).hexdigest(), self.HASH_DISPLAY_LENGTH)
        self.logger.info(f"🔴 Recording new LLM response for {caller_name}() (prompt hash {prompt_hash})...")

        if caller_name not in cached_data:
            cached_data[caller_name] = {}

        cached_data[caller_name][f"{prompt_hash}"] = {
            "prompt": prompt,
            "response": response,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

        # Save to file
        os.makedirs(os.path.dirname(response_file), exist_ok=True)
        with open(response_file, "w") as f:
            yaml.safe_dump(cached_data, f, sort_keys=False)
        self.logger.info(f"Record file updated successfully.")

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
            self.logger.debug(f"Using cached files hash {truncate_hash(self.files_hash, self.HASH_DISPLAY_LENGTH)}.")
            return self.files_hash

        self.logger.debug(f"Calculating hash for files {source_file} and {test_file}...")
        with open(source_file, "rb") as f:
            source_hash = hashlib.sha256(f.read()).hexdigest()
        with open(test_file, "rb") as f:
            test_hash = hashlib.sha256(f.read()).hexdigest()

        self.files_hash = hashlib.sha256((source_hash + test_hash).encode()).hexdigest()
        self.logger.info(f"Generated new files hash {truncate_hash(self.files_hash, self.HASH_DISPLAY_LENGTH)}.")
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
        # Create the subdirectory path
        response_dir = self.base_dir

        # Ensure the directory exists
        response_dir.mkdir(parents=True, exist_ok=True)

        # Calculate the combined hash
        files_hash = truncate_hash(self._calculate_files_hash(source_file, test_file), self.HASH_DISPLAY_LENGTH)
        test_name = os.getenv("TEST_NAME", "default")  # Use TEST_NAME env variable or default to "default"

        # For debug needs when running tests not in a container. May be removed in the future.
        if test_name == "default":
            test_name = Path(source_file).parts[-2] if len(Path(source_file).parts) >= 2 else test_name

        # Get the absolute file path
        response_file_path = (self.base_dir / f"{test_name}_responses_{files_hash}.yml").resolve()
        self.logger.info(f"Response file path {response_file_path}.")

        return response_file_path

    def _find_closest_prompt_match(
        self,
        current_prompt: str,
        recorded_prompts: dict,
        threshold: int = SETTINGS.fuzzy_lookup_threshold,
        prefix_length: Optional[int] = SETTINGS.fuzzy_lookup_prefix_length,
        best_ratio: int = SETTINGS.fuzzy_lookup_best_ratio,
    ) -> str | None:
        """Find the closest matching recorded prompt using fuzzy string matching.

        Args:
            current_prompt: The current prompt text to match
            recorded_prompts: Dictionary of recorded prompts with their hashes as keys
            threshold: Minimum similarity ratio (0-100) required for a match
            prefix_length: Minimum length of prefix to match against, if None uses full prompt
            best_ratio: Best ratio of matching records

        Returns:
            Hash of the closest matching prompt if found and above threshold, None otherwise
        """
        self.logger.info(f"Starting fuzzy prompt matching with {len(recorded_prompts)} recorded prompts...")
        self.logger.info(f"Matching threshold set to {threshold}.")

        # Use full prompt if prefix_length is None, otherwise use prefix
        current_text = (
            current_prompt[:prefix_length]
            if prefix_length and len(current_prompt) > prefix_length
            else current_prompt
        )

        best_match = None
        for prompt_hash, prompt_data in recorded_prompts.items():
            recorded_text = (
                prompt_data[:prefix_length]
                if prefix_length and len(prompt_data) > prefix_length
                else prompt_data
            )

            # Calculate a similarity ratio using token sort to handle reordered text
            ratio = fuzz.token_sort_ratio(current_text, recorded_text)
            self.logger.info(f"Comparing with {prompt_hash}: similarity ratio={ratio}...")

            if ratio > best_ratio:
                self.logger.info(f"New best match found for prompt hash {prompt_hash} with ratio {ratio}.")
                best_ratio = ratio
                best_match = prompt_hash

        result = best_match if best_ratio >= threshold else None
        self.logger.info(f"Final result: best_ratio={best_ratio}, match={'found' if result else 'not found'}")

        return result
