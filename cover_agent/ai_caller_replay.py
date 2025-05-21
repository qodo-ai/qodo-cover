import time

from typing import Optional

from cover_agent.custom_logger import CustomLogger
from cover_agent.record_replay_manager import RecordReplayManager
from cover_agent.utils import get_original_caller


class AICallerReplay:
    """A class that only handles replaying recorded LLM responses."""

    def __init__(
        self,
        source_file: str,
        test_file: str,
        record_replay_manager: Optional[RecordReplayManager] = None,
        logger: Optional[CustomLogger] = None,
        generate_log_files: bool = True,
    ):
        self.source_file = source_file
        self.test_file = test_file
        self.record_replay_manager = record_replay_manager or RecordReplayManager(record_mode=False)
        self.logger = logger or CustomLogger.get_logger(__name__, generate_log_files=generate_log_files)

    def call_model(self, prompt: dict, stream=True) -> tuple[str, int, int]:
        """
        Replay a recorded response for the given prompt.

        Parameters:
            prompt (dict): The prompt to find a matching recorded response for
            stream (bool, optional): Whether to stream the response. Defaults to True.

        Returns:
            tuple: (content, prompt_tokens, completion_tokens)

        Raises:
            KeyError: If no recorded response exists
        """
        caller_name = get_original_caller()

        recorded_response = self.record_replay_manager.load_recorded_response(
            self.source_file,
            self.test_file,
            prompt,
            caller_name=caller_name,
        )

        if not recorded_response:
            msg = (
                f"No recorded response found for prompt hash in replay mode. "
                f"Source file: {self.source_file}, Test file: {self.test_file}."
            )
            self.logger.error(msg)
            raise KeyError(msg)

        content, prompt_tokens, completion_tokens = recorded_response
        replay_msg = "▶️  Replaying results from recorded LLM response..."
        self.logger.info(replay_msg)
        if stream:
            self.stream_recorded_llm_response(content)
        else:
            print(content)

        return content, prompt_tokens, completion_tokens

    @staticmethod
    def stream_recorded_llm_response(content: str) -> None:
        """
        Stream and print the content of a recorded LLM response line by line with a slight delay for each word.

        Parameters:
        content (str): The content to be streamed and printed.

        Behavior:
        - Splits the input content into lines.
        - For each line:
            - If the line is empty, prints a blank line and continues.
            - Calculates the indentation of the line and prints it.
            - Splits the line into words and prints each word with a small delay.
        - Ensures the output maintains the original indentation and formatting.

        Example:
            stream_recorded_llm_response("Hello\n  World")
            Output:
            Hello
              World
        """
        for line in content.splitlines():
            if not line:
                print()
                continue

            indent = len(line) - len(line.lstrip())
            print(" " * indent, end="")

            for word in line.lstrip().split():
                print(word, end=" ", flush=True)
                time.sleep(0.01)

            print()
