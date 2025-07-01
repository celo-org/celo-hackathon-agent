"""
Repository analysis module for the AI Project Analyzer.

This module handles analyzing repository code digests and GitHub metrics using LangChain and Gemini.
"""

import logging
import time
from typing import Any, Dict, Optional, Union

from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import get_gemini_api_key

logger = logging.getLogger(__name__)

# Available models
AVAILABLE_MODELS = {
    "gemini-2.5-pro-preview-03-25": {
        "description": "Balanced model for most use cases",
        "max_tokens": 1000000,
    },
    "gemini-2.5-flash-preview-04-17": {
        "description": "Balanced model for most use cases",
        "max_tokens": 1000000,
    },
}

# Default model to use
DEFAULT_MODEL = "gemini-2.5-flash-preview-04-17"
# Default temperature for generation
DEFAULT_TEMPERATURE = 0.2
# Maximum token limit (can be overridden by model-specific limits)
MAX_TOKENS = 900000
# Maximum retry attempts for API calls
MAX_RETRIES = 3
# Delay between retries (in seconds)
RETRY_DELAY = 5


def load_prompt(prompt_path: str) -> str:
    """
    Load a prompt from a file.

    Args:
        prompt_path: Path to the prompt file

    Returns:
        str: The prompt text

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")


def create_llm_chain(
    prompt_template: str,
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    output_json: bool = False,
    include_metrics: bool = False,
) -> object:
    """
    Create a LangChain chain for analysis.

    Args:
        prompt_template: The prompt template to use
        model_name: Name of the model to use (defaults to DEFAULT_MODEL)
        temperature: Temperature setting for generation (defaults to DEFAULT_TEMPERATURE)
        output_json: Whether to format output as JSON
        include_metrics: Whether to include metrics in the prompt template

    Returns:
        object: The LangChain chain
    """
    # Get API key
    api_key = get_gemini_api_key()

    # Validate model name
    if model_name not in AVAILABLE_MODELS:
        logger.warning(f"Model {model_name} not recognized, using {DEFAULT_MODEL} instead")
        model_name = DEFAULT_MODEL

    # Get model-specific token limit or use default
    max_tokens = AVAILABLE_MODELS[model_name].get("max_tokens", MAX_TOKENS)

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
        max_output_tokens=max_tokens,
    )

    # Create the base prompt template string
    prompt_str = prompt_template

    # Add metrics instruction if metrics will be included
    if include_metrics:
        metrics_instruction = """
## GitHub Metrics
I've included GitHub metrics for this repository that you should incorporate into your analysis:
{metrics_data}

When analyzing the repository, please consider these metrics and include them in your report under appropriate sections. 
Include a 'Repository Metrics' section with all the stats, a 'Top Contributor Profile' section, and a 'Language Distribution' section in your report.
Also add a 'Codebase Breakdown' section based on the strengths, weaknesses, and missing features from the codebase analysis.
"""
        prompt_str += metrics_instruction

    # Add code digest at the end
    base_prompt = prompt_str + "\n\n{code_digest}"

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(base_prompt)

    # Create output parser
    string_parser = StrOutputParser()

    # We're phasing out JSON output, so we'll always use the string parser
    chain = prompt | llm | string_parser

    return chain


def truncate_if_needed(text: str, max_tokens: int = MAX_TOKENS) -> str:
    """
    Truncate text if it might exceed the token limit.

    This is a very rough estimate. Proper tokenization would require a tokenizer.

    Args:
        text: The text to truncate
        max_tokens: Maximum number of tokens allowed

    Returns:
        str: Truncated text
    """
    # Very rough estimate: 4 characters per token
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token

    if len(text) > max_chars:
        logger.warning("Code digest exceeds estimated token limit, truncating...")
        truncated = text[:max_chars]
        return truncated + "\n\n[Content truncated due to length]"

    return text


def analyze_single_repository(
    repo_name: str,
    code_digest: str,
    prompt_path: str,
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    output_json: bool = False,
    metrics_data: Optional[Dict[str, Any]] = None,
) -> Union[str, Dict[str, Any]]:
    """
    Analyze a single repository using the LLM.

    Args:
        repo_name: Name of the repository
        code_digest: Repository code digest
        prompt_path: Path to the prompt file
        model_name: Name of the Gemini model to use
        temperature: Temperature setting for generation
        output_json: Whether to format output as JSON
        metrics_data: Optional dictionary containing GitHub metrics for this repository

    Returns:
        Union[str, Dict[str, Any]]: Analysis result (string or JSON object)
    """
    start_time = time.time()

    # Load the prompt template
    prompt_template = load_prompt(prompt_path)

    # Check if we have metrics for this repository
    has_metrics = metrics_data is not None and len(metrics_data) > 0

    # Create the LangChain chain for this repository
    chain = create_llm_chain(
        prompt_template,
        model_name=model_name,
        temperature=temperature,
        output_json=output_json,
        include_metrics=has_metrics,
    )

    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            # Prepare the code digest (truncate if needed)
            processed_digest = truncate_if_needed(code_digest)

            # Prepare input for the chain
            invoke_params = {"code_digest": processed_digest}

            # Add metrics data if available
            if has_metrics:
                # Convert metrics to a formatted string
                metrics_formatted = format_metrics_for_prompt(metrics_data)
                invoke_params["metrics_data"] = metrics_formatted

            # Run the analysis
            analysis = chain.invoke(invoke_params)

            return analysis

        except KeyboardInterrupt:
            logger.warning("Analysis interrupted by user")
            raise

        except Exception as e:
            retry_count += 1
            logger.error(
                f"Error analyzing repository {repo_name} (attempt {retry_count}/{MAX_RETRIES}): {str(e)}"
            )

            if retry_count < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"All retry attempts failed for {repo_name}")
                # Return error message
                return f"Error: {str(e)}"

    # Should never reach here, but just in case
    return f"Error: Unknown error analyzing {repo_name}"


def analyze_repositories(
    repo_digests: Dict[str, str],
    prompt_path: str,
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    output_json: bool = False,
    metrics_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Analyze multiple repositories using the LLM.

    Args:
        repo_digests: Dictionary mapping repository names to their code digests
        prompt_path: Path to the prompt file
        model_name: Name of the Gemini model to use
        temperature: Temperature setting for generation
        output_json: Whether to format output as JSON
        metrics_data: Optional dictionary mapping repository names to their GitHub metrics

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: Dictionary mapping repository names to their analysis results
    """
    results = {}
    total_repos = len(repo_digests)
    start_time = time.time()

    # Process each repository
    for index, (repo_name, code_digest) in enumerate(repo_digests.items(), 1):
        # Calculate progress
        if index > 1:
            elapsed_time = time.time() - start_time
            avg_time_per_repo = elapsed_time / (index - 1)
            estimated_remaining = avg_time_per_repo * (total_repos - index + 1)

        # Extract metrics for this repository if available
        repo_metrics = metrics_data.get(repo_name, {}) if metrics_data else {}

        # Analyze this repository
        analysis = analyze_single_repository(
            repo_name,
            code_digest,
            prompt_path,
            model_name,
            temperature,
            output_json,
            repo_metrics,
        )

        # Store the result
        results[repo_name] = analysis

    # Calculate and log statistics
    total_time = time.time() - start_time
    successful_analyses = sum(
        1 for v in results.values() if not isinstance(v, str) or not v.startswith("Error:")
    )

    if successful_analyses < total_repos:
        logger.warning(f"Failed to analyze {total_repos - successful_analyses} repositories")

    return results


def format_metrics_for_prompt(metrics: Dict[str, Any]) -> str:
    """
    Format metrics data for inclusion in the prompt.

    Args:
        metrics: Repository metrics data

    Returns:
        str: Formatted metrics string
    """
    formatted = []

    # Repository metrics
    if "repository_metrics" in metrics:
        formatted.append("### Repository Metrics")
        for key, value in metrics["repository_metrics"].items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")

    # Repository links
    if "repository_links" in metrics:
        formatted.append("\n### Repository Links")
        for key, value in metrics["repository_links"].items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")

    # Top contributor
    if "top_contributor" in metrics and metrics["top_contributor"]:
        formatted.append("\n### Top Contributor")
        for key, value in metrics["top_contributor"].items():
            formatted.append(f"- {key.title()}: {value}")

    # PR status
    if "pr_status" in metrics:
        formatted.append("\n### Pull Request Status")
        for key, value in metrics["pr_status"].items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")

    # Language distribution
    if "language_distribution" in metrics and metrics["language_distribution"]:
        formatted.append("\n### Language Distribution")
        for lang, percentage in metrics["language_distribution"].items():
            formatted.append(f"- {lang}: {percentage}%")

    # Celo evidence
    if "celo_evidence" in metrics and metrics["celo_evidence"]:
        evidence = metrics["celo_evidence"]

        if evidence.get("summary"):
            formatted.append("\n### Celo Integration Evidence")
            formatted.append(evidence["summary"])

            # Celo references
            if evidence.get("celo_references"):
                formatted.append("\n#### Files with Celo References:")
                for file_path in evidence["celo_references"][:10]:  # Limit to 10 files
                    formatted.append(f"- `{file_path}`")

            # Alfajores references
            if evidence.get("alfajores_references"):
                formatted.append("\n#### Files with Alfajores References:")
                for file_path in evidence["alfajores_references"][:10]:  # Limit to 10 files
                    formatted.append(f"- `{file_path}`")

            # Contract addresses
            if evidence.get("contract_addresses"):
                formatted.append("\n#### Contract Addresses Found:")

                # Prioritize README addresses by showing them first
                readme_addresses = None
                other_addresses = []

                for item in evidence["contract_addresses"][:5]:  # Limit to 5 files
                    if item["file"].lower() == "readme.md":
                        readme_addresses = item
                    else:
                        other_addresses.append(item)

                # Show README addresses first with prominence
                if readme_addresses:
                    # Check if addresses were found in a Celo context
                    has_celo_context = readme_addresses.get("celo_context", False)

                    if has_celo_context:
                        formatted.append("- **README.md Contains Celo Contract Addresses:**")
                    else:
                        formatted.append("- **README.md Contains Contract Addresses:**")

                    addresses = readme_addresses.get("addresses", [])
                    for addr in addresses[:5]:  # Show more addresses from README
                        formatted.append(f"  - `{addr}`")

                # Then show other addresses
                for item in other_addresses[:4]:  # Limit to 4 other files
                    has_celo_context = item.get("celo_context", False)

                    if has_celo_context:
                        formatted.append(f"- File: `{item['file']}` (Celo context detected)")
                    else:
                        formatted.append(f"- File: `{item['file']}`")

                    addresses = item.get("addresses", [])
                    for addr in addresses[:3]:  # Limit to 3 addresses per file
                        formatted.append(f"  - `{addr}`")

            # Celo packages
            if evidence.get("celo_packages"):
                formatted.append("\n#### Celo Packages:")
                for package in evidence["celo_packages"]:
                    formatted.append(f"- `{package}`")

    # Codebase analysis
    if "codebase_analysis" in metrics:
        analysis = metrics["codebase_analysis"]

        if "strengths" in analysis and analysis["strengths"]:
            formatted.append("\n### Codebase Strengths")
            for item in analysis["strengths"]:
                formatted.append(f"- {item}")

        if "weaknesses" in analysis and analysis["weaknesses"]:
            formatted.append("\n### Codebase Weaknesses")
            for item in analysis["weaknesses"]:
                formatted.append(f"- {item}")

        if "missing_features" in analysis and analysis["missing_features"]:
            formatted.append("\n### Missing or Buggy Features")
            for item in analysis["missing_features"]:
                formatted.append(f"- {item}")

        if "summary" in analysis and analysis["summary"]:
            formatted.append("\n### Codebase Summary")
            formatted.append(analysis["summary"])

    return "\n".join(formatted)
    return "\n".join(formatted)
