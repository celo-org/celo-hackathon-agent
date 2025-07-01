# 🔄 Migration Guide: Monorepo Restructuring

> **Guide for migrating from the old fragmented structure to the new monorepo**

This guide helps developers transition from the old project structure to the new cleaned-up monorepo.

## 📋 **What Changed**

### **Before (Old Structure)**

```
ai-project-analyzer/
├── src/                    # ❌ Scattered CLI code
├── api/                    # ❌ Duplicate API code
├── apps/frontend/          # ❌ Nested frontend
├── prompts/                # ❌ Root-level prompts
├── api.py                  # ❌ Root-level entry points
├── worker.py               # ❌ Root-level workers
└── main.py                 # ❌ Root-level main
```

### **After (New Structure)**

```
ai-project-analyzer/
├── packages/
│   ├── core/src/           # ✅ Business logic
│   ├── cli/src/            # ✅ CLI tools
│   ├── api/app/            # ✅ API server
│   └── frontend/src/       # ✅ React app
├── config/prompts/         # ✅ Shared config
├── .vscode/                # ✅ IDE settings
└── scripts/                # ✅ Build scripts
```

## 🚀 **Migration Steps**

### **Step 1: Update Development Environment**

```bash
# 1. Pull latest changes
git pull origin main

# 2. Clean old dependencies
rm -rf .venv node_modules

# 3. Install new monorepo dependencies
uv sync --dev
cd packages/frontend && npm install
```

### **Step 2: Update Import Statements**

**Old imports (❌ Broken):**

```python
from src.analyzer import analyze_single_repository
from src.config import get_gemini_api_key
from api.services import AnalysisService
```

**New imports (✅ Working):**

```python
# In CLI package
from core.src.analyzer import analyze_single_repository
from core.src.config import get_gemini_api_key

# In API package
from app.services.analysis import AnalysisService

# In Core package (relative imports)
from .config import get_gemini_api_key
from .metrics import fetch_github_metrics
```

### **Step 3: Update Entry Points**

**Old CLI usage (❌ Broken):**

```bash
python main.py --github-urls https://github.com/user/repo
python src/cli.py analyze
```

**New CLI usage (✅ Working):**

```bash
uv run python packages/cli/src/main.py analyze https://github.com/user/repo
cd packages/cli && python src/main.py analyze https://github.com/user/repo
```

**Old API usage (❌ Broken):**

```bash
python api.py
python worker.py
```

**New API usage (✅ Working):**

```bash
cd packages/api && uvicorn app.main:app --reload
cd packages/api && python -m app.worker
```

### **Step 4: Update Configuration Paths**

**Old config paths (❌ Broken):**

```python
prompt_path = "prompts/default.txt"
config_file = ".env"
```

**New config paths (✅ Working):**

```python
# From packages/ subdirectory
prompt_path = "../../config/prompts/default.txt"
config_file = "../../.env"

# From project root
prompt_path = "config/prompts/default.txt"
config_file = ".env"
```

### **Step 5: Update VS Code Settings**

**New workspace features:**

- ✅ **Python path** automatically configured for all packages
- ✅ **Debug configurations** for CLI, API, tests, worker
- ✅ **Task runners** for common operations (Ctrl+Shift+P → "Tasks: Run Task")
- ✅ **Recommended extensions** auto-installed
- ✅ **Integrated testing** with proper Python paths

**Just reopen VS Code in the project root!**

## 🛠️ **Development Workflow Changes**

### **Testing Commands**

**Old (❌):**

```bash
pytest src/
pytest api/tests/
cd apps/frontend && npm test
```

**New (✅):**

```bash
# Test all packages
pytest packages/ -v

# Test specific package
pytest packages/core/ -v
pytest packages/api/ -v

# Frontend testing
cd packages/frontend && npm test
```

### **Linting & Formatting**

**Old (❌):**

```bash
ruff check src/
ruff format src/
ruff check api/
```

**New (✅):**

```bash
# Lint all Python packages
ruff check packages/

# Format all Python packages
ruff format packages/

# Or use VS Code tasks (Ctrl+Shift+P → "Tasks: Run Task")
```

### **Docker Development**

**Old (❌):**

```bash
docker-compose up  # Would start incomplete services
```

**New (✅):**

```bash
# Start full development stack
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis
```

## 📦 **Package Management Changes**

### **Dependency Installation**

**Old (❌):**

```bash
pip install -r requirements.txt
pip install -e .
cd api && pip install -r requirements.txt
```

**New (✅):**

```bash
# One command for all Python packages
uv sync --dev

# Frontend dependencies
cd packages/frontend && npm install
```

### **Package Dependencies**

**Before:** Packages had no formal dependencies between them

**After:** Proper dependency chain:

- `cli` → depends on → `core`
- `api` → depends on → `core`
- `frontend` → standalone React app

## 🧪 **Testing Changes**

### **Test Discovery**

**Old test locations (❌):**

```
src/tests/
api/tests/
apps/frontend/src/__tests__/
```

**New test locations (✅):**

```
packages/core/tests/
packages/cli/tests/
packages/api/tests/
packages/frontend/src/__tests__/
```

### **Test Running**

**Old (❌):**

```bash
cd src && python -m pytest
cd api && python -m pytest tests/
```

**New (✅):**

```bash
# From project root - runs all tests
pytest packages/ -v

# Package-specific tests
pytest packages/core/tests/ -v
pytest packages/api/tests/ -v
```

## 🔧 **Build & Deployment Changes**

### **Build Commands**

**Old (❌):**

```bash
# No standardized build process
python setup.py build
cd apps/frontend && npm run build
```

**New (✅):**

```bash
# Use workspace scripts
./scripts/build.sh

# Or package-specific builds
cd packages/frontend && npm run build
docker-compose build
```

### **Environment Configuration**

**Old (❌):**

```bash
# Multiple .env files
api/.env
apps/frontend/.env
.env
```

**New (✅):**

```bash
# Single workspace .env file
.env

# With templates for different environments
config/env.development
config/env.production
config/env.template
```

## 🚨 **Common Migration Issues**

### **1. Import Errors**

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**

```python
# Change from
from src.analyzer import analyze_single_repository

# To (in CLI/API packages)
from core.src.analyzer import analyze_single_repository

# Or (in Core package)
from .analyzer import analyze_single_repository
```

### **2. Path Resolution Issues**

**Problem:** `FileNotFoundError: prompts/default.txt`

**Solution:**

```python
# Use absolute paths from project root
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prompt_path = os.path.join(project_root, "config", "prompts", "default.txt")
```

### **3. VS Code Python Path Issues**

**Problem:** IntelliSense not working for package imports

**Solution:**

1. Reopen VS Code in project root
2. Install recommended extensions (F1 → "Extensions: Show Recommended Extensions")
3. Select correct Python interpreter (F1 → "Python: Select Interpreter" → `.venv/bin/python`)

### **4. Docker Build Failures**

**Problem:** `COPY src/ ./src/` fails in Dockerfile

**Solution:** Update Dockerfiles to use new package structure:

```dockerfile
# Old
COPY src/ ./src/

# New
COPY packages/api/ ./
```

## 📞 **Need Help?**

### **Quick Fixes**

```bash
# Reset everything and start fresh
git clean -fd
rm -rf .venv node_modules
uv sync --dev
cd packages/frontend && npm install

# Verify setup
pytest packages/core/tests/test_config.py -v
cd packages/cli && python src/main.py --help
```

### **Verification Checklist**

- [ ] ✅ `uv sync --dev` completes without errors
- [ ] ✅ `pytest packages/ -v` runs successfully
- [ ] ✅ `ruff check packages/` shows minimal/expected errors
- [ ] ✅ CLI works: `cd packages/cli && python src/main.py --help`
- [ ] ✅ API starts: `cd packages/api && uvicorn app.main:app --reload`
- [ ] ✅ Frontend builds: `cd packages/frontend && npm run build`
- [ ] ✅ VS Code IntelliSense works for all packages

### **Get Support**

If you encounter issues:

1. **Check the troubleshooting section** in the main README
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Your migration step
   - Error messages
   - Environment details (OS, Python version, Node version)

---

**Happy coding with the new monorepo structure! 🎉**
