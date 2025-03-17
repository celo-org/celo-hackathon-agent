# 🌱 Celo Hackathon Project Analyzer

![Celo](https://img.shields.io/badge/Celo-Blockchain-brightgreen)
![AI](https://img.shields.io/badge/AI-Powered-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)

An intelligent tool that analyzes GitHub repositories for Celo hackathon projects, evaluating code quality and checking for Celo blockchain integration using AI-powered analysis.

## ✨ Features

- 📊 **Multi-Repository Analysis**: Analyze multiple GitHub repositories from Excel data
- 🔍 **Intelligent Code Review**: AI-powered assessment of code quality and best practices
- 🔗 **Celo Integration Detection**: Automatically checks for Celo blockchain integration
- 📝 **Detailed Reports**: Generates comprehensive reports with LLM-driven insights
- 🧠 **Smart Recommendations**: Provides suggestions for improving code and integration

## 🚀 Installation

1. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/celo-hackathon-agent.git
   cd celo-hackathon-agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API tokens**:
   - Create a GitHub token with repo scope at [GitHub Settings](https://github.com/settings/tokens)
   - Get an Anthropic API key from [Anthropic Console](https://console.anthropic.com/)
   - Create a `.env` file:
     ```
     GITHUB_TOKEN=your_github_token_here
     ANTHROPIC_API_KEY=your_anthropic_api_key_here
     ```

## 🛠️ Usage

### 📋 Prepare Project Data

Create an Excel file with the following columns:
- `project_name`: Name of the project
- `project_description`: Brief description of the project
- `project_github_url`: URL of the project's GitHub repository (can be comma-separated for multiple repos)
- `project_owner_github_url`: GitHub URLs of project owners (can be comma-separated)
- `project_url`: Main website URL of the project

Or generate sample data:
```bash
python create_sample_data.py
```

### 🔍 Run the Analyzer

#### Using the Makefile (recommended):
```bash
# Display available commands
make help

# Install dependencies
make setup

# Run in interactive mode
make run

# Analyze projects from an Excel file
make run-excel FILE=sample_projects.xlsx VERBOSE=1

# Analyze a GitHub repository directly
make run-url URL="https://github.com/user/repo"

# Analyze with custom project name
make run-url URL="https://github.com/user/repo" NAME="My Project" VERBOSE=1

# Clean up generated files
make clean
```

#### Using the interactive CLI tool:
```bash
./devrel-agent.py
```

This will launch an interactive CLI that guides you through the process.

#### Using the legacy script:
```bash
python run.py --excel sample_projects.xlsx --output reports --verbose
```

#### Using the CLI tool in non-interactive mode:
```bash
# Analyze from Excel file
./devrel-agent.py --non-interactive --excel sample_projects.xlsx --verbose

# Analyze direct GitHub URLs (project name will be automatically extracted from repository name)
./devrel-agent.py --non-interactive --urls "https://github.com/user/repo1,https://github.com/user/repo2" --verbose

# Analyze direct GitHub URLs with custom project name
./devrel-agent.py --non-interactive --urls "https://github.com/user/repo1,https://github.com/user/repo2" --project-name "My Project" --verbose
```

#### Optional Arguments:
- `--config`: Path to custom configuration file (default: `config.json`)
- `--output`: Directory to save reports (default: `reports`)
- `--verbose`: Display detailed progress information

### ⚙️ Configuration

Customize the analysis by editing `config.json`:
- `weights`: Adjust the weight of each code quality category
- `celo_keywords`: Keywords to search for when checking Celo integration
- `celo_files`: Files to check for Celo-related configurations

## 📊 Project Structure

```
celo-hackathon-agent/
├── src/
│   ├── models/         # Data types and configuration
│   ├── analyzer/       # Analysis components
│   ├── utils/          # Utility functions
│   ├── reporting/      # Report generation
│   └── main.py         # Main application logic
├── run.py              # Legacy entry point script
├── devrel-agent.py     # Interactive CLI tool
├── Makefile            # Simplified command interface
├── config.json         # Configuration
└── requirements.txt    # Dependencies
```

## 📝 Output

The tool generates:
- `summary.md`: Overview of all analyzed projects
- Individual project reports with detailed analysis:
  - AI-powered code quality assessment with explanations
  - Analysis of coding standards and best practices
  - Suggestions for code improvements
  - Comprehensive evaluation of Celo blockchain integration
  - Evidence and detailed analysis of Celo technology usage
- `results.json`: Raw data in JSON format for further processing

## 📄 License

MIT

---

Made with ❤️ for the Celo ecosystem