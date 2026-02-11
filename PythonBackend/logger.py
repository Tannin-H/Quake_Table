import logging
import sys
from pathlib import Path


class Logger:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton class constructor"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file='app.log', log_level=logging.DEBUG, console_level=logging.INFO):
        """
        Initialize the logger.

        :param log_file: File to write logs to (default: 'app.log').
        :param log_level: Logging level for the file (default: logging.DEBUG).
        :param console_level: Logging level for the console (default: logging.INFO).
        """
        if self._initialized:
            return

        self.log_file = log_file
        self.log_level = log_level
        self.console_level = console_level
        self._setup_logger()
        self._initialized = True

    def _setup_logger(self):
        """Configure the root logger with file and console handlers."""
        # Ensure log directory exists
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler
        file_handler = logging.FileHandler(
            self.log_file,
            mode='a',
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.console_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    @staticmethod
    def get_logger(name=None):
        """
        Get a logger instance.

        :param name: Name of the logger (default: None for root logger).
        :return: Logger instance.
        """
        return logging.getLogger(name)