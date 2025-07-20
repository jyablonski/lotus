import logging
import sys


def setup_logging():
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # or DEBUG for more verbosity

    # Console handler for stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Log message format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)

    logger.addHandler(ch)
