from threading import Lock
from tiktoken import get_encoding


class TokenEncoder:
    _encoder_instance = None
    _model = None
    _lock = Lock()  # Create a lock object

    @classmethod
    def get_token_encoder(cls):
        if (
            cls._encoder_instance is None
        ):  # Check without acquiring the lock for performance
            with cls._lock:  # Lock acquisition to ensure thread safety
                if cls._encoder_instance is None:
                    cls._encoder_instance = get_encoding(
                        "o200k_base"
                    )  # for now, we use the same encoder for all models
        return cls._encoder_instance


class TokenHandler:
    def __init__(self):
        self.encoder = TokenEncoder.get_token_encoder()

    def count_tokens(self, patch: str) -> int:
        return len(self.encoder.encode(patch))


def clip_tokens(
    text: str,
    max_tokens: int,
    add_three_dots=True,
    num_input_tokens=None,
    delete_last_line=False,
) -> str:
    if not text:
        return text

    try:
        if num_input_tokens is None:
            encoder = TokenEncoder.get_token_encoder()
            num_input_tokens = len(encoder.encode(text))
        if num_input_tokens <= max_tokens:
            return text
        if max_tokens <= 0:
            return ""

        # calculate the number of characters to keep
        num_chars = len(text)
        chars_per_token = num_chars / num_input_tokens
        factor = 0.9  # reduce by 10% to be safe
        num_output_chars = int(factor * chars_per_token * max_tokens)

        # clip the text
        if num_output_chars > 0:
            clipped_text = text[:num_output_chars]
            if delete_last_line:
                clipped_text = clipped_text.rsplit("\n", 1)[0]
            if add_three_dots:
                clipped_text += "\n...(truncated)"
        else:  # if the text is empty
            clipped_text = ""

        return clipped_text
    except Exception as e:
        print(f"Failed to clip tokens: {e}")
        return text
