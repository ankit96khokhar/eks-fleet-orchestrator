import logging
import os
from logging.handlers import RotatingFileHandler


class LoggerFactory:
    """
    Centralized logger factory.
    Ensures single logger instance across application.
    """

    @staticmethod
    def get_logger(name: str = "eks-fleet") -> logging.Logger:

        logger = logging.getLogger(name)

        if logger.handlers:
            return logger  # Prevent duplicate handlers

        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler (rotating)
        os.makedirs("logs", exist_ok=True)

        file_handler = RotatingFileHandler(
            "logs/fleet.log",
            maxBytes=5_000_000,
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger
