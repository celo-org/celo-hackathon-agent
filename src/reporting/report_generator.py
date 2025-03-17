"""
Report generation module for the Celo Hackathon Analyzer.
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, List, Any
from tqdm import tqdm
from datetime import datetime

from src.utils.spinner import Spinner

# Configure logger
logger = logging.getLogger(__name__)

def format_date(date_string: str) -> str:
    """Format ISO date string to a more readable format."""
    if not date_string or date_string == 'N/A':
        return 'N/A'
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except Exception:
        return date_string
    
def format_size(size_kb: int) -> str:
    """Format size in KB to a more readable format."""
    if size_kb < 1024:
        return f"{size_kb} KB"
    elif size_kb < 1024 * 1024:
        return f"{size_kb / 1024:.1f} MB"
    else:
        return f"{size_kb / (1024 * 1024):.2f} GB"
    
def calculate_project_totals(repo_details: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate combined metrics for all repositories in a project."""
    totals = {
        "stars": 0,
        "forks": 0,
        "open_issues": 0,
        "contributors": 0,
        "commits": 0,
        "languages": {},
        "first_commit": None,
        "latest_commit": None,
        "commit_frequency": 0
    }
    
    repo_count = len(repo_details)
    if repo_count == 0:
        return totals
    
    for repo in repo_details:
        # Sum up numeric metrics
        totals["stars"] += repo.get("stars", 0)
        totals["forks"] += repo.get("forks", 0)
        totals["open_issues"] += repo.get("open_issues", 0)
        totals["contributors"] += repo.get("total_contributors", 0)
        
        # Combine commit stats
        commit_stats = repo.get("commit_stats", {})
        totals["commits"] += commit_stats.get("total_commits", 0)
        
        # Track first and latest commits across all repos
        first_commit = commit_stats.get("first_commit_date", "")
        latest_commit = commit_stats.get("latest_commit_date", "")
        
        if first_commit:
            if not totals["first_commit"] or first_commit < totals["first_commit"]:
                totals["first_commit"] = first_commit
        
        if latest_commit:
            if not totals["latest_commit"] or latest_commit > totals["latest_commit"]:
                totals["latest_commit"] = latest_commit
        
        # Combine language stats
        for lang, percentage in repo.get("main_languages", {}).items():
            if lang in totals["languages"]:
                totals["languages"][lang] += percentage / repo_count
            else:
                totals["languages"][lang] = percentage / repo_count
    
    # Sort languages
    totals["languages"] = dict(sorted(
        totals["languages"].items(),
        key=lambda x: x[1],
        reverse=True
    ))
    
    # Limit to top 5 languages
    totals["languages"] = dict(list(totals["languages"].items())[:5])
    
    # Round language percentages
    totals["languages"] = {
        lang: round(pct, 1) for lang, pct in totals["languages"].items()
    }
    
    # Calculate overall commit frequency
    totals["commit_frequency"] = sum(
        repo.get("commit_stats", {}).get("commit_frequency", 0) 
        for repo in repo_details
    ) / repo_count
    
    return totals


def clean_urls(urls: List[str]) -> List[str]:
    """
    Clean up URL strings that might have artifacts from data processing.
    
    Args:
        urls: List of URLs that might contain formatting artifacts
        
    Returns:
        List of cleaned URLs
    """
    clean_urls = []
    for url in urls:
        # Check if it's a string that might contain list formatting like "['url']"
        if isinstance(url, str) and url.startswith("['") and url.endswith("']"):
            # Extract the actual URL from inside the quotes and brackets
            clean_url = url.strip("[]'")
            clean_urls.append(clean_url)
        else:
            clean_urls.append(url)
    return clean_urls


def generate_summary_report(results: List[Dict[str, Any]], output_path: str):
    """
    Generate a summary report with all projects.
    
    Args:
        results: List of project analysis results
        output_path: Path to write the summary report
    """
    with open(output_path, "w") as f:
        f.write("# Celo Hackathon Project Analysis Summary\n\n")
        
        # Create an enhanced summary table with more metrics
        f.write("| Project | Score | Celo Integration | Stars | Forks | Contributors | Commits | Repos | GitHub URL |\n")
        f.write("|---------|-------|------------------|-------|-------|--------------|---------|-------|------------|\n")

        for result in results:
            project_name = result["project_name"]
            
            # Handle multiple GitHub URLs
            if "github_urls" in result and result["github_urls"]:
                # For multiple URLs, show the first one with a link and note the count
                github_urls = result["github_urls"]
                repo_count = len(github_urls)
                if len(github_urls) > 1:
                    github_url_display = f"[Link]({github_urls[0]}) +{len(github_urls)-1}"
                else:
                    github_url_display = f"[Link]({github_urls[0]})"
            else:
                # Fallback to the original field if github_urls isn't available
                github_url = result["project_github_url"]
                github_url_display = f"[Link]({github_url})"
                repo_count = 1

            # Get code quality score
            score_display = "0.00"
            if "analysis" in result and "code_quality" in result["analysis"]:
                code_quality = result["analysis"]["code_quality"]
                if isinstance(code_quality, dict) and "overall_score" in code_quality:
                    score = code_quality["overall_score"]
                    repos_analyzed = code_quality.get("repositories_analyzed", 1)
                    # Simplified score display
                    score_display = f"{score:.2f}"
                elif isinstance(code_quality, (int, float)):
                    score = code_quality
                    score_display = f"{score:.2f}"

            # Get Celo integration status
            celo_status = "❌"
            if "analysis" in result and "celo_integration" in result["analysis"]:
                celo_integration = result["analysis"]["celo_integration"]
                if isinstance(celo_integration, dict) and "integrated" in celo_integration:
                    celo_integrated = celo_integration["integrated"]
                    repos_with_celo = celo_integration.get("repositories_with_celo", 0)
                elif isinstance(celo_integration, bool):
                    celo_integrated = celo_integration
                    repos_with_celo = 1 if celo_integrated else 0
                else:
                    celo_integrated = False
                    repos_with_celo = 0
                
                # Show Celo integration status with repository count if multiple repositories
                if "github_urls" in result and len(result["github_urls"]) > 1:
                    celo_status = f"{'✅' if celo_integrated else '❌'} ({repos_with_celo}/{len(result['github_urls'])})"
                else:
                    celo_status = "✅" if celo_integrated else "❌"
            
            # Get repository metrics
            stars = 0
            forks = 0
            contributors = 0
            commits = 0
            
            if "analysis" in result and "repo_details" in result["analysis"]:
                repo_details = result["analysis"]["repo_details"]
                if isinstance(repo_details, list):
                    # Calculate totals across all repositories
                    for repo in repo_details:
                        stars += repo.get("stars", 0)
                        forks += repo.get("forks", 0)
                        contributors += repo.get("total_contributors", 0)
                        commits += repo.get("commit_stats", {}).get("total_commits", 0)
                elif isinstance(repo_details, dict):
                    # Single repository
                    stars = repo_details.get("stars", 0)
                    forks = repo_details.get("forks", 0)
                    contributors = repo_details.get("total_contributors", 0)
                    commits = repo_details.get("commit_stats", {}).get("total_commits", 0)

            f.write(
                f"| {project_name} | {score_display} | {celo_status} | {stars} | {forks} | {contributors} | {commits} | {repo_count} | {github_url_display} |\n"
            )
            
        # Add a summary footer
        f.write("\n## Overview\n\n")
        f.write("This report provides a comprehensive analysis of all projects submitted to the Celo Hackathon. ")
        f.write("Each project has been evaluated for code quality, Celo blockchain integration, and various repository metrics.\n\n")
        
        f.write("### Metrics Explanation:\n\n")
        f.write("- **Score**: Overall code quality score (0-100)\n")
        f.write("- **Celo Integration**: Whether the project integrates with Celo blockchain\n")
        f.write("- **Stars**: Total GitHub stars across all repositories\n")
        f.write("- **Forks**: Total number of forks across all repositories\n")
        f.write("- **Contributors**: Total unique contributors\n")
        f.write("- **Commits**: Total number of commits\n")
        f.write("- **Repos**: Number of GitHub repositories\n\n")
        
        f.write("For detailed information on each project, please refer to the individual project reports.")


def extract_technology_highlights(result: Dict[str, Any]) -> List[str]:
    """
    Extract technology highlights from repository data and code quality analysis.
    
    Args:
        result: Project analysis results
        
    Returns:
        List of technology highlights
    """
    highlights = []
    
    # Check if we have repo details
    if "analysis" not in result or "repo_details" not in result["analysis"]:
        return highlights
    
    repo_details = result["analysis"]["repo_details"]
    if not repo_details:
        return highlights
    
    # Get language information
    languages = {}
    if isinstance(repo_details, list):
        # Combine languages from all repos
        for repo in repo_details:
            for lang, pct in repo.get('main_languages', {}).items():
                if lang in languages:
                    languages[lang] += pct
                else:
                    languages[lang] = pct
    elif isinstance(repo_details, dict):
        languages = repo_details.get('main_languages', {})
    
    # Add primary languages as highlights
    for lang, pct in languages.items():
        if lang.lower() in ['javascript', 'typescript', 'python', 'java', 'rust', 'solidity', 'go']:
            if lang.lower() == 'javascript':
                highlights.append(f"Language: {lang}")
            elif lang.lower() == 'typescript':
                highlights.append(f"Language: {lang}")
            elif lang.lower() == 'python':
                highlights.append(f"Language: {lang}")
            elif lang.lower() == 'solidity':
                highlights.append(f"Smart Contracts: Solidity")
            else:
                highlights.append(f"Language: {lang}")
    
    # Check for Celo integration
    if "celo_integration" in result.get("analysis", {}):
        celo_integration = result["analysis"]["celo_integration"]
        if isinstance(celo_integration, dict) and celo_integration.get("integrated", False):
            highlights.append("Blockchain Network: Celo")
    
    # Get potential technologies from code quality analysis
    code_quality = result.get("analysis", {}).get("code_quality", {})
    ai_analysis = code_quality.get("ai_analysis", {})
    
    # Extract from overall analysis if available
    overall_analysis = ai_analysis.get("overall_analysis", "")
    
    # Check for specific technologies in the analysis text
    tech_keywords = {
        "react": "Frontend: React",
        "next.js": "Frontend: Next.js",
        "vue": "Frontend: Vue.js",
        "angular": "Frontend: Angular",
        "express": "Backend: Express.js",
        "node.js": "Backend: Node.js",
        "flask": "Backend: Flask",
        "django": "Backend: Django",
        "fastapi": "Backend: FastAPI",
        "mongodb": "Database: MongoDB",
        "postgres": "Database: PostgreSQL",
        "mysql": "Database: MySQL",
        "sqlite": "Database: SQLite",
        "redis": "Database: Redis",
        "prisma": "ORM: Prisma",
        "typeorm": "ORM: TypeORM",
        "sequelize": "ORM: Sequelize",
        "graphql": "API: GraphQL",
        "rest api": "API: REST",
        "docker": "DevOps: Docker",
        "kubernetes": "DevOps: Kubernetes",
        "aws": "Cloud: AWS",
        "azure": "Cloud: Azure",
        "google cloud": "Cloud: Google Cloud",
        "metamask": "Wallet Integration: MetaMask",
        "wallet connect": "Wallet Integration: WalletConnect",
        "privy": "Wallet Integration: Privy",
        "web3.js": "Web3 Library: web3.js",
        "ethers.js": "Web3 Library: ethers.js",
        "hardhat": "Development: Hardhat",
        "truffle": "Development: Truffle",
        "foundry": "Development: Foundry",
        "tailwind": "UI: Tailwind CSS",
        "bootstrap": "UI: Bootstrap",
        "material ui": "UI: Material UI",
        "chakra ui": "UI: Chakra UI",
        "shadcn/ui": "UI: shadcn/ui",
        "styled-components": "UI: styled-components",
    }
    
    # Create search text combining project description and analysis
    search_text = (result.get("project_description", "") + " " + overall_analysis).lower()
    
    # Add matching technologies
    for keyword, tech_desc in tech_keywords.items():
        if keyword in search_text and tech_desc not in highlights:
            highlights.append(tech_desc)
    
    # Return unique highlights
    return list(set(highlights))

def generate_project_report(result: Dict[str, Any], output_path: str):
    """
    Generate a detailed report for a single project.
    
    Args:
        result: Project analysis results
        output_path: Path to write the project report
    """
    with open(output_path, "w") as f:
        f.write(f"# Project Analysis: {result['project_name']}\n\n")

        # Project Overview
        f.write("## Project Overview\n\n")
        f.write(f"**Project Name:** {result['project_name']}\n\n")
        f.write(f"**Project Description:** {result['project_description']}\n\n")
        
        # Handle None/NaN project_url
        project_url = result['project_url']
        if project_url is None or isinstance(project_url, float) and pd.isna(project_url):
            f.write(f"**Project URL:** Not available\n\n")
        else:
            f.write(f"**Project URL:** [{project_url}]({project_url})\n\n")
        
        # Add GitHub profiles of project owners/developers
        if "project_owner_github_url" in result and result["project_owner_github_url"]:
            owner_urls = clean_urls(result["project_owner_github_url"])
            
            if len(owner_urls) == 1:
                f.write(f"**Project Developer:** [{owner_urls[0]}]({owner_urls[0]})\n\n")
            elif len(owner_urls) > 1:
                f.write(f"**Project Developers:**\n\n")
                for i, url in enumerate(owner_urls):
                    f.write(f"{i+1}. [{url}]({url})\n")
                f.write("\n")
        
        # Handle multiple GitHub URLs
        if "github_urls" in result and result["github_urls"]:
            # List all GitHub URLs
            github_urls = result["github_urls"]
            if len(github_urls) == 1:
                f.write(f"**GitHub URL:** [{github_urls[0]}]({github_urls[0]})\n\n")
            else:
                f.write(f"**GitHub URLs:** ({len(github_urls)} repositories)\n\n")
                for i, url in enumerate(github_urls):
                    f.write(f"{i+1}. [{url}]({url})\n")
                f.write("\n")
        else:
            # Fallback to original format
            f.write(f"**GitHub URL:** [{result['project_github_url']}]({result['project_github_url']})\n\n")

        # Extract and display technology highlights
        tech_highlights = extract_technology_highlights(result)
        if tech_highlights:
            f.write("## Technical Highlights\n\n")
            for highlight in tech_highlights:
                f.write(f"- **{highlight}**\n")
            f.write("\n")

        # Repository details - handle multiple repositories
        if "analysis" in result and "repo_details" in result["analysis"]:
            repo_details = result["analysis"]["repo_details"]
            
            # Check if we have multiple repositories
            if isinstance(repo_details, list) and len(repo_details) > 0:
                f.write("## Repository Statistics\n\n")
                
                if len(repo_details) == 1:
                    # Single repository - show simple stats
                    repo = repo_details[0]
                    # Basic repository info
                    f.write(f"- **Repository:** {repo.get('name', 'N/A')}\n")
                    f.write(f"- **Created:** {format_date(repo.get('created_at', 'N/A'))}\n")
                    f.write(f"- **Last Updated:** {format_date(repo.get('last_update', 'N/A'))}\n")
                    f.write(f"- **License:** {repo.get('license_type', 'None')}\n")
                    f.write(f"- **Size:** {format_size(repo.get('size_kb', 0))}\n\n")
                    
                    # Repository metrics
                    f.write("### Repository Metrics\n\n")
                    f.write(f"- **Stars:** {repo.get('stars', 0)}\n")
                    f.write(f"- **Forks:** {repo.get('forks', 0)}\n")
                    f.write(f"- **Open Issues:** {repo.get('open_issues', 0)}\n")
                    f.write(f"- **Total Contributors:** {repo.get('total_contributors', 0)}\n")
                    
                    # Add PR stats if available
                    pr_stats = repo.get('pull_requests', {})
                    if pr_stats:
                        f.write("\n### Pull Request Statistics\n\n")
                        f.write(f"- **Open PRs:** {pr_stats.get('open', 0)}\n")
                        f.write(f"- **Closed PRs:** {pr_stats.get('closed', 0)}\n")
                        f.write(f"- **Merged PRs:** {pr_stats.get('merged', 0)}\n")
                        f.write(f"- **Total PRs:** {pr_stats.get('total', 0)}\n\n")
                    
                    # Commit Statistics
                    commit_stats = repo.get('commit_stats', {})
                    if commit_stats:
                        f.write(f"- **Total Commits:** {commit_stats.get('total_commits', 0)}\n")
                        f.write(f"- **First Commit:** {format_date(commit_stats.get('first_commit_date', ''))}\n")
                        f.write(f"- **Latest Commit:** {format_date(commit_stats.get('latest_commit_date', ''))}\n")
                        f.write(f"- **Average Commits per Week:** {commit_stats.get('commit_frequency', 0)}\n\n")
                    
                    # Language distribution
                    languages = repo.get('main_languages', {})
                    if languages:
                        f.write("### Language Distribution\n\n")
                        for lang, percentage in languages.items():
                            f.write(f"- **{lang}:** {percentage}%\n")
                        f.write("\n")
                    else:
                        f.write(f"- **Primary Language:** {repo.get('language', 'N/A')}\n\n")
                    
                    # Commit History Visualization (if available)
                    commit_history = commit_stats.get('commit_history', {})
                    if commit_history:
                        f.write("### Commit Activity\n\n")
                        f.write("```\n")
                        
                        # Create a basic ASCII chart of commit activity
                        max_commits = max(commit_history.values()) if commit_history else 0
                        if max_commits > 0:
                            for month, count in commit_history.items():
                                bar_length = int((count / max_commits) * 20)
                                bar = '█' * bar_length
                                f.write(f"{month}: {bar} {count}\n")
                        
                        f.write("```\n\n")
                    
                    # Top Contributors Details (with enhanced information)
                    detailed_contributors = repo.get('detailed_contributors', [])
                    if detailed_contributors:
                        num_contributors = min(5, len(detailed_contributors))
                        f.write(f"## Top {num_contributors} Contributors\n\n")
                        
                        # Display each contributor's details in a more comprehensive format
                        for i, contributor in enumerate(detailed_contributors[:num_contributors]):
                            username = contributor.get('username', 'N/A')
                            name = contributor.get('name', 'N/A')
                            if name == None: 
                                name = username
                            
                            f.write(f"### {i+1}. {name} (@{username})\n\n")
                            
                            # Basic info
                            profile_url = contributor.get('profile_url', '#')
                            contributions = contributor.get('contributions', 0)
                            f.write(f"- **GitHub:** [{username}]({profile_url})\n")
                            f.write(f"- **Contributions:** {contributions}\n")
                            
                            # Additional info if available
                            if contributor.get('company'):
                                f.write(f"- **Company:** {contributor.get('company')}\n")
                            if contributor.get('location'):
                                f.write(f"- **Location:** {contributor.get('location')}\n")
                            if contributor.get('twitter_username'):
                                twitter = contributor.get('twitter_username')
                                f.write(f"- **Twitter:** [@{twitter}](https://twitter.com/{twitter})\n")
                            if contributor.get('blog'):
                                blog = contributor.get('blog')
                                if not blog.startswith(('http://', 'https://')):
                                    blog = 'https://' + blog
                                f.write(f"- **Website:** [{blog}]({blog})\n")
                            if contributor.get('bio'):
                                f.write(f"- **Bio:** {contributor.get('bio')}\n")
                            
                            # Activity stats
                            f.write(f"- **Followers:** {contributor.get('followers', 0)}\n")
                            f.write(f"- **Following:** {contributor.get('following', 0)}\n")
                            f.write(f"- **Public Repositories:** {contributor.get('public_repos', 0)}\n")
                            f.write("\n")
                    
                    # Repository Contributors (fallback to old format if no detailed info)
                    elif repo.get('contributors', []):
                        contributors = repo.get('contributors', [])
                        total_contributors = repo.get('total_contributors', len(contributors))
                        
                        # Determine if we're showing all or just top contributors
                        if total_contributors > len(contributors):
                            f.write(f"### Top {len(contributors)} Contributors (of {total_contributors} total)\n\n")
                        else:
                            f.write("### Repository Contributors\n\n")
                            
                        f.write("| Username | Profile | Contributions |\n")
                        f.write("|----------|---------|---------------|\n")
                        
                        for contributor in contributors:
                            username = contributor.get('login', 'N/A')
                            profile_url = contributor.get('profile_url', '#')
                            contributions = contributor.get('contributions', 0)
                            
                            f.write(f"| {username} | [{profile_url}]({profile_url}) | {contributions} |\n")
                        f.write("\n")
                else:
                    # Calculate combined project metrics
                    project_totals = calculate_project_totals(repo_details)
                    
                    # Project Summary
                    f.write("### Project Summary\n\n")
                    f.write(f"- **Total Repositories:** {len(repo_details)}\n")
                    f.write(f"- **Total Stars:** {project_totals['stars']}\n")
                    f.write(f"- **Total Forks:** {project_totals['forks']}\n")
                    f.write(f"- **Total Contributors:** {project_totals['contributors']}\n")
                    f.write(f"- **Total Commits:** {project_totals['commits']}\n")
                    f.write(f"- **First Commit:** {format_date(project_totals['first_commit'])}\n")
                    f.write(f"- **Latest Commit:** {format_date(project_totals['latest_commit'])}\n")
                    f.write(f"- **Avg. Commit Frequency:** {round(project_totals['commit_frequency'], 2)} commits/week\n\n")
                    
                    # Combine PR stats across repos
                    total_prs = {"open": 0, "closed": 0, "merged": 0, "total": 0}
                    for repo in repo_details:
                        pr_stats = repo.get('pull_requests', {})
                        total_prs["open"] += pr_stats.get('open', 0)
                        total_prs["closed"] += pr_stats.get('closed', 0)
                        total_prs["merged"] += pr_stats.get('merged', 0)
                        total_prs["total"] += pr_stats.get('total', 0)
                    
                    if total_prs["total"] > 0:
                        f.write("### Pull Request Statistics\n\n")
                        f.write(f"- **Open PRs:** {total_prs['open']}\n")
                        f.write(f"- **Closed PRs:** {total_prs['closed']}\n")
                        f.write(f"- **Merged PRs:** {total_prs['merged']}\n")
                        f.write(f"- **Total PRs:** {total_prs['total']}\n\n")
                    
                    # Language distribution
                    languages = project_totals['languages']
                    if languages:
                        f.write("### Project Language Distribution\n\n")
                        for lang, percentage in languages.items():
                            f.write(f"- **{lang}:** {percentage}%\n")
                        f.write("\n")
                    
                    # Multiple repositories - create a detailed summary table
                    f.write("### Repositories\n\n")
                    f.write("| Repository | Stars | Forks | Issues | Contributors | Commits | Created | Last Updated |\n")
                    f.write("|------------|-------|-------|--------|--------------|---------|---------|-------------|\n")
                    
                    for repo in repo_details:
                        repo_name = repo.get('name', 'N/A')
                        stars = repo.get('stars', 0)
                        forks = repo.get('forks', 0)
                        issues = repo.get('open_issues', 0)
                        contributors = repo.get('total_contributors', 0)
                        commits = repo.get('commit_stats', {}).get('total_commits', 0)
                        created = format_date(repo.get('created_at', ''))
                        last_update = format_date(repo.get('last_update', ''))
                        
                        f.write(f"| {repo_name} | {stars} | {forks} | {issues} | {contributors} | {commits} | {created} | {last_update} |\n")
                    f.write("\n")
                    
                    # Collect all detailed contributors across repositories
                    all_detailed_contributors = []
                    for repo in repo_details:
                        detailed_contributors = repo.get('detailed_contributors', [])
                        if detailed_contributors:
                            all_detailed_contributors.extend(detailed_contributors)
                    
                    # If we have detailed contributors, display top 5
                    if all_detailed_contributors:
                        # Sort by contributions and take top 5
                        all_detailed_contributors.sort(key=lambda x: x.get('contributions', 0), reverse=True)
                        top_contributors = all_detailed_contributors[:5]
                        
                        # Display each contributor's details
                        f.write(f"## Top {len(top_contributors)} Contributors\n\n")
                        
                        # Create a markdown table for the contributors
                        f.write("| Contributor | GitHub | Contributions | Company | Location | Twitter |\n")
                        f.write("|-------------|--------|---------------|---------|----------|--------|\n")
                        
                        for contributor in top_contributors:
                            username = contributor.get('username', 'N/A')
                            name = contributor.get('name') or username
                            profile_url = contributor.get('profile_url', '#')
                            contributions = contributor.get('contributions', 0)
                            company = contributor.get('company', 'N/A')
                            location = contributor.get('location', 'N/A')
                            
                            twitter = contributor.get('twitter_username', '')
                            twitter_cell = f"[@{twitter}](https://twitter.com/{twitter})" if twitter else "N/A"
                            
                            f.write(f"| {name} | [{username}]({profile_url}) | {contributions} | {company} | {location} | {twitter_cell} |\n")
                        
                        f.write("\n")
                    
                    # Per-repository details
                    for i, repo in enumerate(repo_details):
                        repo_name = repo.get('name', 'N/A')
                        f.write(f"### Repository {i+1}: {repo_name}\n\n")
                        
                        # Basic repository info
                        f.write(f"- **Created:** {format_date(repo.get('created_at', 'N/A'))}\n")
                        f.write(f"- **Last Updated:** {format_date(repo.get('last_update', 'N/A'))}\n")
                        f.write(f"- **License:** {repo.get('license_type', 'None')}\n")
                        f.write(f"- **Size:** {format_size(repo.get('size_kb', 0))}\n")
                        f.write(f"- **Stars:** {repo.get('stars', 0)}\n")
                        f.write(f"- **Forks:** {repo.get('forks', 0)}\n")
                        f.write(f"- **Open Issues:** {repo.get('open_issues', 0)}\n\n")
                        
                        # PR Stats
                        pr_stats = repo.get('pull_requests', {})
                        if pr_stats and pr_stats.get('total', 0) > 0:
                            f.write("#### Pull Request Statistics\n\n")
                            f.write(f"- **Open PRs:** {pr_stats.get('open', 0)}\n")
                            f.write(f"- **Closed PRs:** {pr_stats.get('closed', 0)}\n")
                            f.write(f"- **Merged PRs:** {pr_stats.get('merged', 0)}\n")
                            f.write(f"- **Total PRs:** {pr_stats.get('total', 0)}\n\n")
                        
                        # Language distribution
                        languages = repo.get('main_languages', {})
                        if languages:
                            f.write("#### Language Distribution\n\n")
                            for lang, percentage in languages.items():
                                f.write(f"- **{lang}:** {percentage}%\n")
                            f.write("\n")
                        
                        # Commit info
                        commit_stats = repo.get('commit_stats', {})
                        if commit_stats:
                            f.write("#### Commit Statistics\n\n")
                            f.write(f"- **Total Commits:** {commit_stats.get('total_commits', 0)}\n")
                            f.write(f"- **First Commit:** {format_date(commit_stats.get('first_commit_date', ''))}\n")
                            f.write(f"- **Latest Commit:** {format_date(commit_stats.get('latest_commit_date', ''))}\n")
                            f.write(f"- **Avg. Commits/Week:** {commit_stats.get('commit_frequency', 0)}\n\n")
                        
                            # Commit history
                            commit_history = commit_stats.get('commit_history', {})
                            if commit_history:
                                f.write("#### Commit Activity\n\n")
                                f.write("```\n")
                                
                                # Create a basic ASCII chart of commit activity
                                max_commits = max(commit_history.values()) if commit_history else 0
                                if max_commits > 0:
                                    for month, count in commit_history.items():
                                        bar_length = int((count / max_commits) * 20)
                                        bar = '█' * bar_length
                                        f.write(f"{month}: {bar} {count}\n")
                                
                                f.write("```\n\n")
                        
                        # Contributors
                        contributors = repo.get('contributors', [])
                        total_contributors = repo.get('total_contributors', len(contributors))
                        
                        if contributors:
                            # Determine if we're showing all or just top contributors
                            if total_contributors > len(contributors):
                                f.write(f"#### Top {len(contributors)} Contributors (of {total_contributors} total)\n\n")
                            else:
                                f.write("#### Contributors\n\n")
                                
                            f.write("| Username | Profile | Contributions |\n")
                            f.write("|----------|---------|---------------|\n")
                            
                            for contributor in contributors:
                                username = contributor.get('login', 'N/A')
                                profile_url = contributor.get('profile_url', '#')
                                contributions = contributor.get('contributions', 0)
                                
                                f.write(f"| {username} | [{profile_url}]({profile_url}) | {contributions} |\n")
                            f.write("\n")
                        else:
                            f.write("#### Contributors\n\n")
                            f.write("No contributor information available.\n\n")
                    
                    f.write("\n")
            elif isinstance(repo_details, dict):
                # Single repository in old format
                f.write("### Repository Statistics\n\n")
                f.write(f"- **Repository:** {repo_details.get('name', 'N/A')}\n")
                f.write(f"- **Stars:** {repo_details.get('stars', 0)}\n")
                f.write(f"- **Forks:** {repo_details.get('forks', 0)}\n")
                f.write(f"- **Open Issues:** {repo_details.get('open_issues', 0)}\n")
                f.write(f"- **Primary Language:** {repo_details.get('language', 'N/A')}\n")
                f.write(f"- **Last Updated:** {format_date(repo_details.get('last_update', 'N/A'))}\n")
                
                # Add PR stats if available
                pr_stats = repo_details.get('pull_requests', {})
                if pr_stats:
                    f.write("\n### Pull Request Statistics\n\n")
                    f.write(f"- **Open PRs:** {pr_stats.get('open', 0)}\n")
                    f.write(f"- **Closed PRs:** {pr_stats.get('closed', 0)}\n")
                    f.write(f"- **Merged PRs:** {pr_stats.get('merged', 0)}\n")
                    f.write(f"- **Total PRs:** {pr_stats.get('total', 0)}\n\n")
                
                # Add contributor info if available
                if 'contributors' in repo_details:
                    total_contributors = repo_details.get('total_contributors', len(repo_details['contributors']))
                    f.write(f"- **Total Contributors:** {total_contributors}\n\n")
                    
                    # Check if we have detailed contributor information
                    detailed_contributors = repo_details.get('detailed_contributors', [])
                    if detailed_contributors:
                        num_contributors = min(5, len(detailed_contributors))
                        f.write(f"## Top {num_contributors} Contributors\n\n")
                        
                        for i, contributor in enumerate(detailed_contributors[:num_contributors]):
                            username = contributor.get('username', 'N/A')
                            name = contributor.get('name') or username
                            
                            f.write(f"### {i+1}. {name} (@{username})\n\n")
                            
                            # Basic info
                            profile_url = contributor.get('profile_url', '#')
                            contributions = contributor.get('contributions', 0)
                            f.write(f"- **GitHub:** [{username}]({profile_url})\n")
                            f.write(f"- **Contributions:** {contributions}\n")
                            
                            # Additional info if available
                            if contributor.get('company'):
                                f.write(f"- **Company:** {contributor.get('company')}\n")
                            if contributor.get('location'):
                                f.write(f"- **Location:** {contributor.get('location')}\n")
                            if contributor.get('twitter_username'):
                                twitter = contributor.get('twitter_username')
                                f.write(f"- **Twitter:** [@{twitter}](https://twitter.com/{twitter})\n")
                            if contributor.get('blog'):
                                blog = contributor.get('blog')
                                if not blog.startswith(('http://', 'https://')):
                                    blog = 'https://' + blog
                                f.write(f"- **Website:** [{blog}]({blog})\n")
                            if contributor.get('bio'):
                                f.write(f"- **Bio:** {contributor.get('bio')}\n")
                            
                            # Activity stats
                            f.write(f"- **Followers:** {contributor.get('followers', 0)}\n")
                            f.write(f"- **Following:** {contributor.get('following', 0)}\n")
                            f.write(f"- **Public Repositories:** {contributor.get('public_repos', 0)}\n")
                            f.write("\n")
                    elif repo_details['contributors']:
                        # Use old contributor format if no detailed info
                        if total_contributors > len(repo_details['contributors']):
                            f.write(f"### Top {len(repo_details['contributors'])} Contributors (of {total_contributors} total)\n\n")
                        else:
                            f.write("### Repository Contributors\n\n")
                            
                        f.write("| Username | Profile | Contributions |\n")
                        f.write("|----------|---------|---------------|\n")
                        
                        for contributor in repo_details['contributors']:
                            username = contributor.get('login', 'N/A')
                            profile_url = contributor.get('profile_url', '#')
                            contributions = contributor.get('contributions', 0)
                            
                            f.write(f"| {username} | [{profile_url}]({profile_url}) | {contributions} |\n")
                        f.write("\n")
                else:
                    f.write("\n")

        # Code Quality
        f.write("## Code Quality Assessment\n\n")

        if "analysis" in result and "code_quality" in result["analysis"]:
            quality = result["analysis"]["code_quality"]

            if isinstance(quality, (int, float)):
                # If code_quality is just a number
                f.write(f"**Overall Score:** {quality:.2f}/100\n\n")
            elif isinstance(quality, dict):
                if "error" in quality:
                    f.write(f"**Error:** {quality['error']}\n\n")
                else:
                    # Check if we have multiple repository info
                    repos_analyzed = quality.get("repositories_analyzed", 0)
                    
                    # Safely get values with proper type checking
                    overall_score = quality.get("overall_score", 0)
                    if isinstance(overall_score, (int, float)):
                        if repos_analyzed > 1:
                            f.write(f"**Overall Score:** {overall_score:.2f}/100 (average of {repos_analyzed} repositories)\n\n")
                        else:
                            f.write(f"**Overall Score:** {overall_score:.2f}/100\n\n")
                    else:
                        f.write(f"**Overall Score:** 0.00/100\n\n")
                    
                    # Add a detailed analysis section
                    f.write("### Detailed Analysis\n\n")
                    
                    # Readability score and analysis
                    readability = quality.get("readability", 0)
                    readability_reasoning = None
                    if "ai_analysis" in quality and "readability_reasoning" in quality.get("ai_analysis", {}):
                        readability_reasoning = quality["ai_analysis"]["readability_reasoning"]
                        
                    if isinstance(readability, (int, float)):
                        f.write(f"**Readability and Documentation:** {readability:.2f}/100\n\n")
                        if readability_reasoning:
                            f.write(f"{readability_reasoning}\n\n")
                    else:
                        f.write(f"**Readability and Documentation:** Not evaluated\n\n")
                    
                    # Standards score and analysis
                    standards = quality.get("standards", 0)
                    standards_reasoning = None
                    if "ai_analysis" in quality and "standards_reasoning" in quality.get("ai_analysis", {}):
                        standards_reasoning = quality["ai_analysis"]["standards_reasoning"]
                        
                    if isinstance(standards, (int, float)):
                        f.write(f"**Coding Standards and Best Practices:** {standards:.2f}/100\n\n")
                        if standards_reasoning:
                            f.write(f"{standards_reasoning}\n\n")
                    else:
                        f.write(f"**Coding Standards and Best Practices:** Not evaluated\n\n")
                    
                    # Complexity score and analysis
                    complexity = quality.get("complexity", 0)
                    complexity_reasoning = None
                    if "ai_analysis" in quality and "complexity_reasoning" in quality.get("ai_analysis", {}):
                        complexity_reasoning = quality["ai_analysis"]["complexity_reasoning"]
                        
                    if isinstance(complexity, (int, float)):
                        f.write(f"**Algorithm Complexity and Efficiency:** {complexity:.2f}/100\n\n")
                        if complexity_reasoning:
                            f.write(f"{complexity_reasoning}\n\n")
                    else:
                        f.write(f"**Algorithm Complexity and Efficiency:** Not evaluated\n\n")
                    
                    # Testing score and analysis
                    testing = quality.get("testing", 0)
                    testing_reasoning = None
                    if "ai_analysis" in quality and "testing_reasoning" in quality.get("ai_analysis", {}):
                        testing_reasoning = quality["ai_analysis"]["testing_reasoning"]
                        
                    if isinstance(testing, (int, float)):
                        f.write(f"**Testing and Coverage:** {testing:.2f}/100\n\n")
                        if testing_reasoning:
                            f.write(f"{testing_reasoning}\n\n")
                    else:
                        f.write(f"**Testing and Coverage:** Not evaluated\n\n")
                    
                    # Overall analysis and suggestions
                    overall_analysis = None
                    suggestions = []
                    if "ai_analysis" in quality:
                        if "overall_analysis" in quality["ai_analysis"]:
                            overall_analysis = quality["ai_analysis"]["overall_analysis"]
                        if "suggestions" in quality["ai_analysis"]:
                            suggestions = quality["ai_analysis"]["suggestions"]
                            
                    if overall_analysis:
                        f.write("### Overall Assessment\n\n")
                        f.write(f"{overall_analysis}\n\n")
                        
                    if suggestions and len(suggestions) > 0:
                        f.write("### Suggestions for Improvement\n\n")
                        for suggestion in suggestions:
                            f.write(f"- {suggestion}\n")
                        f.write("\n")
                    
                    # Metrics
                    if "metrics" in quality:
                        f.write("### Metrics\n\n")
                        metrics = quality["metrics"]
                        f.write(
                            f"- **Total Files:** {metrics.get('file_count', 'N/A')}\n"
                        )
                        f.write(
                            f"- **Test Files:** {metrics.get('test_file_count', 'N/A')}\n"
                        )
                        f.write(
                            f"- **Documentation Files:** {metrics.get('doc_file_count', 'N/A')}\n"
                        )
                        
                        if "code_lines" in metrics:
                            f.write(
                                f"- **Lines of Code:** {metrics.get('code_lines', 'N/A')}\n"
                            )
                        
                        if "comment_lines" in metrics:
                            f.write(
                                f"- **Comment Lines:** {metrics.get('comment_lines', 'N/A')}\n"
                            )
                            
                        if "code_files_analyzed" in metrics:
                            f.write(
                                f"- **Code Files Analyzed:** {metrics.get('code_files_analyzed', 'N/A')}\n"
                            )
                        
                        f.write("\n")
            else:
                f.write(
                    "Could not assess code quality due to an error or inaccessible repository.\n\n"
                )
        else:
            f.write(
                "Could not assess code quality due to an error or inaccessible repository.\n\n"
            )

        # Celo Integration
        f.write("## Celo Blockchain Integration\n\n")

        if "analysis" in result and "celo_integration" in result["analysis"]:
            celo = result["analysis"]["celo_integration"]

            if isinstance(celo, bool):
                # If celo_integration is just a boolean
                integration_status = "Yes" if celo else "No"
                f.write(f"**Integrated with Celo:** {integration_status}\n\n")
            elif isinstance(celo, dict):
                if "error" in celo:
                    f.write(f"**Error:** {celo['error']}\n\n")
                else:
                    # Get integration status safely
                    if "integrated" in celo:
                        integrated = celo["integrated"]
                        # Check if we have multiple repository data
                        repos_with_celo = celo.get("repositories_with_celo", 0)
                        repos_analyzed = 1  # Default for backward compatibility
                        
                        # Check if we can determine total repositories analyzed
                        if "github_urls" in result and result["github_urls"]:
                            repos_analyzed = len(result["github_urls"])
                    else:
                        integrated = False
                        repos_with_celo = 0
                        repos_analyzed = 1
                        
                    # Format integration status with repository counts if multiple repos
                    if repos_analyzed > 1:
                        integration_status = f"{'Yes' if integrated else 'No'} ({repos_with_celo}/{repos_analyzed} repositories)"
                    else:
                        integration_status = "Yes" if integrated else "No"

                    f.write(f"**Integrated with Celo:** {integration_status}\n\n")

                    if integrated and "evidence" in celo and isinstance(celo["evidence"], list):
                        f.write("### Evidence of Integration\n\n")
                        for evidence in celo["evidence"]:
                            if isinstance(evidence, dict) and "keyword" in evidence and "file" in evidence:
                                # Check if evidence includes repository information
                                if "repository" in evidence:
                                    f.write(
                                        f"- Found keyword '{evidence['keyword']}' in file: {evidence['file']} (Repository: {evidence['repository']})\n"
                                    )
                                else:
                                    f.write(
                                        f"- Found keyword '{evidence['keyword']}' in file: {evidence['file']}\n"
                                    )
                        f.write("\n")
                    
                    # Add AI analysis of Celo integration if available
                    if integrated and "analysis" in celo:
                        f.write("### Integration Analysis\n\n")
                        f.write(f"{celo['analysis']}\n\n")
            else:
                # Default case if celo_integration is something unexpected
                f.write(f"**Integrated with Celo:** No\n\n")
        else:
            f.write(
                "Could not assess Celo integration due to an error or inaccessible repository.\n\n"
            )

        # Expert Review Section
        f.write("## Expert Review\n\n")
        
        # Determine the project strengths and concerns
        strengths = []
        concerns = []
        
        # Add repository-related strengths/concerns
        if "analysis" in result and "repo_details" in result["analysis"]:
            repo_details = result["analysis"]["repo_details"]
            
            # Process all repos or single repo
            repos_to_process = []
            if isinstance(repo_details, list):
                repos_to_process = repo_details
            elif isinstance(repo_details, dict):
                repos_to_process = [repo_details]
            
            # Evaluate metrics
            for repo in repos_to_process:
                # Check for active development
                commit_stats = repo.get('commit_stats', {})
                latest_commit = commit_stats.get('latest_commit_date', '')
                
                if latest_commit:
                    from datetime import datetime, timezone
                    try:
                        commit_date = datetime.fromisoformat(latest_commit.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        days_since_commit = (now - commit_date).days
                        
                        if days_since_commit < 30:
                            strengths.append("Active development with recent commits")
                        elif days_since_commit > 180:
                            concerns.append(f"Limited recent activity (last commit was {days_since_commit} days ago)")
                    except:
                        pass
                
                # Check for test files
                if "metrics" in result.get("analysis", {}).get("code_quality", {}):
                    metrics = result["analysis"]["code_quality"]["metrics"]
                    test_files = metrics.get("test_file_count", 0)
                    total_files = metrics.get("file_count", 0)
                    
                    if test_files > 0 and total_files > 0:
                        test_ratio = test_files / total_files
                        if test_ratio > 0.1:
                            strengths.append("Good test coverage")
                        elif test_ratio < 0.05 and total_files > 10:
                            concerns.append("Limited test coverage")
                
                # Check for documentation
                doc_files = repo.get("metrics", {}).get("doc_file_count", 0)
                if doc_files > 3:
                    strengths.append("Well-documented codebase")
                
                # Check contributor metrics
                contributors = repo.get("total_contributors", 0)
                if contributors > 5:
                    strengths.append("Strong contributor community")
                elif contributors == 1 and repo.get("stars", 0) > 0:
                    concerns.append("Single-contributor project")
        
        # Add code quality related strengths/concerns
        if "analysis" in result and "code_quality" in result["analysis"]:
            quality = result["analysis"]["code_quality"]
            
            if isinstance(quality, dict):
                score = quality.get("overall_score", 0)
                
                if isinstance(score, (int, float)):
                    if score > 80:
                        strengths.append("High code quality score")
                    elif score < 50:
                        concerns.append("Code quality issues identified")
                
                # Check specific areas
                readability = quality.get("readability", 0)
                standards = quality.get("standards", 0)
                complexity = quality.get("complexity", 0)
                testing = quality.get("testing", 0)
                
                if isinstance(readability, (int, float)) and readability > 80:
                    strengths.append("Excellent code readability and documentation")
                
                if isinstance(standards, (int, float)) and standards > 80:
                    strengths.append("Strong adherence to coding standards")
                
                if isinstance(complexity, (int, float)) and complexity < 50:
                    concerns.append("Complex code structure that may be difficult to maintain")
                
                if isinstance(testing, (int, float)) and testing < 40:
                    concerns.append("Insufficient testing infrastructure")
        
        # Add Celo integration related strengths/concerns
        if "analysis" in result and "celo_integration" in result["analysis"]:
            celo = result["analysis"]["celo_integration"]
            
            if isinstance(celo, dict) and celo.get("integrated", False):
                strengths.append("Confirmed Celo blockchain integration")
                
                # Check evidence count
                evidence = celo.get("evidence", [])
                if len(evidence) > 5:
                    strengths.append("Comprehensive Celo integration across multiple files")
        
        # Extract technology highlights
        tech_highlights = extract_technology_highlights(result)
        if tech_highlights:
            # Add technology related strengths
            if any("Frontend:" in tech for tech in tech_highlights):
                strengths.append("Complete frontend implementation")
            
            if any("Database:" in tech for tech in tech_highlights):
                strengths.append("Database integration for data persistence")
            
            if any("Wallet Integration:" in tech for tech in tech_highlights):
                strengths.append("Wallet connectivity for blockchain interaction")
        
        # Write strengths
        if strengths:
            f.write("### Positive Factors\n\n")
            for strength in strengths:
                f.write(f"- {strength}\n")
            f.write("\n")
        
        # Write concerns
        if concerns:
            f.write("### Areas for Improvement\n\n")
            for concern in concerns:
                f.write(f"- {concern}\n")
            f.write("\n")
        
        # If no strengths or concerns were identified
        if not strengths and not concerns:
            f.write("Insufficient data for a detailed expert review. More repository activity and code samples would help provide a more comprehensive analysis.\n\n")

        # Deep Code Analysis Section
        if "analysis" in result and "deep_code_analysis" in result["analysis"]:
            deep_analysis = result["analysis"]["deep_code_analysis"]
            
            # Debug output to see what's in the analysis
            print(f"Deep code analysis in report: {deep_analysis.keys() if isinstance(deep_analysis, dict) else 'not a dict'}")
            
            # If there's an error, show it
            if isinstance(deep_analysis, dict) and deep_analysis.get("error"):
                print(f"Deep code analysis error: {deep_analysis.get('error')}")
            
            if isinstance(deep_analysis, dict):
                f.write("## Deep Code Analysis\n\n")
                
                # Make sure to dump the raw analysis details for debugging
                if "raw_analysis" in deep_analysis and isinstance(deep_analysis["raw_analysis"], dict):
                    print("Deep code analysis successful, raw data available")
                
                # Implemented Features
                implemented_features = deep_analysis.get("implemented_features", [])
                if implemented_features:
                    f.write("### Implemented Features\n\n")
                    for feature in implemented_features:
                        f.write(f"- {feature}\n")
                    f.write("\n")
                
                # Missing Features
                missing_features = deep_analysis.get("missing_features", [])
                if missing_features:
                    f.write("### Missing or Incomplete Features\n\n")
                    for feature in missing_features:
                        f.write(f"- {feature}\n")
                    f.write("\n")
                
                # Technologies and Frameworks
                frameworks = deep_analysis.get("frameworks", [])
                technologies = deep_analysis.get("technologies", [])
                
                if frameworks:
                    f.write("### Frameworks\n\n")
                    for framework in frameworks:
                        f.write(f"- {framework}\n")
                    f.write("\n")
                
                if technologies:
                    f.write("### Technologies\n\n")
                    for tech in technologies:
                        f.write(f"- {tech}\n")
                    f.write("\n")
                
                # Architecture Patterns
                architecture_patterns = deep_analysis.get("architecture_patterns", [])
                if architecture_patterns:
                    f.write("### Architecture Patterns\n\n")
                    for pattern in architecture_patterns:
                        f.write(f"- {pattern}\n")
                    f.write("\n")
                
                # Codebase Breakdown
                codebase_breakdown = deep_analysis.get("codebase_breakdown", {})
                if codebase_breakdown:
                    f.write("### Codebase Structure\n\n")
                    
                    if "structure" in codebase_breakdown:
                        f.write(f"**Structure:** {codebase_breakdown['structure']}\n\n")
                    
                    if "components" in codebase_breakdown and codebase_breakdown["components"]:
                        f.write("**Components:**\n\n")
                        for component in codebase_breakdown["components"]:
                            f.write(f"- {component}\n")
                        f.write("\n")
                    
                    if "interactions" in codebase_breakdown:
                        f.write(f"**Component Interactions:** {codebase_breakdown['interactions']}\n\n")
                    
                    if "code_organization" in codebase_breakdown:
                        f.write(f"**Code Organization:** {codebase_breakdown['code_organization']}\n\n")
        
        # Additional Notes
        f.write("## Additional Notes\n\n")

        if "analysis" in result and "error" in result["analysis"]:
            f.write(f"- {result['analysis']['error']}\n")
        else:
            f.write("No additional notes.\n")


def generate_report(results: List[Dict[str, Any]], output_dir: str = "reports") -> None:
    """
    Generate Markdown reports from analysis results.

    Args:
        results: List of dictionaries containing analysis results
        output_dir: Directory to save reports
    """
    # Create a spinner for report generation
    spinner = Spinner(f"Generating reports in {output_dir} directory")
    spinner.start()
    
    logger.info(f"Starting report generation for {len(results)} projects")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate summary report
        spinner.update(f"Creating summary report")
        logger.info(f"Generating summary report in {output_dir}")
        
        summary_path = os.path.join(output_dir, "summary.md")
        generate_summary_report(results, summary_path)
        
        # Initialize progress bar for individual reports with custom colors and format
        progress_bar = tqdm(
            total=len(results),
            desc="Generating Reports",
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            ncols=80,
            colour="blue"
        )

        # Generate individual reports
        for idx, result in enumerate(results):
            project_name = result["project_name"]
            file_name = project_name.replace(" ", "_").lower()
            report_path = os.path.join(output_dir, f"{file_name}.md")
            
            # Keep the progress description simple
            progress_bar.set_description(f"Generating Reports")
            
            # Log progress
            logger.info(f"Creating report for {project_name} ({idx+1}/{len(results)})")

            # Generate the project report
            generate_project_report(result, report_path)
            
            # Update progress bar
            progress_bar.update(1)
        
        # Close progress bar
        progress_bar.close()
        # Add space after progress bar
        print("")
        
        # Save raw results to JSON
        spinner.update(f"Saving raw results to JSON")
        logger.info(f"Saving raw results to {output_dir}/results.json")
        with open(os.path.join(output_dir, "results.json"), "w") as f:
            json.dump(results, f, indent=2)
        
        # Final spinner update
        spinner.stop(f"Successfully generated all reports in {output_dir}")
        logger.info(f"Report generation completed successfully")
        
    except Exception as e:
        error_msg = f"Error generating reports: {str(e)}"
        spinner.stop(f"Error generating reports: {str(e)}")
        logger.error(error_msg)
        raise Exception(error_msg)