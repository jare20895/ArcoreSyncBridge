import logging


LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s message=%(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return

    logging.basicConfig(level=level, format=LOG_FORMAT)
