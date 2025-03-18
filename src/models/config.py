"""
Configuration for the Celo Hackathon Analyzer.
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Config:
    """Configuration for the repository analyzer."""
    weights: Dict[str, float]
    celo_keywords: List[str]
    celo_files: List[str]
    default_model: str = "anthropic"
    model_name: str = "claude-3-haiku-20240307"
    temperature: float = 0.1
    
    @classmethod
    def from_file(cls, config_path: str = "config.json") -> 'Config':
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Config object with loaded settings
        """
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Get default model provider from config
        default_model = config_data.get("default_model", "anthropic")
        
        return cls(
            weights=config_data["weights"],
            celo_keywords=config_data["celo_keywords"],
            celo_files=config_data["celo_files"],
            default_model=default_model
        )