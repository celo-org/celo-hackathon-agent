"""
Logging utilities for Hackathon Agent.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable


class Logger:
    """
    Centralized logging utility for the Hackathon Agent.
    
    This class handles different verbosity levels and provides consistent 
    formatting for all log messages across the application.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the logger.
        
        Args:
            verbose: Whether to enable verbose logging
        """
        self.verbose = verbose
        self.timers: Dict[str, float] = {}
        
        # Colors for terminal output
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[92m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'yellow': '\033[93m',
            'magenta': '\033[95m',
            'red': '\033[91m'
        }
        
        # Set up file logging
        self._setup_file_logger()
    
    def _setup_file_logger(self):
        """Set up file logging with consistent format."""
        # File handler for detailed logging
        file_handler = logging.FileHandler("analysis.log")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Configure logger
        self.file_logger = logging.getLogger("hackathon_agent")
        self.file_logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Remove existing handlers if any
        if self.file_logger.handlers:
            self.file_logger.handlers.clear()
            
        self.file_logger.addHandler(file_handler)
        
        # Suppress logging from other libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("anthropic").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("google").setLevel(logging.WARNING)
    
    def start_timer(self, name: str):
        """
        Start a timer for measuring elapsed time for an operation.
        
        Args:
            name: Name of the timer for tracking multiple operations
        """
        self.timers[name] = time.time()
        
    def stop_timer(self, name: str) -> float:
        """
        Stop a timer and return the elapsed time.
        
        Args:
            name: Name of the timer to stop
            
        Returns:
            Elapsed time in seconds
        """
        if name not in self.timers:
            return 0.0
            
        elapsed = time.time() - self.timers[name]
        del self.timers[name]
        return elapsed
    
    def info(self, message: str, step: Optional[str] = None):
        """
        Log an informational message, always shown regardless of verbose mode.
        
        Args:
            message: The message to log
            step: Optional step name (for timing operations)
        """
        # Always log to file
        self.file_logger.info(message)
        
        # Format terminal output
        if step:
            self.start_timer(step)
            formatted = f"{self.colors['cyan']}⚡ {self.colors['bold']}{step}:{self.colors['reset']} {message}"
        else:
            formatted = message
            
        print(formatted)
    
    def step_complete(self, step: str):
        """
        Log completion of a step with elapsed time.
        
        Args:
            step: The step that completed
        """
        elapsed = self.stop_timer(step)
        
        # Log to file
        self.file_logger.info(f"Completed {step} in {elapsed:.2f}s")
        
        # Print to terminal
        formatted = f"{self.colors['green']}✓ {self.colors['bold']}{step}:{self.colors['reset']} completed in {self.colors['yellow']}{elapsed:.2f}s{self.colors['reset']}"
        print(formatted)
    
    def debug(self, message: str):
        """
        Log a debug message, only shown in verbose mode.
        
        Args:
            message: The message to log
        """
        # Always log to file
        self.file_logger.debug(message)
        
        # Only print in verbose mode
        if self.verbose:
            formatted = f"{self.colors['magenta']}🔍 {message}{self.colors['reset']}"
            print(formatted)
    
    def warn(self, message: str):
        """
        Log a warning message, always shown.
        
        Args:
            message: The warning message
        """
        # Log to file
        self.file_logger.warning(message)
        
        # Print to terminal
        formatted = f"{self.colors['yellow']}⚠️  {message}{self.colors['reset']}"
        print(formatted)
    
    def error(self, message: str, exc_info: bool = False):
        """
        Log an error message, always shown.
        
        Args:
            message: The error message
            exc_info: Whether to include exception info
        """
        # Log to file
        self.file_logger.error(message, exc_info=exc_info)
        
        # Print to terminal
        formatted = f"{self.colors['red']}❌ {message}{self.colors['reset']}"
        print(formatted)
    
    def progress_callback(self, name: str) -> Callable[[str], None]:
        """
        Create a progress callback function for a specific operation.
        
        Args:
            name: Name of the operation
            
        Returns:
            Callback function that accepts status updates
        """
        def callback(message: str):
            if self.verbose:
                status = f"{self.colors['cyan']}⏳ {self.colors['bold']}{name}:{self.colors['reset']} {message}"
                print(status)
                
            # Always log to file
            self.file_logger.debug(f"{name}: {message}")
            
        return callback

# Create a global logger instance that can be imported
logger = Logger(verbose=False)

def configure_logger(verbose: bool = False):
    """
    Configure the global logger instance.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    global logger
    logger = Logger(verbose=verbose)