"""
Celo blockchain integration detection functionality.
"""

import json
import re
from typing import Dict, List, Tuple, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models.types import CeloIntegrationResult, CeloEvidence
from src.models.config import Config
from src.utils.timeout import AIAnalysisError
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

    def check_integration(
        self, repo, repo_owner: str, repo_name: str
    ) -> CeloIntegrationResult:
        """
        Check for Celo integration in a repository using GitIngest data.

        Args:
            repo: Repository object with GitIngest data
            repo_owner: Owner of the repository
            repo_name: Name of the repository

        Returns:
            CeloIntegrationResult with integration details
        """
        try:
            # Check if repository data is available
            if not hasattr(repo, 'repo_data') or repo.repo_data is None:
                return self.check_without_access(repo_owner, repo_name, "")
            
            repo_data = repo.repo_data
            summary = repo_data.get("summary", "")
            tree = repo_data.get("tree", "")
            content = repo_data.get("content", "")
            
            # Collect evidence
            evidence = []
            
            # Step 1: Check for Celo in repository name
            if "celo" in repo_name.lower():
                evidence.append({"file": "Repository name", "keyword": "celo"})
            
            # Step 2: Check for Celo keywords in repository summary
            for keyword in self.config.celo_keywords:
                if keyword.lower() in summary.lower():
                    evidence.append({"file": "Repository summary", "keyword": keyword})
            
            # Step 3: Check key files for Celo keywords in content
            # Look for file matches in tree and extract content from the digest
            for file_path in self.config.celo_files:
                file_pattern = f"```\\s*.*{re.escape(file_path)}\\s*\\n(.*?)```"
                file_matches = re.finditer(file_pattern, content, re.DOTALL)
                
                for match in file_matches:
                    file_content = match.group(1)
                    for keyword in self.config.celo_keywords:
                        if keyword.lower() in file_content.lower():
                            evidence.append({"file": match.group(0).split('\n')[0], "keyword": keyword})
            
            # Step 4: Check README files specifically
            readme_pattern = r"```\s*(.*README.*\.md)\s*\n(.*?)```"
            readme_matches = re.finditer(readme_pattern, content, re.DOTALL)
            for match in readme_matches:
                readme_path = match.group(1)
                readme_content = match.group(2)
                for keyword in self.config.celo_keywords:
                    if keyword.lower() in readme_content.lower():
                        evidence.append({"file": readme_path, "keyword": keyword})
            
            # Determine integration status
            is_integrated = len(evidence) > 0

            # If integrated and LLM is available, run deeper analysis
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

    def search_repo_content_for_keywords(self, content: str) -> List[CeloEvidence]:
        """
        Search repository content for Celo keywords.
        
        Args:
            content: Repository content string from GitIngest
            
        Returns:
            List of evidence dictionaries
        """
        evidence = []
        
        # Extract code blocks from the content
        code_pattern = r"```\s*([^`\n]+)\s*\n(.*?)```"
        code_blocks = re.finditer(code_pattern, content, re.DOTALL)
        
        for block in code_blocks:
            file_path = block.group(1)
            file_content = block.group(2)
            
            # Skip binary files and non-meaningful paths
            if file_path.lower().endswith(
                (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar")
            ):
                continue
                
            # Check for Celo keywords in the file content
            for keyword in self.config.celo_keywords:
                if keyword.lower() in file_content.lower():
                    evidence.append({"file": file_path, "keyword": keyword})
                    # Once evidence is found for this file, move to next one
                    break
                    
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
            
        # If we have too many evidence items, limit to the first 10 to avoid overwhelming the API
        if len(evidence) > 10:
            limited_evidence = evidence[:10]
            evidence_note = f" (showing 10 of {len(evidence)} items)"
        else:
            limited_evidence = evidence
            evidence_note = ""

        try:
            # Use a simpler template approach to avoid prompt issues
            combined_prompt = CELO_ANALYSIS_PROMPT + "\n\n" + HUMAN_CELO_ANALYSIS_PROMPT
            celo_analysis_prompt = ChatPromptTemplate.from_template(combined_prompt)
            
            # Format evidence for the prompt
            evidence_str = "\n".join(
                [f"- Found '{e['keyword']}' in {e['file']}" for e in limited_evidence]
            ) + evidence_note

            # Run analysis with the AI model, with a lower temperature for more reliability
            # Use a slightly modified model configuration for this specific task
            modified_llm = self.llm
            if hasattr(self.llm, 'temperature'):
                modified_llm = self.llm.with_config(temperature=0.1)
                
            # Run analysis with the AI model
            analysis_chain = celo_analysis_prompt | modified_llm | StrOutputParser()
            analysis = analysis_chain.invoke({"evidence": evidence_str})

            return analysis
        except Exception as e:
            print(f"Error in Celo integration analysis: {str(e)}")
            # Provide a basic fallback analysis without using the LLM
            keywords_found = set(e['keyword'] for e in evidence)
            files_with_evidence = set(e['file'] for e in evidence)
            
            fallback_analysis = (
                f"Found {len(evidence)} references to Celo in {len(files_with_evidence)} files. "
                f"Keywords detected: {', '.join(keywords_found)}. "
                "This repository appears to integrate with the Celo blockchain."
            )
            return fallback_analysis
