#!/usr/bin/env python3
"""
Celo Hackathon Analyzer using LangChain agent-based architecture.

This script is a legacy entry point that now redirects to run_agents.py for consistency.
"""

import os
import sys

def main():
    """Redirect to the new entry point."""
    print("Note: This script is deprecated. Using run_agents.py instead.")
    print("For direct access use: python run_agents.py [options]")
    print("\nRedirecting...")
    
    # Convert arguments to the new format and call run_agents.py
    args = sys.argv[1:]
    os.execv(sys.executable, [sys.executable, "run_agents.py"] + args)

if __name__ == "__main__":
    main()