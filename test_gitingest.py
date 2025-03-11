#!/usr/bin/env python3
"""
Test script for gitingest integration.
"""

import os
import json
from src.analyzer.github_repo import GitHubRepository
from src.models.config import Config

def test_gitingest():
    """Test the gitingest integration with a sample repository."""
    print("Testing gitingest integration...")
    
    # Create a config
    config = Config.from_file()
    
    # Create a repository instance
    repo = GitHubRepository(config)
    
    # Test with a public repository
    repo_url = "https://github.com/celo-org/celo-composer"
    
    print(f"Analyzing repository: {repo_url}")
    repo_owner, repo_name = repo.setup_repository(repo_url)
    print(f"Repository owner: {repo_owner}")
    print(f"Repository name: {repo_name}")
    
    # Get repository details
    print("\nFetching repository details...")
    repo_details = repo.get_repository_details()
    print(f"Repository details: {json.dumps(repo_details, indent=2)}")
    
    # Collect code samples with progress updates
    print("\nCollecting code samples...")
    def progress_callback(message):
        print(f"Progress: {message}")
    
    file_metrics, code_samples = repo.collect_code_samples(progress_callback)
    
    print(f"\nFile metrics: {json.dumps(file_metrics, indent=2)}")
    print(f"Collected {len(code_samples)} code samples")
    
    # Print first code sample
    if code_samples:
        print("\nFirst code sample:")
        print(code_samples[0][:500] + "...\n")
    
    # Test keyword search
    print("\nSearching for Celo keywords...")
    celo_keywords = ["celo", "contractkit", "wallet", "blockchain", "web3"]
    evidence = repo.search_files_for_keywords([], celo_keywords)
    
    print(f"Found {len(evidence)} matches for Celo keywords:")
    for i, match in enumerate(evidence[:5]):  # Show first 5 matches
        print(f"{i+1}. {match['keyword']} in {match['file']}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_gitingest()