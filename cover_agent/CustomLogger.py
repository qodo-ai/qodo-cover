import logging
import os


class CustomLogger:
    @classmethod
    def get_logger(cls, name, generate_logs=True):
        """
        Return a logger object with specified name.

        Parameters:
            name (str): The name of the logger.
            generate_logs (bool): Whether to generate log files.

        Returns:
            logging.Logger: The logger object.

        Note:
            This method sets up the logger to handle all messages of DEBUG level and above.
            It adds a file handler to write log messages to a file specified by 'log_file_path'
            and a stream handler to output log messages to the console. The log file is overwritten on each run.

        Example:
            logger = CustomLogger.get_logger('my_logger')
            logger.debug('This is a debug message')
            logger.info('This is an info message')
            logger.warning('This is a warning message')
            logger.error('This is an error message')
            logger.critical('This is a critical message')
        """
        log_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        logger = logging.getLogger(name)

        log_level = log_levels.get(os.environ.get("LOG_LEVEL", "").upper(), logging.DEBUG)

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
