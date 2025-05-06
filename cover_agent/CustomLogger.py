import logging


class CustomLogger:

    @classmethod
    def get_logger(cls, name, generate_log_files=True, file_level=logging.INFO, console_level=logging.INFO):
        """
        Return a logger object with specified name.

        Parameters:
            name (str): The name of the logger.
            generate_log_files (bool): Whether to generate log files.
            file_level (int): The log level to use.
            console_level (int): The log level to use.

        Returns:
            logging.Logger: The logger object.

        Note:
            This method sets up the logger to handle all messages of DEBUG level and above.
            It adds a file handler to write log messages to a file specified by 'log_file_path' and a stream handler
            to output log messages to the console. The log file is overwritten on each run.

        Example:
            logger = CustomLogger.get_logger('my_logger')
            logger.debug('This is a debug message')
            logger.info('This is an info message')
            logger.warning('This is a warning message')
            logger.error('This is an error message')
            logger.critical('This is a critical message')
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Specify the log file path
        log_file_path = "run.log"

        # Check if handlers are already set up to avoid adding them multiple times
        if not logger.handlers:
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            # Only add file handler if file generation is enabled
            if generate_log_files:
                # File handler for writing to a file. Use 'w' to overwrite the log file on each run
                file_handler = logging.FileHandler(log_file_path, mode="w")
                file_handler.setLevel(file_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

            # Stream handler for output to the console
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(console_level)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

            # Prevent log messages from being propagated to the root logger
            logger.propagate = False

        return logger
