import functools
import logging
import socket
import sys
import os
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from src.config import config_instance


class AppLogger:
    def __init__(self, name: str, is_file_logger: bool = False, log_level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        self._add_stream_or_file_handler(is_file_logger)
        self._add_sentry_handler()

    def _add_stream_or_file_handler(self, is_file_logger: bool):
        if is_file_logger:
            logging_file = f'logs/{config_instance().LOGGING.filename}'
            os.makedirs(os.path.dirname(logging_file), exist_ok=True)
            handler = logging.FileHandler(logging_file)
        else:
            handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _add_sentry_handler(self):
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.INFO  # Send INFO as events
        )
        sentry_sdk.init(
            dsn=config_instance().SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            integrations=[sentry_logging]
        )

        # Sentry SDK does not use a traditional handler,
        # it's configured globally when initialized


@functools.lru_cache
def init_logger(name: str = "eod-stock-api"):
    """
    Initialize and return a logger instance.

    :param name: Name of the logger.
    :return: Logger instance.
    """
    is_development = socket.gethostname() == config_instance().DEVELOPMENT_SERVER_NAME
    logger = AppLogger(name=name, is_file_logger=not is_development, log_level=logging.INFO).logger
    return logger


# Example usage
if __name__ == "__main__":
    logger = init_logger('my_application')
    logger.info("This is an info message")
    logger.error("This is an error message")
