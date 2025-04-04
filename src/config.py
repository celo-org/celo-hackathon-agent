"""
Configuration module for the AI Project Analyzer.
"""

import os
import logging
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variable names
GEMINI_API_KEY_ENV = "GOOGLE_API_KEY"
LOG_LEVEL_ENV = "LOG_LEVEL"
DEFAULT_MODEL_ENV = "DEFAULT_MODEL"
TEMPERATURE_ENV = "TEMPERATURE"

# Default values
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0.2


def get_gemini_api_key() -> str:
    """
    Get the Gemini API key from environment variables.

    Returns:
        str: The API key

    Raises:
        ValueError: If the API key is not set
    """
    api_key = os.getenv(GEMINI_API_KEY_ENV)
    if not api_key:
        raise ValueError(
            f"{GEMINI_API_KEY_ENV} environment variable is not set. "
            f"Please set it in your .env file or export it directly."
        )
    return api_key


def get_default_model() -> str:
    """
    Get the default model from environment variables or use the default.

    Returns:
        str: The default model name
    """
    return os.getenv(DEFAULT_MODEL_ENV, DEFAULT_MODEL)


def get_default_temperature() -> float:
    """
    Get the default temperature from environment variables or use the default.

    Returns:
        float: The default temperature
    """
    temp_str = os.getenv(TEMPERATURE_ENV)
    if temp_str:
        try:
            temp = float(temp_str)
            # Ensure temperature is in valid range
            return max(0.0, min(1.0, temp))
        except ValueError:
            return DEFAULT_TEMPERATURE
    return DEFAULT_TEMPERATURE


def get_default_log_level() -> str:
    """
    Get the default log level from environment variables or use the default.

    Returns:
        str: The default log level
    """
    return os.getenv(LOG_LEVEL_ENV, DEFAULT_LOG_LEVEL)


def get_config() -> Dict[str, Any]:
    """
    Get all configuration values.

    Returns:
        Dict[str, Any]: Dictionary with all configuration values
    """
    return {
        "api_key": get_gemini_api_key(),
        "model": get_default_model(),
        "temperature": get_default_temperature(),
        "log_level": get_default_log_level(),
    }


def setup_logging(level_name: Optional[str] = None) -> None:
    """
    Set up logging with the specified level.

    Args:
        level_name: The name of the logging level, or None to use default
    """
    if level_name is None:
        level_name = get_default_log_level()

    # Map string names to logging levels
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    level = level_map.get(level_name.upper(), logging.INFO)

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

    # Set third-party loggers to a higher level to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.debug(f"Logging initialized at level: {level_name}")
