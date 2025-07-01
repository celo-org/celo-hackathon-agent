"""
GitHub metrics module for the AI Project Analyzer.

This module handles fetching GitHub repository metrics like stars, forks, contributors,
programming languages, and other statistics using parallel processing.
"""

import logging
import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import concurrent.futures
from github import Github, Auth

logger = logging.getLogger(__name__)


class GithubMetricsFetcher:
    """
    Class for fetching GitHub repository metrics with parallel processing.
    """

    def __init__(self, token: Optional[str] = None, max_workers: int = 5):
        """
        Initialize the GitHub metrics fetcher.

        Args:
            token: GitHub personal access token (optional)
            max_workers: Maximum number of parallel workers
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.github = self._initialize_github()
        self.max_workers = max_workers
        logger.debug(f"GitHub metrics fetcher initialized with {max_workers} workers")

    def _initialize_github(self) -> Github:
        """
        Initialize the GitHub API client.

        Returns:
            Github: GitHub API client
        """
        if self.token:
            auth = Auth.Token(self.token)
            github = Github(auth=auth)
            logger.debug("GitHub client initialized with token")
        else:
            github = Github()
            logger.warning("GitHub client initialized without token (rate-limited)")

        return github

    def extract_repo_info_from_url(self, url: str) -> Tuple[str, str]:
        """
        Extract owner and repository name from a GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            Tuple[str, str]: Owner and repository name
        """
        # Remove trailing slashes
        url = url.rstrip("/")

        # Extract owner/repo part from GitHub URL
        pattern = r"github\.com[/:]([^/]+)/([^/]+)"
        match = re.search(pattern, url)

        if match:
            owner, repo = match.groups()
            # Remove .git suffix if present
            if repo.endswith(".git"):
                repo = repo[:-4]
            return owner, repo

        raise ValueError(f"Could not extract owner/repo from URL: {url}")

    def get_repository(self, url: str):
        """
        Get a GitHub repository from a URL.

        Args:
            url: GitHub repository URL

        Returns:
            Repository object
        """
        owner, repo_name = self.extract_repo_info_from_url(url)
        full_name = f"{owner}/{repo_name}"

        try:
            repo = self.github.get_repo(full_name)
            logger.debug(f"Fetched repository: {full_name}")
            return repo
        except Exception as e:
            logger.error(f"Error fetching repository {full_name}: {str(e)}")
            raise

    def fetch_metrics_for_repositories(self, repo_urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch metrics for multiple GitHub repositories in parallel.

        Args:
            repo_urls: List of repository URLs

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping repository names to their metrics
        """
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all repository fetching tasks
            future_to_url = {
                executor.submit(self.fetch_repository_metrics, url): url for url in repo_urls
            }

            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    owner, repo_name = self.extract_repo_info_from_url(url)
                    repo_key = f"{owner}/{repo_name}"
                    metrics = future.result()

                    results[repo_key] = metrics
                    logger.info(f"Successfully fetched metrics for {repo_key}")

                except Exception as e:
                    logger.error(f"Error fetching metrics for {url}: {str(e)}")

        logger.info(f"Fetched metrics for {len(results)} repositories successfully")
        return results

    def fetch_repository_metrics(self, url: str) -> Dict[str, Any]:
        """
        Fetch metrics for a GitHub repository using parallel processing for different metrics.

        Args:
            url: GitHub repository URL

        Returns:
            Dict[str, Any]: Repository metrics
        """
        repo = self.get_repository(url)

        # Basic repository metrics (fast, no need for parallelization)
        metrics = {
            "repository_metrics": {
                "stars": repo.stargazers_count,
                "watchers": repo.subscribers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
            },
            "repository_links": {
                "github_repository": repo.html_url,
                "owner_website": repo.owner.html_url,
                "created": repo.created_at.isoformat() if repo.created_at else None,
                "last_updated": repo.updated_at.isoformat() if repo.updated_at else None,
            },
        }

        # Fetch remaining metrics in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            # Submit tasks for metrics that require additional API calls
            contributors_future = executor.submit(self._count_contributors, repo)
            languages_future = executor.submit(self._get_language_distribution, repo)
            top_contributor_future = executor.submit(self._get_top_contributor, repo)
            pr_metrics_future = executor.submit(self._get_pull_request_metrics, repo)
            codebase_analysis_future = executor.submit(self.analyze_codebase, repo)
            celo_evidence_future = executor.submit(detect_celo_evidence, repo)

            # Wait for all futures to complete and collect results
            metrics["repository_metrics"]["total_contributors"] = contributors_future.result()
            metrics["language_distribution"] = languages_future.result()
            metrics["top_contributor"] = top_contributor_future.result()
            metrics["pr_status"] = pr_metrics_future.result()
            metrics["codebase_analysis"] = codebase_analysis_future.result()
            metrics["celo_evidence"] = celo_evidence_future.result()

        return metrics

    def _count_contributors(self, repo):
        """
        Count the total number of contributors to a repository.

        Args:
            repo: GitHub repository object

        Returns:
            int: Number of contributors
        """
        try:
            contributors = list(repo.get_contributors())
            return len(contributors)
        except Exception as e:
            logger.warning(f"Error counting contributors: {str(e)}")
            return 0

    def _get_language_distribution(self, repo):
        """
        Get the language distribution of a repository.

        Args:
            repo: GitHub repository object

        Returns:
            Dict[str, float]: Language distribution (percentages)
        """
        try:
            languages = repo.get_languages()
            total_bytes = sum(languages.values())

            # Convert byte counts to percentages
            if total_bytes > 0:
                return {
                    lang: round((bytes_count / total_bytes) * 100, 2)
                    for lang, bytes_count in languages.items()
                }
            return {}
        except Exception as e:
            logger.warning(f"Error getting language distribution: {str(e)}")
            return {}

    def _get_top_contributor(self, repo):
        """
        Get information about the top contributor to a repository.

        Args:
            repo: GitHub repository object

        Returns:
            Dict[str, str]: Top contributor information
        """
        try:
            contributors = list(repo.get_contributors())
            if not contributors:
                return {}

            # Get the contributor with the most commits
            top_contributor = contributors[0]
            user_data = {
                "name": top_contributor.name or top_contributor.login,
                "github": top_contributor.html_url,
                "company": top_contributor.company or "N/A",
                "location": top_contributor.location or "N/A",
                "twitter": top_contributor.twitter_username or "N/A",
                "website": top_contributor.blog or "N/A",
            }

            return user_data
        except Exception as e:
            logger.warning(f"Error getting top contributor: {str(e)}")
            return {}

    def _get_pull_request_metrics(self, repo):
        """
        Get pull request metrics for a repository.

        Args:
            repo: GitHub repository object

        Returns:
            Dict[str, int]: Pull request metrics
        """
        try:
            # Count open PRs
            open_prs = repo.get_pulls(state="open").totalCount

            # Count closed PRs
            closed_prs = repo.get_pulls(state="closed").totalCount

            # For merged PRs, we need to check each closed PR
            merged_prs = 0

            # Limit to a reasonable number to avoid API rate limits
            # Using parallel processing for better performance
            closed_pulls = list(repo.get_pulls(state="closed")[:100])

            # Only process if there are actually closed PRs
            if closed_pulls:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(10, len(closed_pulls))
                ) as executor:
                    # Check if each PR is merged in parallel
                    merged_results = list(executor.map(lambda pr: pr.merged, closed_pulls))
                    merged_prs = sum(1 for merged in merged_results if merged)

            # Estimate merged PRs percentage if we didn't check all
            if closed_prs > 100 and closed_pulls:
                merge_rate = merged_prs / len(closed_pulls)
                merged_prs = int(merge_rate * closed_prs)

            # Calculate total PRs
            total_prs = open_prs + closed_prs

            return {
                "open_prs": open_prs,
                "closed_prs": closed_prs,
                "merged_prs": merged_prs,
                "total_prs": total_prs,
            }
        except Exception as e:
            logger.warning(f"Error getting PR metrics: {str(e)}")
            return {
                "open_prs": 0,
                "closed_prs": 0,
                "merged_prs": 0,
                "total_prs": 0,
            }

    def analyze_codebase(self, repo) -> Dict[str, Any]:
        """
        Perform codebase analysis to identify strengths and weaknesses.

        Args:
            repo: GitHub repository object

        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            analysis = {"strengths": [], "weaknesses": [], "missing_features": [], "summary": ""}

            # Check activity and maintenance
            if repo.updated_at:
                days_since_update = (datetime.now() - repo.updated_at.replace(tzinfo=None)).days
                if days_since_update < 30:
                    analysis["strengths"].append(
                        "Active development (updated within the last month)"
                    )
                elif days_since_update < 180:
                    analysis["strengths"].append("Maintained (updated within the last 6 months)")
                else:
                    analysis["weaknesses"].append(
                        f"Limited recent activity (last updated {days_since_update} days ago)"
                    )

            # Check community engagement
            if repo.stargazers_count > 100:
                analysis["strengths"].append(
                    f"Strong community interest ({repo.stargazers_count} stars)"
                )
            elif repo.stargazers_count < 10:
                analysis["weaknesses"].append("Limited community adoption")

            if repo.forks_count > 50:
                analysis["strengths"].append(f"Active collaboration ({repo.forks_count} forks)")

            # Check issue tracking
            if repo.open_issues_count > 0:
                if repo.open_issues_count > 50:
                    analysis["weaknesses"].append(
                        f"Large number of open issues ({repo.open_issues_count})"
                    )
                elif repo.open_issues_count < 5:
                    analysis["strengths"].append("Few open issues")

            # Check documentation
            has_readme = False
            # Get wiki info but don't store it as variable
            _ = repo.has_wiki

            try:
                readme_content = repo.get_readme().decoded_content.decode("utf-8")
                has_readme = True

                # Check readme quality
                if len(readme_content) > 2000:
                    analysis["strengths"].append("Comprehensive README documentation")
                elif len(readme_content) < 500:
                    analysis["weaknesses"].append("Minimal README documentation")
            except Exception:
                analysis["weaknesses"].append("Missing README")

            try:
                docs_content = repo.get_contents("docs")
                if docs_content:
                    # Just add directly to strengths
                    analysis["strengths"].append("Dedicated documentation directory")
            except Exception:
                try:
                    docs_content = repo.get_contents("documentation")
                    if docs_content:
                        # Set flag but use it directly without storing
                        analysis["strengths"].append("Dedicated documentation directory")
                except Exception:
                    analysis["weaknesses"].append("No dedicated documentation directory")

            # Check for contributing guidelines
            try:
                repo.get_contents("CONTRIBUTING.md")
                analysis["strengths"].append("Clear contribution guidelines")
            except Exception:
                analysis["weaknesses"].append("Missing contribution guidelines")

            # Check for license
            try:
                repo.get_license()
                analysis["strengths"].append("Properly licensed")
            except Exception:
                analysis["weaknesses"].append("Missing license information")

            # Check testing
            has_tests = False
            try:
                # Just check existence, don't store content
                _ = repo.get_contents("tests") or repo.get_contents("test")
                has_tests = True
                analysis["strengths"].append("Includes test suite")
            except Exception:
                try:
                    _ = repo.get_contents("__tests__")
                    has_tests = True
                    analysis["strengths"].append("Includes test suite")
                except Exception:
                    analysis["weaknesses"].append("Missing tests")
                    analysis["missing_features"].append("Test suite implementation")

            # Check CI/CD
            has_ci = False
            try:
                workflows = repo.get_contents(".github/workflows")
                if workflows:
                    has_ci = True
                    analysis["strengths"].append("GitHub Actions CI/CD integration")
            except Exception:
                try:
                    travis = repo.get_contents(".travis.yml")
                    if travis:
                        has_ci = True
                        analysis["strengths"].append("Travis CI integration")
                except Exception:
                    try:
                        circleci = repo.get_contents(".circleci")
                        if circleci:
                            has_ci = True
                            analysis["strengths"].append("CircleCI integration")
                    except Exception:
                        analysis["weaknesses"].append("No CI/CD configuration")
                        analysis["missing_features"].append("CI/CD pipeline integration")

            # Check for configuration files
            has_config = False
            config_files = [".env.example", "config.json", "config.js", "config.py", ".env.sample"]
            for config_file in config_files:
                try:
                    repo.get_contents(config_file)
                    has_config = True
                    break
                except Exception:
                    pass

            if has_config:
                analysis["strengths"].append("Configuration management")
            else:
                analysis["missing_features"].append("Configuration file examples")

            # Check for containerization
            try:
                repo.get_contents("Dockerfile")
                analysis["strengths"].append("Docker containerization")
            except Exception:
                try:
                    repo.get_contents("docker-compose.yml")
                    analysis["strengths"].append("Docker containerization")
                except Exception:
                    analysis["missing_features"].append("Containerization")

            # Generate codebase breakdown summary
            good_points = min(10, len(analysis["strengths"]))
            bad_points = min(5, len(analysis["weaknesses"]))
            # No need to store this value
            # min(5, len(analysis["missing_features"]))

            summary = "The repository shows "
            if good_points > 7:
                summary += "strong development practices with "
            elif good_points > 4:
                summary += "decent development practices with "
            else:
                summary += "basic development practices with "

            if has_readme:
                summary += "documentation, "
            if has_tests:
                summary += "testing, "
            if has_ci:
                summary += "CI/CD integration, "

            summary = summary.rstrip(", ") + ". "

            if bad_points > 0:
                summary += (
                    f"Areas for improvement include {', '.join(analysis['weaknesses'][:3])}. "
                )

            if repo.stargazers_count > 0 or repo.forks_count > 0:
                summary += f"The project has gained community interest with {repo.stargazers_count} stars and {repo.forks_count} forks."

            analysis["summary"] = summary

            return analysis
        except Exception as e:
            logger.warning(f"Error analyzing codebase: {str(e)}")
            return {
                "strengths": [],
                "weaknesses": [],
                "missing_features": [],
                "summary": "Could not analyze codebase due to errors.",
            }


def detect_celo_evidence(repo) -> Dict[str, Any]:
    """
    Detect Celo integration evidence in a repository.

    Args:
        repo: GitHub repository object

    Returns:
        Dict[str, Any]: Evidence of Celo integration
    """
    try:
        evidence = {
            "celo_references": [],
            "alfajores_references": [],
            "contract_addresses": [],
            "celo_packages": [],
            "summary": "",
        }

        # Check in README first
        try:
            readme_content = repo.get_readme().decoded_content.decode("utf-8").lower()

            # Check for Celo mentions
            if "celo" in readme_content:
                evidence["celo_references"].append("README.md")

            # Check for Alfajores mentions
            if "alfajores" in readme_content:
                evidence["alfajores_references"].append("README.md")

            # Look for contract addresses with better context detection
            # First look for addresses near Celo keywords
            celo_context_pattern = (
                r"(?i)(?:celo|alfajores|baklava|contract|deploy|address).{0,100}(0x[a-fA-F0-9]{40})"
            )
            celo_context_addresses = re.findall(celo_context_pattern, readme_content)

            # Then look for all addresses as backup
            all_addresses = re.findall(r"0x[a-fA-F0-9]{40}", readme_content)

            # Combine addresses, prioritizing those with Celo context
            prioritized_addresses = list(dict.fromkeys(celo_context_addresses + all_addresses))

            if prioritized_addresses:
                evidence["contract_addresses"].append(
                    {
                        "file": "README.md",
                        "addresses": prioritized_addresses[:5],  # Limit to 5 addresses
                        "celo_context": len(celo_context_addresses) > 0,
                    }
                )
        except Exception as e:
            logger.warning(f"Error checking README: {str(e)}")

        # Check package.json for Celo dependencies
        try:
            package_json = repo.get_contents("package.json").decoded_content.decode("utf-8")
            package_data = json.loads(package_json)

            # Check dependencies
            all_deps = {}
            if "dependencies" in package_data:
                all_deps.update(package_data["dependencies"])
            if "devDependencies" in package_data:
                all_deps.update(package_data["devDependencies"])

            # Find Celo packages
            celo_deps = [dep for dep in all_deps.keys() if "celo" in dep.lower()]
            if celo_deps:
                evidence["celo_packages"] = celo_deps
        except Exception as e:
            logger.debug(f"Error checking package.json: {str(e)}")

        # Check for common config and contract files
        celo_related_paths = [
            "contracts",
            "src/contracts",
            "src/utils",
            "src/lib",
            "src/helpers",
            "src/services",
            "config",
            "src/config",
        ]

        for path in celo_related_paths:
            try:
                contents = repo.get_contents(path)
                # Handle directory vs file
                if not isinstance(contents, list):
                    contents = [contents]

                for content in contents:
                    if content.type == "file" and content.size < 100000:  # Skip large files
                        file_content = content.decoded_content.decode(
                            "utf-8", errors="ignore"
                        ).lower()

                        if (
                            "celo" in file_content
                            and content.path not in evidence["celo_references"]
                        ):
                            evidence["celo_references"].append(content.path)

                        if (
                            "alfajores" in file_content
                            and content.path not in evidence["alfajores_references"]
                        ):
                            evidence["alfajores_references"].append(content.path)

                        # Check for contract addresses with context
                        # Look for addresses near Celo keywords first
                        celo_context_pattern = r"(?i)(?:celo|alfajores|baklava|contract|deploy|address).{0,100}(0x[a-fA-F0-9]{40})"
                        celo_context_addresses = re.findall(celo_context_pattern, file_content)

                        # Then look for all addresses
                        all_addresses = re.findall(r"0x[a-fA-F0-9]{40}", file_content)

                        # Skip if no addresses found
                        if all_addresses and len(all_addresses) > 0:
                            # Prioritize addresses with Celo context
                            prioritized_addresses = list(
                                dict.fromkeys(celo_context_addresses + all_addresses)
                            )

                            evidence["contract_addresses"].append(
                                {
                                    "file": content.path,
                                    "addresses": prioritized_addresses[:5],  # Limit to 5 addresses
                                    "celo_context": len(celo_context_addresses) > 0,
                                }
                            )
            except Exception:
                # Path might not exist, just continue
                pass

        # Generate a summary
        summary_parts = []
        if evidence["celo_references"]:
            summary_parts.append(
                f"Celo references found in {len(evidence['celo_references'])} files"
            )
        if evidence["alfajores_references"]:
            summary_parts.append(
                f"Alfajores testnet references found in {len(evidence['alfajores_references'])} files"
            )
        if evidence["contract_addresses"]:
            summary_parts.append(
                f"Contract addresses found in {len(evidence['contract_addresses'])} files"
            )
        if evidence["celo_packages"]:
            summary_parts.append(f"Celo packages found: {', '.join(evidence['celo_packages'])}")

        if summary_parts:
            evidence["summary"] = ". ".join(summary_parts)
        else:
            evidence["summary"] = "No direct evidence of Celo integration found"

        return evidence
    except Exception as e:
        logger.warning(f"Error detecting Celo evidence: {str(e)}")
        return {
            "celo_references": [],
            "alfajores_references": [],
            "contract_addresses": [],
            "celo_packages": [],
            "summary": f"Error detecting Celo evidence: {str(e)}",
        }


def fetch_github_metrics(
    repo_urls: List[str], github_token: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch GitHub metrics for a list of repository URLs.

    Args:
        repo_urls: List of GitHub repository URLs
        github_token: GitHub personal access token (optional)

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping repository names to their metrics
    """
    fetcher = GithubMetricsFetcher(token=github_token)
    return fetcher.fetch_metrics_for_repositories(repo_urls)
