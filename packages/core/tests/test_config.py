"""Tests for core configuration module."""

import os
from unittest.mock import patch


def test_config_imports():
    """Test that config module imports successfully."""
    from ..src.config import get_gemini_api_key, setup_logging

    assert setup_logging is not None
    assert get_gemini_api_key is not None


@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
def test_get_gemini_api_key():
    """Test getting Gemini API key from environment."""
    from ..src.config import get_gemini_api_key

    api_key = get_gemini_api_key()
    assert api_key == "test_key"


def test_setup_logging():
    """Test logging setup."""
    from ..src.config import setup_logging

    # Should not raise an exception
    setup_logging("INFO")
