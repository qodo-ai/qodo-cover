import datetime
import os
import time

import litellm
from functools import wraps
from wandb.sdk.data_types.trace_tree import Trace
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from cover_agent import (
    NO_SUPPORT_TEMPERATURE_MODELS,
    USER_MESSAGE_ONLY_MODELS,
    NO_SUPPORT_STREAMING_MODELS,
)

MODEL_RETRIES = 3


def conditional_retry(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.enable_retry:
            return func(self, *args, **kwargs)

        @retry(stop=stop_after_attempt(MODEL_RETRIES), wait=wait_fixed(1))
        def retry_wrapper():
            return func(self, *args, **kwargs)

        return retry_wrapper()

    return wrapper


class AICaller:
    def __init__(
        self, model: str, api_base: str = "", enable_retry=True, max_tokens=16384
    ):
        """
        Initializes an instance of the AICaller class.

        Parameters:
            model (str): The name of the model to be used.
            api_base (str): The base API URL to use in case the model is set to Ollama or Hugging Face.
        """
        self.model = model
        self.api_base = api_base
        self.enable_retry = enable_retry
        self.max_tokens = max_tokens

        self.user_message_only_models = USER_MESSAGE_ONLY_MODELS
        self.no_support_temperature_models = NO_SUPPORT_TEMPERATURE_MODELS
        self.no_support_streaming_models = NO_SUPPORT_STREAMING_MODELS

    @conditional_retry  # You can access self.enable_retry here
    def call_model(self, prompt: dict, stream=True):
        """
        Call the language model with the provided prompt and retrieve the response.

        Parameters:
            prompt (dict): The prompt to be sent to the language model.
            stream (bool, optional): Whether to stream the response or not. Defaults to True.

        Returns:
            tuple: A tuple containing the response generated by the language model, the number of tokens used from the prompt, and the total number of tokens in the response.
        """
        if "system" not in prompt or "user" not in prompt:
            raise KeyError(
                "The prompt dictionary must contain 'system' and 'user' keys."
            )
        if prompt["system"] == "":
            messages = [{"role": "user", "content": prompt["user"]}]
        else:
            if self.model in self.user_message_only_models:
                # Combine system and user messages for models that only support user messages
                combined_content = (prompt["system"] + "\n" + prompt["user"]).strip()
                messages = [{"role": "user", "content": combined_content}]
            else:
                messages = [
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ]

        # Default completion parameters
        completion_params = {
            "model": self.model,
            "messages": messages,
            "stream": stream,  # Use the stream parameter passed to the method
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
        }

        # Remove temperature for models that don't support it
        if self.model in self.no_support_temperature_models:
            completion_params.pop("temperature", None)

        # Model-specific adjustments
        if self.model in self.no_support_streaming_models:
            stream = False
            completion_params["stream"] = False
            completion_params["max_completion_tokens"] = 2 * self.max_tokens
            # completion_params["reasoning_effort"] = "high"
            completion_params.pop("max_tokens", None)  # Remove 'max_tokens' if present

        # API base exception for OpenAI Compatible, Ollama, and Hugging Face models
        if (
            "ollama" in self.model
            or "huggingface" in self.model
            or self.model.startswith("openai/")
        ):
            completion_params["api_base"] = self.api_base

        try:
            response = litellm.completion(**completion_params)
        except Exception as e:
            print(f"Error calling LLM model: {e}")
            raise e

        if stream:
            chunks = []
            print("Streaming results from LLM model...")
            try:
                for chunk in response:
                    print(chunk.choices[0].delta.content or "", end="", flush=True)
                    chunks.append(chunk)
                    time.sleep(
                        0.01
                    )  # Optional: Delay to simulate more 'natural' response pacing

            except Exception as e:
                print(f"Error calling LLM model during streaming: {e}")
                if self.enable_retry:
                    raise e
            model_response = litellm.stream_chunk_builder(chunks, messages=messages)
            print("\n")
            # Build the final response from the streamed chunks
            content = model_response["choices"][0]["message"]["content"]
            usage = model_response["usage"]
            prompt_tokens = int(usage["prompt_tokens"])
            completion_tokens = int(usage["completion_tokens"])
        else:
            # Non-streaming response is a CompletionResponse object
            content = response.choices[0].message.content
            print(f"Printing results from LLM model...\n{content}")
            usage = response.usage
            prompt_tokens = int(usage.prompt_tokens)
            completion_tokens = int(usage.completion_tokens)

        if "WANDB_API_KEY" in os.environ:
            try:
                root_span = Trace(
                    name="inference_"
                    + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                    kind="llm",  # kind can be "llm", "chain", "agent", or "tool"
                    inputs={
                        "user_prompt": prompt["user"],
                        "system_prompt": prompt["system"],
                    },
                    outputs={"model_response": content},
                )
                root_span.log(name="inference")
            except Exception as e:
                print(f"Error logging to W&B: {e}")

        # Returns: Response, Prompt token count, and Completion token count
        return content, prompt_tokens, completion_tokens
