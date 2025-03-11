"""
Celo blockchain integration detection functionality.
"""

import json
import base64
from typing import Dict, List, Tuple, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models.types import CeloIntegrationResult, CeloEvidence
from src.models.config import Config
from src.utils.timeout import AIAnalysisError, with_timeout
from prompts.celo_integration import (
    CELO_INTEGRATION_PROMPT,
    HUMAN_CELO_INTEGRATION_PROMPT,
    CELO_ANALYSIS_PROMPT,
    HUMAN_CELO_ANALYSIS_PROMPT,
)


class CeloIntegrationDetector:
    """Detects Celo blockchain integration in repositories."""

    def __init__(self, config: Config, llm=None):
        """
        Initialize with configuration and optional LLM.

        Args:
            config: Configuration object
            llm: Optional LangChain LLM instance
        """
        self.config = config
        self.llm = llm

    def check_without_access(
        self, repo_owner: str, repo_name: str, repo_description: str
    ) -> CeloIntegrationResult:
        """
        Check for Celo integration without direct repository access.

        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_description: Repository description

        Returns:
            CeloIntegrationResult with estimated integration status
        """
        # Special case for Celo organization repos - they are likely to be Celo-related
        if repo_owner.lower() == "celo-org" or "celo" in repo_owner.lower():
            return {
                "integrated": True,
                "evidence": [{"file": "Organization name", "keyword": "celo-org"}],
                "analysis": f"This repository belongs to the {repo_owner} organization, which is likely related to the Celo blockchain ecosystem. Unable to perform detailed analysis due to API access limitations.",
            }

        # Check for Celo keywords in name/description
        repo_name_lower = repo_name.lower()
        repo_description_lower = repo_description.lower() if repo_description else ""

        # Collect evidence from name and description
        evidence = []
        for keyword in self.config.celo_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in repo_name_lower:
                evidence.append({"file": "Repository name", "keyword": keyword})
            elif keyword_lower in repo_description_lower:
                evidence.append({"file": "Repository description", "keyword": keyword})

        # If we found evidence, return it
        if evidence:
            return {
                "integrated": True,
                "evidence": evidence,
                "analysis": "The repository name or description contains Celo-related keywords. Unable to perform detailed analysis due to API access limitations.",
            }

        # If no basic evidence and we have a LLM, use it for more detailed analysis
        if self.llm is not None:
            try:
                return self.estimate_integration_with_ai(
                    repo_owner, repo_name, repo_description
                )
            except Exception as e:
                print(f"Error in AI estimation of Celo integration: {str(e)}")

        # Default to not integrated if no evidence found
        return {"integrated": False, "evidence": [], "repositories_with_celo": 0}

    def estimate_integration_with_ai(
        self, repo_owner: str, repo_name: str, repo_description: str
    ) -> CeloIntegrationResult:
        """
        Estimate Celo integration using AI based on repository metadata.

        Args:
            repo_owner: Owner of the repository
            repo_name: Name of the repository
            repo_description: Repository description

        Returns:
            CeloIntegrationResult with AI-based integration estimation
        """
        # Format keywords for the prompt
        keywords_str = ", ".join(self.config.celo_keywords)

        # Create system prompt with keywords
        system_template = CELO_INTEGRATION_PROMPT.format(keywords=keywords_str)

        # Create prompt for Celo integration search
        celo_prompt = ChatPromptTemplate.from_messages(
            [("system", system_template), ("human", HUMAN_CELO_INTEGRATION_PROMPT)]
        )

        # Format repository info
        repo_info_str = f"""Repository: {repo_owner}/{repo_name}
        Description: {repo_description}
        """

        try:
            # Run analysis with the AI model
            celo_chain = celo_prompt | self.llm | StrOutputParser()
            celo_result = celo_chain.invoke(
                {
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                    "repo_info": repo_info_str,
                }
            )

            # Parse AI response
            celo_json = json.loads(celo_result)

            is_integrated = celo_json.get("is_celo_integrated", False)
            confidence = celo_json.get("confidence", 0)

            # Only report as integrated if confidence is reasonable
            if is_integrated and confidence > 50:
                evidence = []
                for reason in celo_json.get("evidence", []):
                    evidence.append({"file": "AI analysis", "keyword": reason})

                return {
                    "integrated": True,
                    "evidence": evidence,
                    "analysis": celo_json.get("explanation", "")
                    + " (Note: This is an estimate based on limited information)",
                    "repositories_with_celo": 1,
                }

            # If not integrated or low confidence
            return {"integrated": False, "evidence": [], "repositories_with_celo": 0}
        except Exception as e:
            raise AIAnalysisError(
                f"Error in AI estimation of Celo integration: {str(e)}"
            )

    @with_timeout(60)
    def check_integration_with_gitingest(
        self, repo_content: str, repo_owner: str, repo_name: str
    ) -> CeloIntegrationResult:
        """
        Check for Celo integration in a repository using gitingest data.

        Args:
            repo_content: Repository content from gitingest
            repo_owner: Owner of the repository
            repo_name: Name of the repository

        Returns:
            CeloIntegrationResult with integration details
        """
        try:
            # Step 1: Check config files for Celo keywords
            evidence = self.check_config_files(repo_content)

            # Step 2: If no evidence found, check README files
            if not evidence:
                evidence = self.check_readme_files(repo_content)

            # Step 3: If still no evidence, search all content
            if not evidence:
                evidence = self.search_repository_content(repo_content)

            # Determine integration status
            is_integrated = len(evidence) > 0

            # Step 4: If integrated, run deeper analysis with LLM
            analysis = None
            if is_integrated and self.llm is not None:
                analysis = self.analyze_celo_evidence(evidence)

            return {
                "integrated": is_integrated,
                "evidence": evidence,
                "analysis": analysis,
                "repositories_with_celo": 1 if is_integrated else 0,
            }
        except Exception as e:
            error_msg = f"Error checking Celo integration: {str(e)}"
            print(error_msg)

            # Fallback to checking repository name
            has_celo_in_name = "celo" in repo_name.lower()

            evidence = []
            if has_celo_in_name:
                evidence = [{"file": "Repository name", "keyword": "celo"}]

            return {
                "integrated": has_celo_in_name,
                "evidence": evidence,
                "error": error_msg,
                "repositories_with_celo": 1 if has_celo_in_name else 0,
            }
    
    @with_timeout(60)
    def check_integration(
        self, repo, repo_owner: str, repo_name: str
    ) -> CeloIntegrationResult:
        """
        Check for Celo integration in a repository.

        Args:
            repo: GitHub repository object (can be a GitHubRepository instance with repo_data attribute)
            repo_owner: Owner of the repository
            repo_name: Name of the repository

        Returns:
            CeloIntegrationResult with integration details
        """
        # Check if this is a gitingest-based repository object
        if hasattr(repo, 'repo_data') and hasattr(repo, 'content') and repo.content:
            return self.check_integration_with_gitingest(repo.content, repo_owner, repo_name)
        
        # Legacy implementation for PyGitHub
        try:
            # Step 1: Check config files for Celo keywords
            evidence = []
            
            # Check for the existence of specific config files
            for file_path in self.config.celo_files:
                try:
                    content = repo.get_contents(file_path)
                    if content and content.type == "file":
                        content_str = base64.b64decode(content.content).decode("utf-8")
                        for keyword in self.config.celo_keywords:
                            if keyword.lower() in content_str.lower():
                                evidence.append({"file": file_path, "keyword": keyword})
                except Exception:
                    # File doesn't exist, skip
                    continue
            
            # Step 2: If no evidence found, check README files
            if not evidence:
                readme_files = [
                    "README.md",
                    "README",
                    "Readme.md",
                    "readme.md",
                    "docs/README.md",
                    "docs/Readme.md",
                    "documentation/README.md",
                ]
                
                for readme_file in readme_files:
                    try:
                        content = repo.get_contents(readme_file)
                        if content and content.type == "file":
                            content_str = base64.b64decode(content.content).decode("utf-8")
                            for keyword in self.config.celo_keywords:
                                if keyword.lower() in content_str.lower():
                                    evidence.append({"file": readme_file, "keyword": keyword})
                    except Exception:
                        # File doesn't exist, skip
                        continue

            # Determine integration status
            is_integrated = len(evidence) > 0

            # Step 4: If integrated, run deeper analysis with LLM
            analysis = None
            if is_integrated and self.llm is not None:
                analysis = self.analyze_celo_evidence(evidence)

            return {
                "integrated": is_integrated,
                "evidence": evidence,
                "analysis": analysis,
                "repositories_with_celo": 1 if is_integrated else 0,
            }
        except Exception as e:
            error_msg = f"Error checking Celo integration: {str(e)}"
            print(error_msg)

            # Fallback to checking repository name
            has_celo_in_name = "celo" in repo_name.lower()

            evidence = []
            if has_celo_in_name:
                evidence = [{"file": "Repository name", "keyword": "celo"}]

            return {
                "integrated": has_celo_in_name,
                "evidence": evidence,
                "error": error_msg,
                "repositories_with_celo": 1 if has_celo_in_name else 0,
            }

    def check_config_files(self, repo_content: str) -> List[CeloEvidence]:
        """
        Check repository content for Celo keywords in configuration files.

        Args:
            repo_content: Repository content from gitingest

        Returns:
            List of evidence dictionaries
        """
        evidence = []
        config_files = self.config.celo_files

        # Process the content to find configuration files
        for file_path in config_files:
            # Look for file patterns in the content
            file_lower = file_path.lower()
            repo_content_lower = repo_content.lower()
            
            # If the file is mentioned in the content
            if file_lower in repo_content_lower:
                # Try to find the file content
                file_pattern = r'{}[\s\n]+(.*?)(?=[-\w./]+\.\w+|\Z)'.format(file_path.replace('.', '\\.'))
                import re
                match = re.search(file_pattern, repo_content, re.DOTALL | re.IGNORECASE)
                
                if match:
                    file_content = match.group(1)
                    # Check for Celo keywords
                    for keyword in self.config.celo_keywords:
                        if keyword.lower() in file_content.lower():
                            evidence.append({"file": file_path, "keyword": keyword})
                            break
                else:
                    # If we can't find specific content, just check if the keyword appears near the filename
                    for keyword in self.config.celo_keywords:
                        keyword_lower = keyword.lower()
                        # Check if keyword appears within 500 characters of the filename
                        pattern = r'{}\s*[^/]{{0,500}}{}'.format(
                            re.escape(file_lower), 
                            re.escape(keyword_lower)
                        )
                        if re.search(pattern, repo_content_lower, re.DOTALL):
                            evidence.append({"file": file_path, "keyword": keyword})
                            break

        return evidence

    def check_readme_files(self, repo_content: str) -> List[CeloEvidence]:
        """
        Check repository content for Celo keywords in README files.

        Args:
            repo_content: Repository content from gitingest

        Returns:
            List of evidence dictionaries
        """
        evidence = []
        readme_files = [
            "README.md",
            "README",
            "Readme.md",
            "readme.md",
            "docs/README.md",
            "docs/Readme.md",
            "documentation/README.md",
        ]

        # Process the content to find README files
        for file_path in readme_files:
            # Look for file patterns in the content
            file_lower = file_path.lower()
            repo_content_lower = repo_content.lower()
            
            # If the file is mentioned in the content
            if file_lower in repo_content_lower:
                # Try to find the file content
                file_pattern = r'{}[\s\n]+(.*?)(?=[-\w./]+\.\w+|\Z)'.format(file_path.replace('.', '\\.'))
                import re
                match = re.search(file_pattern, repo_content, re.DOTALL | re.IGNORECASE)
                
                if match:
                    file_content = match.group(1)
                    # Check for Celo keywords
                    for keyword in self.config.celo_keywords:
                        if keyword.lower() in file_content.lower():
                            evidence.append({"file": file_path, "keyword": keyword})
                            break
                else:
                    # If we can't find specific content, just check if the keyword appears near the filename
                    for keyword in self.config.celo_keywords:
                        keyword_lower = keyword.lower()
                        # Check if keyword appears within 1000 characters of the filename (README files can be long)
                        pattern = r'{}\s*[^/]{{0,1000}}{}'.format(
                            re.escape(file_lower), 
                            re.escape(keyword_lower)
                        )
                        if re.search(pattern, repo_content_lower, re.DOTALL):
                            evidence.append({"file": file_path, "keyword": keyword})
                            break

        return evidence

    def search_repository_content(self, repo_content: str) -> List[CeloEvidence]:
        """
        Search repository content for Celo keywords using gitingest data.

        Args:
            repo_content: Repository content from gitingest

        Returns:
            List of evidence dictionaries
        """
        evidence = []
        import re
        
        # Process the content to find Celo keywords
        for keyword in self.config.celo_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in repo_content.lower():
                # Try to find a file context for the keyword
                # Look for the keyword in context of a file mention
                pattern = r'([-\w./]+\.\w+)[\s\n]+[^/]*{}[^/]*'.format(re.escape(keyword_lower))
                matches = re.finditer(pattern, repo_content.lower(), re.IGNORECASE)
                
                # Add each match as evidence
                found_files = set()  # Keep track of files we've already added
                for match in matches:
                    file_path = match.group(1)
                    if file_path not in found_files:
                        evidence.append({"file": file_path, "keyword": keyword})
                        found_files.add(file_path)
                
                # If no file context found, add generic evidence
                if not found_files:
                    evidence.append({"file": "repository_content", "keyword": keyword})

        return evidence

    def analyze_celo_evidence(self, evidence: List[CeloEvidence]) -> str:
        """
        Analyze Celo integration evidence using AI.

        Args:
            evidence: List of Celo integration evidence

        Returns:
            Analysis string from AI
        """
        if not self.llm:
            return None

        try:
            # Create prompt for Celo integration analysis
            celo_analysis_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", CELO_ANALYSIS_PROMPT),
                    ("human", HUMAN_CELO_ANALYSIS_PROMPT),
                ]
            )

            # Format evidence for the prompt
            evidence_str = "\n".join(
                [f"- Found '{e['keyword']}' in {e['file']}" for e in evidence]
            )

            # Run analysis with the AI model
            analysis_chain = celo_analysis_prompt | self.llm | StrOutputParser()
            analysis = analysis_chain.invoke({"evidence": evidence_str})

            return analysis
        except Exception as e:
            print(f"Error in Celo integration analysis: {str(e)}")
            return None
