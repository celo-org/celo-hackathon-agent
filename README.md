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
   - Get an Anthropic API key from [Anthropic Console](https://console.anthropic.com/)
   - Create a `.env` file:
     ```
     ANTHROPIC_API_KEY=your_anthropic_api_key_here
     ```

## 🔄 Repository Analysis with Gitingest

This tool uses [gitingest](https://gitingest.com/) to analyze GitHub repositories. Gitingest provides:

- Efficient repository data extraction without requiring GitHub tokens
- Smart formatting optimized for LLM analysis
- Comprehensive code samples and directory structure information

The integration with gitingest simplifies the repository analysis process and eliminates the need for a GitHub API token.

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

#### Standard Version
```bash
python run.py --excel sample_projects.xlsx --output reports --verbose
```

#### Advanced Agent-Based Version with Parallel Execution
```bash
python run_agents.py --excel sample_projects.xlsx --output reports --verbose --workers 4
```

#### Analyze a Single Repository
```bash
python run_agents.py --single https://github.com/username/repository --output reports
```

#### Optional Arguments:
- `--config`: Path to custom configuration file (default: `config.json`)
- `--output`: Directory to save reports (default: `reports`)
- `--verbose`: Display detailed progress information
- `--workers`: Number of parallel analysis workers (default: CPU count)
- `--single`: URL of a single repository to analyze

### ⚙️ Configuration

Customize the analysis by editing `config.json`:
- `weights`: Adjust the weight of each code quality category
- `celo_keywords`: Keywords to search for when checking Celo integration
- `celo_files`: Files to check for Celo-related configurations

## 📊 Project Structure

```
celo-hackathon-agent/
├── src/
│   ├── agents/         # AI agents for analysis
│   │   ├── repo_agent.py           # Repository exploration agent
│   │   ├── code_quality_agent.py   # Code quality analysis agent
│   │   ├── celo_agent.py           # Celo integration detection agent
│   │   ├── reporting_agent.py      # Report generation agent
│   │   ├── orchestrator.py         # Parallel execution orchestration
│   │   └── coordinator.py          # Agent coordination system
│   ├── models/         # Data types and configuration
│   │   ├── types.py                # TypedDict definitions
│   │   └── config.py               # Configuration handling
│   ├── analyzer/       # Analysis components
│   │   ├── repo_analyzer.py        # Main analyzer class
│   │   ├── github_repo.py          # GitHub repository access
│   │   ├── code_quality.py         # Code quality analysis
│   │   └── celo_detector.py        # Celo integration detection
│   ├── tools/          # LangChain tools
│   │   ├── repo/                   # Repository analysis tools
│   │   ├── code_quality/           # Code quality tools
│   │   ├── celo/                   # Celo detection tools
│   │   └── reporting/              # Report generation tools
│   ├── utils/          # Utility functions
│   │   ├── spinner.py              # Progress indicator
│   │   └── timeout.py              # Timeout handling
│   ├── reporting/      # Report generation
│   │   └── report_generator.py     # Markdown report creation
│   └── main.py         # Main application logic
├── run.py              # Standard entry point script
├── run_agents.py       # Advanced agent-based entry point with parallel execution
├── config.json         # Configuration
└── requirements.txt    # Dependencies
```

## 🤖 AI Agent Architecture

The advanced version of this tool uses a specialized LangChain agent-based architecture:

### Agent Specialization

1. **Repository Agent** - Analyzes GitHub repositories to extract:
   - Repository metadata (stars, forks, etc.)
   - Directory structure
   - Representative code samples

2. **Code Quality Agent** - Evaluates code quality focusing on:
   - Readability and documentation
   - Coding standards and best practices
   - Algorithm complexity and efficiency
   - Testing and coverage

3. **Celo Integration Agent** - Detects Celo blockchain integration by:
   - Scanning for Celo-specific keywords
   - Analyzing smart contract integration
   - Evaluating overall Celo usage depth

4. **Reporting Agent** - Generates comprehensive reports with:
   - Project overviews and summaries
   - Detailed code quality assessments
   - Evidence of Celo integration

### Parallel Processing

The orchestration system manages the analysis workflow with:
- Parallel repository analysis
- Thread-safe progress reporting
- Automatic error recovery
- Optimized resource utilization

Run with multiple workers to analyze repositories simultaneously:
```bash
python run_agents.py --workers 4 --excel sample_projects.xlsx
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