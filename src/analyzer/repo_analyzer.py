"""
Repository analyzer that combines all analysis components.
"""

import os
import time
import json
import re
from typing import Dict, Any, Optional, Callable

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.callbacks.manager import get_openai_callback
import anthropic

from src.models.config import Config
from src.models.types import RepositoryAnalysisResult
from src.analyzer.github_repo import GitHubRepository
from src.utils.logger import logger

# System prompt template for repository analysis
SYSTEM_PROMPT = """
You are an expert code reviewer, software architect, and blockchain specialist with deep knowledge of the Celo ecosystem. Your task is to thoroughly analyze the provided GitHub repository and generate a comprehensive technical assessment.

ABOUT CELO:
Celo is a mobile-first blockchain platform focused on financial inclusion through:
- Mobile-first design with phone number-based addressing
- Stable value currencies (cUSD, cEUR, cREAL, etc.)
- ContractKit: JavaScript SDK for Celo integration
- Lightweight identity protocol and Valora wallet
- Fast, low-cost transactions with proof-of-stake consensus
- DeFi capabilities including staking, lending, and swapping
- On/off ramps for fiat currencies
- Developer tools for building decentralized applications

ANALYSIS INSTRUCTIONS:

1. Repository Classification (10%):
   - Determine repository type (dApp, smart contracts, library, tool, etc.)
   - Identify primary languages, frameworks, and technologies
   - Assess repository completeness and production-readiness

2. Architecture Analysis (20%):
   - Evaluate overall architectural approach
   - Assess component organization and interaction patterns
   - Identify design patterns and architectural principles in use
   - Analyze data flow and state management

3. Code Quality Assessment (25%):
   - Evaluate code readability, formatting, and documentation
   - Assess adherence to language-specific best practices
   - Analyze code complexity, modularity, and reusability
   - Evaluate error handling, input validation, and edge cases
   - Examine testing approach, coverage, and quality

4. Celo Integration Analysis (30%):
   - Determine presence and depth of Celo blockchain integration
   - Identify specific Celo features being leveraged
   - Assess correctness of Celo-specific implementation
   - Evaluate security practices in blockchain interactions
   - Analyze gas optimization in smart contracts (if applicable)
   - IMPORTANT: Look for and extract any deployed smart contract addresses from code or README
   - IMPORTANT: Note which blockchain network deployments exist on (mainnet, testnet, alfajores, etc.)

5. Key Findings & Recommendations (15%):
   - Highlight 3-5 significant strengths of the implementation
   - Identify 3-5 critical areas for improvement
   - Provide specific, actionable recommendations
   - Assess project potential and technical viability

OUTPUT FORMAT:
Return your analysis as a structured JSON object with this exact format:

{
  "repo_type": {
    "type": "Repository type (dApp, smart contract, library, etc.)",
    "languages": ["Primary language", "Secondary language"],
    "frameworks": ["Framework1", "Framework2"],
    "completeness": "Assessment of project completeness (0-100%)",
    "production_readiness": "Assessment of production readiness (0-100%)"
  },
  "deployment": {
    "site_url": "Live deployed site URL (if found in README or code)",
    "contract_addresses": [
      {"network": "Network name (e.g., Celo Mainnet, Alfajores)", "address": "Contract address", "contract_name": "Name of contract"}
    ]
  },
  "code_quality": {
    "overall_score": number,
    "readability": {"score": number, "analysis": "Detailed analysis with examples"},
    "standards": {"score": number, "analysis": "Detailed analysis with examples"},
    "complexity": {"score": number, "analysis": "Detailed analysis with examples"},
    "testing": {"score": number, "analysis": "Detailed analysis with examples"}
  },
  "celo_integration": {
    "integrated": boolean,
    "integration_depth": "none|minimal|moderate|deep",
    "features_used": [
      {"feature": "Celo feature name", "implementation_quality": number, "notes": "Implementation details"}
    ],
    "security_assessment": {"score": number, "findings": ["Security finding 1", "Security finding 2"]},
    "gas_optimization": {"score": number, "findings": ["Optimization note 1", "Optimization note 2"]},
    "evidence": ["File path or code snippet showing Celo integration"],
    "contract_addresses": ["Deployed contract addresses found in code or README"],
    "overall_score": number
  },
  "architecture": {
    "pattern": "Primary architectural pattern",
    "components": [
      {"name": "Component name", "purpose": "Component purpose", "quality": number}
    ],
    "data_flow": "Description of data flow through the system",
    "strengths": ["Architectural strength 1", "Architectural strength 2"],
    "weaknesses": ["Architectural weakness 1", "Architectural weakness 2"],
    "overall_score": number
  },
  "findings": {
    "strengths": [
      {"description": "Strength description", "impact": "High/Medium/Low", "details": "Detailed explanation"}
    ],
    "concerns": [
      {"description": "Weakness description", "impact": "High/Medium/Low", "details": "Detailed explanation"}
    ],
    "overall_assessment": "Overall assessment of the project"
  },
  "recommendations": [
    {"priority": "High/Medium/Low", "description": "Recommendation", "justification": "Why this matters"}
  ],
  "confidence_levels": {
    "code_quality": {"level": "High/Medium/Low", "reasoning": "Reasoning for confidence level"},
    "celo_integration": {"level": "High/Medium/Low", "reasoning": "Reasoning for confidence level"},
    "architecture": {"level": "High/Medium/Low", "reasoning": "Reasoning for confidence level"}
  }
}

IMPORTANT GUIDELINES:
- Base your analysis solely on the provided code and repository information
- Provide specific code examples and file paths to support your findings
- Balance technical detail with clear explanations
- Be honest but constructive in your assessment
- Consider the apparent purpose and audience of the project
- If Celo integration is minimal or absent, provide suggestions for integration
- Focus on substantive technical issues rather than stylistic preferences
- Clearly indicate your confidence level in each area of analysis
- IMPORTANT: Only include deployed contract addresses that are clearly identified as such
- When reporting contract addresses:
  - ONLY include addresses with clear deployment context (e.g., "deployed at", "contract address:", etc.)
  - Do NOT include addresses that appear to be example addresses, test addresses, or wallet addresses
  - If no deployed contract addresses are found, use "N/A" or empty array, DO NOT make up addresses
  - Each address should have a confidence rating (high/medium/low) about whether it's a deployed contract
  - Include the network (mainnet/testnet/alfajores) if this information is available
- For deployed site URLs:
  - Only include URLs that are clearly identified as deployed applications
  - If no deployed site is found, use "N/A" or empty string, DO NOT make up URLs
- Review the "Deployment Information" section of the digest carefully for validated contract addresses
- Pay special attention to the "Confidence" indicator for contract addresses
"""


class RepositoryAnalyzer:
    """
    Analyzes GitHub repositories for code quality and Celo blockchain integration.

    This class combines GitHub API access, code analysis, and AI-powered evaluation
    to provide insights into repository quality and Celo integration.
    """

    def __init__(
        self,
        config_path: str = "config.json",
        model_provider: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the repository analyzer with configuration.

        Args:
            config_path: Path to the configuration file
            model_provider: Optional model provider override (anthropic, openai, google)
            verbose: Whether to enable verbose output
        """
        # Load configuration
        self.config = Config.from_file(config_path)
        self.verbose = verbose

        # Set up LLM based on provider
        self.llm = None
        self.model_provider = model_provider or self.config.default_model

        logger.debug(
            f"Initializing repository analyzer with model provider: {self.model_provider}"
        )

        # Initialize LLM based on provider
        if self.model_provider == "anthropic":
            self._init_anthropic_model()
        elif self.model_provider == "openai":
            self._init_openai_model()
        elif self.model_provider == "google":
            self._init_google_model()
        else:
            logger.warn(
                f"Unknown model provider '{self.model_provider}'. Falling back to default."
            )
            self._init_anthropic_model()

        # Initialize GitHub repository handler
        self.github_repo = GitHubRepository(self.config)

    def _init_anthropic_model(self):
        """Initialize Anthropic Claude model."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

        logger.info(f"Using Anthropic model: {self.config.model_name}")
        self.llm = ChatAnthropic(
            model=self.config.model_name,
            temperature=self.config.temperature,
            anthropic_api_key=api_key,
        )

    def _init_openai_model(self):
        """Initialize OpenAI model."""
        logger.info("Using OpenAI model: gpt-4")
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=self.config.temperature,
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
        )

    def _init_google_model(self):
        """Initialize Google Gemini model."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        logger.info("Using Google Gemini model: gemini-2.0-flash")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=self.config.temperature,
            google_api_key=api_key,
        )

    def analyze_repository(
        self, repo_url: str, callback: Optional[Callable] = None
    ) -> RepositoryAnalysisResult:
        """
        Analyze a GitHub repository.

        Args:
            repo_url: URL of the GitHub repository
            callback: Optional callback for progress updates

        Returns:
            Analysis results
        """
        # Initialize analysis result
        analysis_result = {}

        try:
            # Set up repository and get repository details
            repo_details = self._get_repository_details_safely(repo_url, callback)
            analysis_result["repo_details"] = repo_details

            # Collect code samples with progress updates
            if callback:
                callback("Collecting code samples")

            start_time = time.time()
            file_metrics, code_samples = self.github_repo.collect_code_samples(
                progress_callback=callback
            )
            elapsed = time.time() - start_time

            if callback:
                callback(f"Collected code samples in {elapsed:.2f}s")

            logger.debug(f"Code samples collected in {elapsed:.2f}s")

            # Process collected data to find Celo integration evidence
            celo_evidence = []
            if callback:
                callback("Searching for blockchain integration evidence")

            start_time = time.time()
            for keyword in self.config.celo_keywords:
                keyword_found = self.github_repo.search_files_for_keywords(
                    self.github_repo.code_sample_files, [keyword]
                )
                celo_evidence.extend(keyword_found)

            elapsed = time.time() - start_time
            logger.debug(
                f"Found {len(celo_evidence)} blockchain integration evidence points in {elapsed:.2f}s"
            )

            # Generate digest for LLM analysis
            if callback:
                callback("Generating repository digest for AI analysis")

            start_time = time.time()
            repo_digest = self._generate_repo_digest(
                repo_details, file_metrics, code_samples, celo_evidence
            )
            elapsed = time.time() - start_time

            # Log digest size
            logger.debug(
                f"Repository digest generated in {elapsed:.2f}s - Size: {len(repo_digest)} characters"
            )

            if len(repo_digest) < 500:
                logger.warn("Repository digest is suspiciously small!")
                logger.debug(f"Full digest: {repo_digest}")

            # Analyze digest with LLM
            if callback:
                callback("Analyzing repository with AI model")

            repo_analysis = self._analyze_with_llm(repo_digest, callback)

            # Combine all analysis components into final result
            for key, value in repo_analysis.items():
                analysis_result[key] = value

            # Add celo evidence to results if not already included
            if "celo_integration" in analysis_result and isinstance(
                analysis_result["celo_integration"], dict
            ):
                if (
                    not analysis_result["celo_integration"].get("evidence")
                    and celo_evidence
                ):
                    analysis_result["celo_integration"]["evidence"] = celo_evidence

            return analysis_result

        except Exception as e:
            error_msg = f"Error analyzing repository: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def _get_repository_details_safely(
        self, repo_url: str, callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Get repository details safely with progress updates.

        Args:
            repo_url: URL of the GitHub repository
            callback: Optional callback for progress updates

        Returns:
            Repository details
        """
        # Use callback to report progress if provided
        if callback:
            callback(f"Fetching repository data for {repo_url}")

        start_time = time.time()

        # Setup the repository
        self.github_repo.setup_repository(repo_url)

        # Get repository details
        repo_details = self.github_repo.get_repository_details()

        elapsed = time.time() - start_time
        if callback:
            callback(f"Fetched repository data in {elapsed:.2f}s")

        logger.debug(f"Repository data fetched in {elapsed:.2f}s")

        return repo_details

    def _generate_repo_digest(
        self,
        repo_details: Dict[str, Any],
        file_metrics: Dict[str, int],
        code_samples: list,
        celo_evidence: list,
    ) -> str:
        """
        Generate a comprehensive digest of the repository for LLM analysis.

        Args:
            repo_details: Repository details
            file_metrics: File metrics
            code_samples: Code samples
            celo_evidence: Celo integration evidence

        Returns:
            Repository digest string
        """
        # Start with repository information
        digest = f"# Repository Information\n"
        digest += f"Name: {repo_details['name']}\n"
        digest += f"Description: {repo_details['description']}\n"
        digest += f"URL: {repo_details['url']}\n"
        digest += f"Stars: {repo_details['stars']}\n"
        digest += f"Forks: {repo_details['forks']}\n"
        digest += f"Main Language: {repo_details['language']}\n\n"

        # Extract potential deployment information from README
        readme_content = self._extract_readme_content(code_samples)
        if readme_content:
            # Look for deployed site URLs in README
            site_urls = self._extract_site_urls(readme_content)
            if site_urls:
                digest += "## Deployment Information (from README)\n"
                digest += "Potential deployed site URLs:\n"
                for url in site_urls:
                    digest += f"- {url}\n"
                digest += "\n"

            # Look for contract addresses in README
            contract_addresses = self._extract_contract_addresses(readme_content)
            if contract_addresses:
                if "## Deployment Information (from README)" not in digest:
                    digest += "## Deployment Information (from README)\n"
                digest += "Potential deployed contract addresses:\n"
                for addr_info in contract_addresses:
                    network = addr_info.get("network", "unknown")
                    context = addr_info.get("context", "")
                    digest += f"- Network: {network}, Address: {addr_info['address']}\n"
                    digest += f"  Context: {context}\n"
                digest += "\n"
            elif "## Deployment Information (from README)" in digest:
                digest += "No deployed contract addresses found in README.\n\n"

        # Add language breakdown if available
        if repo_details.get("main_languages"):
            digest += "## Language Breakdown\n"
            for lang, percentage in repo_details["main_languages"].items():
                digest += f"- {lang}: {percentage}%\n"
            digest += "\n"

        # Add file metrics
        digest += "## File Metrics\n"
        digest += f"Total Files: {file_metrics['file_count']}\n"
        digest += f"Test Files: {file_metrics['test_file_count']}\n"
        digest += f"Documentation Files: {file_metrics['doc_file_count']}\n"
        digest += f"Code Files Analyzed: {file_metrics['code_files_analyzed']}\n\n"

        # Add Celo integration evidence if found
        if celo_evidence:
            digest += "## Blockchain Integration Evidence\n"
            for evidence in celo_evidence:
                digest += f"- Found keyword '{evidence['keyword']}' in file '{evidence['file']}'\n"
            digest += "\n"

        # Add contract addresses found in code files
        code_contract_addresses = self._extract_contract_addresses_from_code(
            code_samples
        )
        if code_contract_addresses:
            digest += "## Deployed Contract Addresses Found in Code\n"
            digest += (
                "These addresses appear to be deployed contracts based on context:\n\n"
            )
            for address_info in code_contract_addresses:
                if address_info.get("is_likely_deployed", False):
                    digest += f"- Address: {address_info['address']}\n"
                    digest += f"  File: {address_info['file']}\n"
                    digest += f"  Context: {address_info['context']}\n"
                    digest += f"  Confidence: High\n\n"
                else:
                    digest += f"- Address: {address_info['address']}\n"
                    digest += f"  File: {address_info['file']}\n"
                    digest += f"  Context: {address_info['context']}\n"
                    digest += f"  Confidence: Low (may not be a deployed contract)\n\n"
            digest += "\n"
        else:
            digest += "## Deployed Contract Addresses\n"
            digest += "No deployed contract addresses found in code files.\n\n"

        # Add code samples
        digest += "## Code Samples\n"
        logger.debug(f"Adding {len(code_samples)} code samples to digest")
        for i, sample in enumerate(code_samples):
            if self.verbose:
                logger.debug(f"Adding sample {i+1}, length: {len(sample)}")
            digest += f"{sample}\n"

        # Log digest length for debugging
        logger.debug(f"Total digest length: {len(digest)} characters")
        if self.verbose:
            logger.debug(f"Digest first 200 chars: {digest[:200]}")
            logger.debug(f"Digest last 200 chars: {digest[-200:]}")

        return digest

    def _extract_readme_content(self, code_samples: list) -> str:
        """
        Extract README content from code samples.

        Args:
            code_samples: List of code samples

        Returns:
            README content or empty string if not found
        """
        for sample in code_samples:
            if "README" in sample or "readme" in sample:
                # Extract content after the file header
                content = sample.split("=" * 10, 2)[-1].strip()
                return content
        return ""

    def _extract_site_urls(self, content: str) -> list:
        """
        Extract potential deployed site URLs from content.

        Args:
            content: Text content to search

        Returns:
            List of potential deployed site URLs
        """
        # Common patterns for deployed site URLs
        patterns = [
            r"(?:deployed|live|demo|website|app|application|site)\s+(?:at|url|link|here)?\s*[:\-=]?\s*(https?://\S+)",
            r"(?:check out|visit|view|access|try|test)\s+(?:the|our|the demo|our demo)?\s+(?:app|site|application|demo|website)\s+(?:at|here)?\s*[:\-=]?\s*(https?://\S+)",
            r"(?:app|application|site|website|demo)\s+(?:is|live|available|deployed)\s+(?:at|here|on|via|at url)?\s*[:\-=]?\s*(https?://\S+)",
            r"(?:frontend|UI|website|application)\s+(?:deployed|hosted|available)\s+(?:at|on|via)?\s*[:\-=]?\s*(https?://\S+)",
            # Simple URL pattern as fallback but only for vercel/netlify/github.io/firebase domains
            r"(https?://(?:[a-zA-Z0-9-]+\.vercel\.app|[a-zA-Z0-9-]+\.netlify\.app|[a-zA-Z0-9-]+\.github\.io|[a-zA-Z0-9-]+\.web\.app|[a-zA-Z0-9-]+\.firebaseapp\.com)/\S*)",
        ]

        results = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Clean up the URL
                url = (
                    match.strip(',:;.()"`\'"').split()[0]
                    if isinstance(match, str)
                    else match[0].strip(',:;.()"`\'"').split()[0]
                )
                if url not in results:
                    results.append(url)

        return results

    def _extract_contract_addresses(self, content: str) -> list:
        """
        Extract potential contract addresses from content.

        Args:
            content: Text content to search

        Returns:
            List of potential contract addresses with network and context
        """
        # Structure for detailed contract address information
        structured_addresses = []

        # Look for deployed contract addresses with specific context
        # Pattern for addresses with "deployed" context
        deployed_patterns = [
            r"(?:deployed|published|created)\s+(?:contract|smart contract|)\s+(?:to|at|on)\s+(?:address)?\s*[:\-=]?\s*(0x[a-fA-F0-9]{40})",
            r"(?:contract|smart contract)\s+(?:address|deployed at)\s*[:\-=]?\s*(0x[a-fA-F0-9]{40})",
            r"(?:address|contract address)[:\-=]?\s*(0x[a-fA-F0-9]{40})",
        ]

        # Network identification patterns
        network_patterns = {
            "celo mainnet": [r"(?:celo|main)(?:net)?", r"production"],
            "alfajores": [r"alfajores", r"test(?:net)?"],
            "baklava": [r"baklava", r"test(?:net)?"],
        }

        # Extract addresses with deployment context
        for pattern in deployed_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Get the full line for context
                line_start = content[: match.start()].rfind("\n")
                if line_start == -1:
                    line_start = 0
                line_end = content.find("\n", match.end())
                if line_end == -1:
                    line_end = len(content)

                full_line = content[line_start:line_end].strip()
                address = match.group(1).strip(',:;.()"`\'"')

                # Skip if address doesn't match the exact format (0x + 40 hex chars)
                if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
                    continue

                # Determine network
                network = "unknown"
                for net_name, patterns in network_patterns.items():
                    for net_pattern in patterns:
                        if re.search(net_pattern, full_line, re.IGNORECASE):
                            network = net_name
                            break
                    if network != "unknown":
                        break

                # Add to structured addresses
                structured_addresses.append(
                    {
                        "address": address,
                        "network": network,
                        "context": full_line,
                        "is_likely_deployed": True,  # This is likely a deployed contract due to context
                    }
                )

        # If no deployed addresses found with specific context, look for generic addresses
        if not structured_addresses:
            # Simple contract address pattern as fallback
            simple_pattern = r"(0x[a-fA-F0-9]{40})"
            matches = re.finditer(simple_pattern, content)

            for match in matches:
                address = match.group(1)

                # Skip if address doesn't match the exact format
                if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
                    continue

                # Get surrounding context (20 chars before and after)
                context_start = max(0, match.start() - 20)
                context_end = min(len(content), match.end() + 20)
                context = content[context_start:context_end].strip()

                # Check if this appears to be a deployed contract
                is_deployed = False
                deploy_keywords = ["deploy", "contract", "address", "published"]
                for keyword in deploy_keywords:
                    if keyword in context.lower():
                        is_deployed = True
                        break

                # Only include if it's likely a deployed contract
                if is_deployed:
                    structured_addresses.append(
                        {
                            "address": address,
                            "network": "unknown",
                            "context": context,
                            "is_likely_deployed": False,  # This is less certain
                        }
                    )

        # Further filter to remove false positives
        filtered_addresses = []
        for addr_info in structured_addresses:
            # Skip if context suggests this isn't a deployed contract
            lower_context = addr_info["context"].lower()

            # Negative indicators (skip if present)
            negative_indicators = [
                "recipient",
                "from address",
                "to address",
                "sender",
                "receiver",
                "wallet",
                "account",
                "example",
                "sample",
                "transfer",
                "send to",
            ]

            if any(indicator in lower_context for indicator in negative_indicators):
                continue

            # Check for positive deployment indicators
            positive_indicators = [
                "deployed",
                "contract",
                "publish",
                "create",
                "deploy",
            ]

            # Only include addresses with clear deployment context or that were categorized as likely deployed
            if addr_info["is_likely_deployed"] or any(
                indicator in lower_context for indicator in positive_indicators
            ):
                filtered_addresses.append(addr_info)

        # Return only unique addresses (no duplicates)
        unique_addresses = []
        unique_addr_values = set()

        for addr_info in filtered_addresses:
            if addr_info["address"] not in unique_addr_values:
                unique_addr_values.add(addr_info["address"])
                unique_addresses.append(addr_info)

        return unique_addresses

    def _extract_contract_addresses_from_code(self, code_samples: list) -> list:
        """
        Extract potential contract addresses from code samples.

        Args:
            code_samples: List of code samples

        Returns:
            List of potential contract addresses with file info
        """
        contract_addresses = []
        for sample in code_samples:
            # Skip if it's a README or image file
            if (
                "README" in sample
                or "readme" in sample
                or any(
                    ext in sample for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg"]
                )
            ):
                continue

            # Extract file name
            file_name = ""
            file_match = re.search(r"={10,}\nFile: (.*?)\n={10,}", sample)
            if file_match:
                file_name = file_match.group(1)
            else:
                continue

            # Extract content
            content = sample.split("=" * 10, 2)[-1].strip()

            # Skip files that likely contain example addresses rather than deployed contracts
            lower_file = file_name.lower()
            if any(
                term in lower_file
                for term in ["test", "example", "mock", "sample", "spec"]
            ):
                continue

            # Look for contract addresses with deployment context
            # First look for specific deployment patterns
            deploy_patterns = [
                r"(?:deploy(?:ed)?|publish(?:ed)?)\s+(?:to|at|on|contract)?\s*[:\-=]?\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
                r"[\"'](?:contractAddress|deployedAddress|contractAddr)[\"']\s*:\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
                r"(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:ContractAddress|DeployedContract|DeployedAddr))(?:\s*:\s*string)?\s*=\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
            ]

            for pattern in deploy_patterns:
                if "ContractAddress" in pattern:
                    # Special case for variable pattern which has two groups
                    matches = re.findall(pattern, content)
                    for var_name, address in matches:
                        if re.match(r"^0x[a-fA-F0-9]{40}$", address):
                            contract_addresses.append(
                                {
                                    "address": address,
                                    "file": file_name,
                                    "context": f"Deployed contract variable: {var_name}",
                                    "is_likely_deployed": True,
                                }
                            )
                else:
                    # Regular pattern with one group
                    matches = re.findall(pattern, content)
                    for address in matches:
                        if re.match(r"^0x[a-fA-F0-9]{40}$", address):
                            contract_addresses.append(
                                {
                                    "address": address,
                                    "file": file_name,
                                    "context": "Deployment context",
                                    "is_likely_deployed": True,
                                }
                            )

            # Look for contract configuration in config or env files
            if any(
                term in lower_file
                for term in ["config", ".env", "environment", "deploy", "contract"]
            ):
                # Look for patterns in config files
                config_patterns = [
                    r"[\"'](?:CONTRACT_ADDRESS|CONTRACT_ADDR|DEPLOYED_ADDRESS|DEPLOYED_CONTRACT)[\"']\s*[=:]\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
                    r"(?:CONTRACT_ADDRESS|CONTRACT_ADDR|DEPLOYED_ADDRESS|DEPLOYED_CONTRACT)\s*=\s*[\"']?(0x[a-fA-F0-9]{40})[\"']?",
                    r"[\"'](?:address|contractAddress|addr)[\"']\s*:\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
                ]

                for pattern in config_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for address in matches:
                        if re.match(r"^0x[a-fA-F0-9]{40}$", address):
                            contract_addresses.append(
                                {
                                    "address": address,
                                    "file": file_name,
                                    "context": "Config/env file",
                                    "is_likely_deployed": True,
                                }
                            )

            # For non-config files, be more selective about which addresses to include
            elif not any(
                term in lower_file for term in ["config", ".env", "deploy", "contract"]
            ):
                # Skip unnecessary files that often contain non-deployed addresses
                if any(
                    term in lower_file for term in ["test", "example", "mock", "sample"]
                ):
                    continue

                # Look for variable declarations with specific naming conventions suggesting deployment
                var_patterns = [
                    r"(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:ContractAddress|DeployedContract|ContractAddr))(?:\s*:\s*string)?\s*=\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
                    r"(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*Address)(?:\s*:\s*string)?\s*=\s*[\"'](0x[a-fA-F0-9]{40})[\"']",
                ]

                for pattern in var_patterns:
                    matches = re.findall(pattern, content)
                    for var_name, address in matches:
                        # Skip if the variable suggests this isn't a deployed contract
                        lower_var = var_name.lower()
                        if any(
                            term in lower_var
                            for term in [
                                "example",
                                "sample",
                                "test",
                                "recipient",
                                "sender",
                                "wallet",
                            ]
                        ):
                            continue

                        if re.match(r"^0x[a-fA-F0-9]{40}$", address):
                            # Check variable name to determine if it's likely a deployed contract
                            is_likely_deployed = any(
                                term in lower_var
                                for term in ["contract", "deploy", "publish"]
                            )

                            contract_addresses.append(
                                {
                                    "address": address,
                                    "file": file_name,
                                    "context": f"Variable: {var_name}",
                                    "is_likely_deployed": is_likely_deployed,
                                }
                            )

        # Filter the addresses to remove false positives
        filtered_addresses = []
        seen_addresses = set()

        # First add all addresses marked as likely deployed
        for addr_info in contract_addresses:
            if (
                addr_info["is_likely_deployed"]
                and addr_info["address"] not in seen_addresses
            ):
                filtered_addresses.append(addr_info)
                seen_addresses.add(addr_info["address"])

        # If no likely deployed addresses found, include other addresses but mark them as uncertain
        if not filtered_addresses:
            for addr_info in contract_addresses:
                if addr_info["address"] not in seen_addresses:
                    filtered_addresses.append(addr_info)
                    seen_addresses.add(addr_info["address"])

        return filtered_addresses

    def _analyze_with_llm(
        self, repo_digest: str, callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Analyze repository digest with LLM.

        Args:
            repo_digest: Repository digest to analyze
            callback: Optional callback for progress updates

        Returns:
            Analysis results
        """
        try:
            # Count input tokens - just estimate for non-Anthropic
            start_time = time.time()

            if self.verbose:
                input_tokens = 0
                if self.model_provider == "anthropic":
                    input_tokens = anthropic.count_tokens(SYSTEM_PROMPT + repo_digest)
                else:
                    # Rough estimate: 4 chars per token
                    input_tokens = (len(SYSTEM_PROMPT) + len(repo_digest)) // 4

                logger.debug(f"Input tokens (estimated): {input_tokens}")

                if callback:
                    callback(
                        f"Sending approximately {input_tokens} tokens to LLM for analysis"
                    )

            # Track token usage with OpenAI callback (works for multiple providers)
            with get_openai_callback() as cb:
                try:
                    # No need to truncate for Gemini with 900k token limit
                    logger.debug(
                        f"Repository digest length: {len(repo_digest)} characters"
                    )

                    # We estimate about 4 characters per token, so max 3.6M characters
                    if len(repo_digest) > 3600000:  # Only warn at extreme sizes
                        logger.warn(
                            f"Repository digest is extremely large ({len(repo_digest)} chars). May approach model limits."
                        )

                    # Get LLM response
                    logger.debug(
                        f"Sending prompt to LLM: system={len(SYSTEM_PROMPT)} chars, user={len(repo_digest)} chars"
                    )

                    if callback:
                        callback("Waiting for AI model response...")

                    response = self.llm.invoke(
                        [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": repo_digest},
                        ]
                    )
                    content = response.content

                    # Debug output
                    if self.verbose:
                        logger.debug(f"LLM response received. Length: {len(content)}")
                        logger.debug(f"Response starts with: {content[:100]}...")

                    # Log token usage
                    if self.verbose:
                        if callback:
                            callback(
                                f"Analysis completed. Input tokens: {cb.prompt_tokens}, Output tokens: {cb.completion_tokens}"
                            )
                        logger.debug(
                            f"Token usage - Input: {cb.prompt_tokens}, Output: {cb.completion_tokens}, Total: {cb.total_tokens}"
                        )
                except Exception as api_error:
                    logger.error(f"API call error: {str(api_error)}")
                    if callback:
                        callback(f"Error calling AI model: {str(api_error)}")
                    return {"error": f"API call failed: {str(api_error)}"}

            # Parse JSON from response
            try:
                if callback:
                    callback("Extracting analysis from AI response")

                # Extract JSON from response (may be wrapped in markdown code blocks)
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content

                # Debug JSON extraction
                if self.verbose:
                    logger.debug(
                        f"Extracted JSON string (first 100 chars): {json_str[:100]}..."
                    )

                analysis_result = json.loads(json_str)

                # Add token metrics if verbose mode is enabled
                if self.verbose:
                    analysis_result["token_metrics"] = {
                        "input_tokens": cb.prompt_tokens,
                        "output_tokens": cb.completion_tokens,
                        "total_tokens": cb.total_tokens,
                    }

                elapsed = time.time() - start_time
                logger.debug(f"LLM analysis completed in {elapsed:.2f}s")

                if callback:
                    callback(f"AI analysis completed in {elapsed:.2f}s")

                return analysis_result

            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON from LLM response: {str(json_err)}")
                if callback:
                    callback("Error parsing AI analysis result")
                return {
                    "error": f"Failed to parse analysis result: {str(json_err)}",
                    "raw_response": (
                        content[:500] + "...(truncated)"
                        if len(content) > 500
                        else content
                    ),
                }

        except Exception as e:
            error_msg = f"Error in LLM analysis: {str(e)}"
            logger.error(error_msg)
            if callback:
                callback(f"Error in AI analysis: {str(e)}")
            return {"error": error_msg}
