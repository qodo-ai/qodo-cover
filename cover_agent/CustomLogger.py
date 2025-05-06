import logging
import os


class CustomLogger:
    VALID_LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    @classmethod
    def get_logger(cls, name, generate_logs=True):
        """
        Return a logger object with specified name.

        Parameters:
            name (str): The name of the logger.
            generate_logs (bool): Whether to generate log files.

        Returns:
            logging.Logger: The logger object.

        Raises:
            ValueError: If LOG_LEVEL environment variable contains invalid value.
        """
        logger = logging.getLogger(name)

        # Get LOG_LEVEL from environment, default to empty string if not set
        env_log_level = os.environ.get("LOG_LEVEL", "").upper()

        # Check if provided log level is valid when it's not empty
        if env_log_level and env_log_level not in cls.VALID_LOG_LEVELS:
            valid_levels = ", ".join(cls.VALID_LOG_LEVELS.keys())
            raise ValueError(f"Invalid LOG_LEVEL: {env_log_level}. Valid levels are: {valid_levels}")

        log_level = cls.VALID_LOG_LEVELS.get(env_log_level, logging.DEBUG)
        logger.setLevel(log_level)

        # Specify the log file path
        log_file_path = "run.log"

        # Check if handlers are already set up to avoid adding them multiple times
        if not logger.handlers:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            # Only add file handler if file generation is enabled
            if generate_logs:
                # File handler for writing to a file. Use 'w' to overwrite the log file on each run
                file_handler = logging.FileHandler(log_file_path, mode="w")
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

            # Stream handler for output to the console
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

            # Prevent log messages from being propagated to the root logger
            logger.propagate = False

        return logger
