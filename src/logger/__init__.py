import functools
import logging
import socket
import sys
import os
from colorama import Fore, Style, init as colorama_init
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from src.config import config_instance

# Initialize colorama
colorama_init(autoreset=True)

# Define a dictionary of colors for specific loggers
LOGGER_COLORS = {
    "funeral-manager": Fore.GREEN,
    "MessagingController": Fore.BLUE,
    "NotificationsController": Fore.CYAN,
    "SubscriptionsController": Fore.LIGHTGREEN_EX,
    "CompanyController": Fore.LIGHTRED_EX,
    "EmailService": Fore.LIGHTBLUE_EX,
    "caching": Fore.LIGHTYELLOW_EX,
    "subscriptions_route_logger": Fore.LIGHTCYAN_EX
    # Add more loggers and colors as needed
}

class ColoredFormatter(logging.Formatter):
    def __init__(self, *args, logger_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_name = logger_name

    def format(self, record):
        # Use logger name to determine color
        log_color = LOGGER_COLORS.get(self.logger_name, Fore.WHITE)
        record.msg = f"{log_color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)


class AppLogger:
    def __init__(self, name: str, is_file_logger: bool = False, log_level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self._add_stream_or_file_handler(is_file_logger, name)
        self._add_sentry_handler()

    def _add_stream_or_file_handler(self, is_file_logger: bool, logger_name: str):
        if is_file_logger:
            logging_file = f'logs/{config_instance().LOGGING.filename}'
            os.makedirs(os.path.dirname(logging_file), exist_ok=True)
            handler = logging.FileHandler(logging_file)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        else:
            handler = logging.StreamHandler(sys.stdout)
            formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                                         logger_name=logger_name)

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    @staticmethod
    def _add_sentry_handler():
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send ERROR as events
        )
        sentry_sdk.init(
            dsn=config_instance().SENTRY_DSN,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            integrations=[sentry_logging]
        )


@functools.lru_cache
def init_logger(name: str = "funeral-manager"):
    """
    Initialize and return a logger instance.

    :param name: Name of the logger.
    :return: Logger instance.
    """
    is_development = socket.gethostname() == config_instance().DEVELOPMENT_SERVER_NAME
    return AppLogger(name=name, is_file_logger=not is_development, log_level=logging.INFO).logger


# Example usage
if __name__ == "__main__":
    logger = init_logger('my_application')
    logger.info("This is an info message")
    logger.error("This is an error message")

    another_logger = init_logger('another_logger')
    another_logger.info("This is an info message from another logger")
    another_logger.error("This is an error message from another logger")
