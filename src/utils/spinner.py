"""
Spinner and progress indicator utilities.
"""

import time
import threading
from typing import Callable, Any, Dict, Tuple


class Spinner:
    """Animated spinner for CLI progress indication."""
    
    def __init__(self, message: str = "Loading"):
        """
        Initialize the spinner.
        
        Args:
            message: Initial message to display
        """
        self.message = message
        # Simple spinner frames that work consistently across terminals
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.fallback_frames = ["-", "\\", "|", "/"]  # Fallback if unicode doesn't display well
        self.delay = 0.1
        self.is_spinning = False
        self.index = 0
        self.start_time = time.time()
        self.spinner_thread = None
        
        # Color setup
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[92m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'yellow': '\033[93m',
            'magenta': '\033[95m'
        }
        
        # Choose the appropriate frame set based on terminal capability
        try:
            # Try printing a unicode character
            print("\u2588", end="", flush=True)
            print("\r", end="", flush=True)  # Clear the test character
            self.current_frames = self.frames
        except UnicodeEncodeError:
            # Fall back to simple ASCII frames if unicode isn't supported
            self.current_frames = self.fallback_frames
    
    def _spin(self):
        """Internal method that runs the spinner animation in a thread."""
        while self.is_spinning:
            self._render_frame()
            time.sleep(0.1)
    
    def _render_frame(self):
        """Render the current spinner frame with message."""
        # Update animation frame
        self.index = (self.index + 1) % len(self.current_frames)
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        
        # Format the message with elapsed time
        if "running for" in self.message or "completed in" in self.message:
            display_message = self.message
        else:
            display_message = f"{self.message} ({elapsed:.1f}s)"
        
        # Clear line completely first
        print("\r" + " " * 120, end="", flush=True)
        
        # Format with colors
        spinner = f"{self.colors['cyan']}{self.current_frames[self.index]}{self.colors['reset']}"
        formatted_message = f"{self.colors['bold']}{display_message}{self.colors['reset']}"
        
        # Print the spinner and message
        print(f"\r{spinner} {formatted_message}", end="", flush=True)
    
    def start(self):
        """Start the spinner animation."""
        if self.is_spinning:
            return
            
        self.is_spinning = True
        self.start_time = time.time()
        
        # Clear the line first
        print("\r" + " " * 120, end="", flush=True)
        
        # Initial frame
        spinner = f"{self.colors['cyan']}{self.current_frames[self.index]}{self.colors['reset']}"
        message = f"{self.colors['bold']}{self.message}{self.colors['reset']}"
        print(f"\r{spinner} {message}", end="", flush=True)
        
        # Start spinning in a separate thread
        self.spinner_thread = threading.Thread(target=self._spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
    
    def update(self, message: str = None):
        """
        Update the spinner with a new message.
        
        Args:
            message: New message to display
        """
        if message:
            self.message = message
    
    def stop(self, message: str = None):
        """
        Stop the spinner and display a final message.
        
        Args:
            message: Final message to display
        """
        # Stop the spinning thread
        self.is_spinning = False
        
        if self.spinner_thread and self.spinner_thread.is_alive():
            self.spinner_thread.join()
        
        final_message = message if message else self.message
        elapsed = time.time() - self.start_time
        
        # Clear line completely first
        print("\r" + " " * 120, end="", flush=True)
        
        # Choose icon based on message content
        if "Error" in final_message or "error" in final_message or "failed" in final_message:
            icon = f"{self.colors['yellow']}⚠️{self.colors['reset']}"  # Warning for errors
        else:
            icon = f"{self.colors['green']}✓{self.colors['reset']}"  # Checkmark for success
        
        message = f"{self.colors['bold']}{final_message}{self.colors['reset']}"
        elapsed_text = f"{self.colors['yellow']}(completed in {elapsed:.1f}s){self.colors['reset']}"
        
        print(f"\r{icon} {message} {elapsed_text}")
        
        return elapsed


def run_with_active_spinner(
    func: Callable, 
    args: Tuple = (), 
    kwargs: Dict = {}, 
    message: str = None, 
    callback: Callable = None,
    update_interval: float = 0.2
) -> Any:
    """
    Run a function while updating a spinner/progress indicator.
    
    Args:
        func: Function to run
        args: Arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
        message: Message to display in the spinner
        callback: Callback function for updating the spinner
        update_interval: Interval for spinner updates
        
    Returns:
        The result of the function
    """
    # If we don't have a callback, create and manage our own spinner
    if callback is None:
        spinner = Spinner(message or "Processing...")
        spinner.start()
        
        try:
            # Run the function
            result = func(*args, **kwargs)
            spinner.stop("Completed successfully")
            return result
        except Exception as e:
            spinner.stop(f"Error: {str(e)}")
            raise e
    
    # If we have a callback, use it to update an existing spinner
    else:
        # Original message
        original_message = message
        
        # Initial spinner update
        if message:
            callback(f"{message}")
        
        # Wrapper for the callback that preserves the context
        def progress_update_wrapper(update_message):
            # If the update is just the original message, ignore it
            if update_message == original_message:
                return
            
            # Forward the update to the actual callback
            callback(update_message)
        
        # Directly run the function
        start_time = time.time()
        try:
            # Execute the function - if the function takes a callback for progress updates,
            # it will use our wrapper callback
            result = func(*args, **kwargs)
            
            # Update spinner after completion only if there wasn't a final update from the function
            elapsed = time.time() - start_time
            if message and original_message:
                callback(f"{original_message} (completed in {elapsed:.1f}s)")
                
            return result
        except Exception as e:
            # Update spinner with error
            elapsed = time.time() - start_time
            if message:
                callback(f"{message} - Error: {str(e)}")
            raise e