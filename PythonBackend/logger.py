import logging
import sys

class Logger:
    def __init__(self, log_file='app.log', log_level=logging.INFO, console_level=logging.INFO):
        """
        Initialize the logger.

        :param log_file: File to write logs to (default: 'app.log').
        :param log_level: Logging level for the file (default: logging.INFO).
        :param console_level: Logging level for the console (default: logging.INFO).
        """
        self.log_file = log_file
        self.log_level = log_level
        self.console_level = console_level

        # Configure the root logger
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=self.log_file,
            filemode='a',  # Append mode
            encoding='utf-8'
        )

        # Add a StreamHandler to print logs to stdout
        self._add_console_handler()

    def _add_console_handler(self):
        """Add a console handler to the root logger."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

    @staticmethod
    def get_logger(name=None):
        """
        Get a logger instance.

        :param name: Name of the logger (default: None, which returns the root logger).
        :return: Logger instance.
        """
        return logging.getLogger(name)