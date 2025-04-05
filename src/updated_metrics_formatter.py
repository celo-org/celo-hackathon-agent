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
                for item in evidence["contract_addresses"][:5]:  # Limit to 5 files
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