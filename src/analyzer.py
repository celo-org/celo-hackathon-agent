"""
Repository analysis module for the AI Project Analyzer.

This module handles analyzing repository code digests using LangChain and Gemini.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough

from src.config import get_gemini_api_key

logger = logging.getLogger(__name__)

# Available models
AVAILABLE_MODELS = {
    "gemini-2.0-flash-lite": {
        "description": "Balanced model for most use cases",
        "max_tokens": 30000,
    },
    "gemini-2.0-flash": {
        "description": "Advanced model with better capabilities",
        "max_tokens": 30000,
    },
}

# Default model to use
DEFAULT_MODEL = "gemini-2.0-flash"
# Default temperature for generation
DEFAULT_TEMPERATURE = 0.2
# Maximum token limit (can be overridden by model-specific limits)
MAX_TOKENS = 30000
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
) -> object:
    """
    Create a LangChain chain for analysis.

    Args:
        prompt_template: The prompt template to use
        model_name: Name of the model to use (defaults to DEFAULT_MODEL)
        temperature: Temperature setting for generation (defaults to DEFAULT_TEMPERATURE)
        output_json: Whether to format output as JSON

    Returns:
        object: The LangChain chain
    """
    # Get API key
    api_key = get_gemini_api_key()

    # Validate model name
    if model_name not in AVAILABLE_MODELS:
        logger.warning(
            f"Model {model_name} not recognized, using {DEFAULT_MODEL} instead"
        )
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

    # Create prompt template
    prompt = ChatPromptTemplate.from_template(prompt_template + "\n\n{code_digest}")

    # Create output parser
    string_parser = StrOutputParser()

    if output_json:
        # Add specific instructions for JSON output to help the model
        json_instruction = "\n\nPlease format your response as a valid JSON object containing the analysis results. Include scores for each category (readability, standards, complexity, testing) and provide an overall analysis."
        json_prompt = ChatPromptTemplate.from_template(
            prompt_template + json_instruction + "\n\n{code_digest}"
        )

        # Custom JSON parsing function
        def parse_json_string(text: str) -> dict:
            """Parse JSON string, handling common formatting issues."""
            try:
                # First, try to find JSON content between triple backticks
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
                if json_match:
                    json_str = json_match.group(1).strip()
                else:
                    # If no code blocks, use the entire text
                    json_str = text.strip()

                # Try to parse JSON directly
                try:
                    return json.loads(json_str)
                except:
                    # If that fails, try to find a JSON object in the text
                    # This handles cases where the model adds extra text before/after JSON
                    object_match = re.search(r"(\{[\s\S]*\})", json_str)
                    if object_match:
                        return json.loads(object_match.group(1))
                    raise  # Re-raise the exception if we couldn't find a JSON object

            except Exception as e:
                logger.error(f"Failed to parse JSON: {e}")
                # Return a basic error object with the raw text for debugging
                return {
                    "error": f"Failed to parse JSON: {str(e)}",
                    "raw_text": text[:500] + "..." if len(text) > 500 else text,
                }

        # Create chain with custom JSON parser
        chain = json_prompt | llm | string_parser | parse_json_string
    else:
        # Use string output parser for regular text output
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
        logger.warning(f"Code digest exceeds estimated token limit, truncating...")
        truncated = text[:max_chars]
        return truncated + "\n\n[Content truncated due to length]"

    return text


def analyze_repositories(
    repo_digests: Dict[str, str],
    prompt_path: str,
    model_name: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    output_json: bool = False,
) -> Dict[str, Union[str, Dict[str, Any]]]:
    """
    Analyze multiple repositories using the LLM.

    Args:
        repo_digests: Dictionary mapping repository names to their code digests
        prompt_path: Path to the prompt file
        model_name: Name of the Gemini model to use
        temperature: Temperature setting for generation
        output_json: Whether to format output as JSON

    Returns:
        Dict[str, Union[str, Dict[str, Any]]]: Dictionary mapping repository names to their analysis results
    """
    results = {}
    total_repos = len(repo_digests)
    start_time = time.time()

    # Load the prompt template
    logger.info(f"Loading prompt from {prompt_path}")
    prompt_template = load_prompt(prompt_path)

    # Create the LangChain chain
    logger.info(f"Creating LLM chain with model {model_name}")
    chain = create_llm_chain(
        prompt_template,
        model_name=model_name,
        temperature=temperature,
        output_json=output_json,
    )

    # Process each repository
    for index, (repo_name, code_digest) in enumerate(repo_digests.items(), 1):
        logger.info(f"Analyzing repository {index}/{total_repos}: {repo_name}")

        # Calculate progress
        if index > 1:
            elapsed_time = time.time() - start_time
            avg_time_per_repo = elapsed_time / (index - 1)
            estimated_remaining = avg_time_per_repo * (total_repos - index + 1)
            logger.info(f"Estimated time remaining: {estimated_remaining:.1f} seconds")

        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # Prepare the code digest (truncate if needed)
                processed_digest = truncate_if_needed(code_digest)

                # Run the analysis
                logger.info(
                    f"Running LLM analysis for {repo_name} (attempt {retry_count + 1}/{MAX_RETRIES})"
                )
                analysis = chain.invoke({"code_digest": processed_digest})

                # Store the result
                results[repo_name] = analysis

                logger.info(f"Analysis complete for {repo_name}")
                break  # Success, exit retry loop

            except KeyboardInterrupt:
                logger.warning("Analysis interrupted by user")
                raise

            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error analyzing repository {repo_name} (attempt {retry_count}/{MAX_RETRIES}): {str(e)}"
                )

                if retry_count < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {repo_name}")
                    # Store error message in results
                    results[repo_name] = f"Error: {str(e)}"

    # Calculate and log statistics
    total_time = time.time() - start_time
    successful_analyses = sum(
        1
        for v in results.values()
        if not isinstance(v, str) or not v.startswith("Error:")
    )

    logger.info(
        f"Analyzed {successful_analyses}/{total_repos} repositories successfully"
    )
    logger.info(f"Total analysis time: {total_time:.2f} seconds")

    if successful_analyses < total_repos:
        logger.warning(
            f"Failed to analyze {total_repos - successful_analyses} repositories"
        )

    return results
