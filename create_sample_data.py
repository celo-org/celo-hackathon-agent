import pandas as pd

# Create sample data for testing
sample_data = [
    {
        "project_name": "Celo Composer",
        "project_description": "celo-composer is a starter project with all code needed to build, deploy, and upgrade a dapps on Celo.",
        "project_github_url": "https://github.com/celo-org/celo-composer",
        "project_owner_github_url": ["https://github.com/viral-sangani"],
        "project_url": "NA",
    },
    {
        "project_name": "Akashic",
        "project_description": "NA",
        "project_github_url": "https://github.com/akashic-fund/akashic",
        "project_owner_github_url": ["https://github.com/Prajjawalk"],
        "project_url": "NA",
    },
]

# Create DataFrame
df = pd.DataFrame(sample_data)

# Save to Excel
df.to_excel("sample_projects.xlsx", index=False)

print("Sample data created and saved to 'sample_projects.xlsx'")
