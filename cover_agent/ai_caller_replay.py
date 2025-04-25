from typing import Optional

from cover_agent.CustomLogger import CustomLogger
from cover_agent.record_replay_manager import RecordReplayManager
from cover_agent.utils import stream_recorded_llm_response


class AICallerReplay:
    """A class that only handles replaying recorded LLM responses."""

    def __init__(
            self,
            source_file: str,
            test_file: str,
            record_replay_manager: Optional[RecordReplayManager]=None,
            logger: Optional[CustomLogger]=None
    ):
        self.source_file = source_file
        self.test_file = test_file
        self.record_replay_manager = record_replay_manager or RecordReplayManager(record_mode=False)
        self.logger = logger or CustomLogger.get_logger(__name__)

    def call_model(self, prompt: dict, stream=True):
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
        recorded_response = self.record_replay_manager.load_recorded_response(
            self.source_file,
            self.test_file,
            prompt,
        )

        if not recorded_response:
            msg = (
                f"No recorded response found for prompt hash in replay mode. "
                f"Source file: {self.source_file}, Test file: {self.test_file}."
            )
            self.logger.error(msg)
            raise KeyError(msg)

        content, prompt_tokens, completion_tokens = recorded_response
        replay_msg = "▶️  Replaying results from recorded LLM response...\n"

        if stream:
            self.logger.info(replay_msg)
            stream_recorded_llm_response(content)
        else:
            self.logger.info(replay_msg)
            print(content)

        return content, prompt_tokens, completion_tokens
