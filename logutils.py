import argparse
import logging

class SpecificLogFilter(logging.Filter):
    def __init__(self, target_name=None, target_func=None, target_lines=None):
        """
        A filter to only allow logs from specified classes, methods, or line numbers.

        Args:
            target_class (str): The name of the target class to log (optional).
            target_method (str): The name of the target method to log (optional).
            target_lines (list): A list of line numbers to log (optional).
        """
        super().__init__()
        self.target_name = target_name
        self.target_func = target_func
        self.target_lines = target_lines or []

    def filter(self, record):
        # Filter by module name
        # if self.target_class and self.target_class not in record.name:
        #     print(f"class {self.target_class} not in {record}")
        #     return False

        # Filter by method name
        if self.target_func and self.target_func != record.funcName:
            return False

        # Filter by line numbers
        if self.target_lines and record.lineno not in self.target_lines:
            return False
        return True  # Allow this log record




# Import your Python classes or modules here
# Example: from your_module import YourClass

def setup_logger(log_level=logging.DEBUG, filter_params={}):
    """
    Sets up the logger with optional custom filtering.

    Args:
        log_level (int): Global logging level.
        filter_params (dict): Parameters for the log filter.
    """
    logger = logging.getLogger()  # Root logger
    logger.setLevel(log_level)

    # Console handler for log output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)


    # Create a custom log filter and apply it based on arguments
    if filter_params:
        log_filter = SpecificLogFilter(
                target_name=filter_params.get("tname"),
                target_func=filter_params.get("tfunc"),
                target_lines=filter_params.get("tlines")
        )
        console_handler.addFilter(log_filter)

    # Simple log formatting
    console_formatter = logging.Formatter(
            "%(levelname)s [%(name)s:%(funcName)s:%(lineno)d]: %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    return logger

def parse_args():
    parser = argparse.ArgumentParser(description="Control specific logging at runtime.")
    parser.add_argument("--log_level", help="The logging level: INFO, DEBUG, CRITICAL, ...", type=str, default=logging.INFO)
    parser.add_argument("--tname", help="The name of the logger (module) for which to log debug messages.", type=str,
                        default=None)
    parser.add_argument("--tfunc", help="The function or method name for which to log debug messages.", type=str, default=None)
    parser.add_argument("--tlines", help="Comma-separated list of line numbers to log.", type=str, default=None)
    return parser.parse_args()
