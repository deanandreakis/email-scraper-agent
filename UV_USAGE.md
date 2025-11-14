# UV Usage Guide

This project uses [UV](https://github.com/astral-sh/uv) for fast and reliable Python package management.

## Quick Reference

### Initial Setup

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup project
git clone <repo-url>
cd email-scraper-agent
uv sync

# Install Playwright browsers
uv run playwright install
```

### Common Commands

```bash
# Run the agent
uv run python main.py run --topic "your topic"

# Run examples
uv run python example.py

# Check configuration
uv run python main.py config

# Analyze a topic
uv run python main.py analyze --topic "technology companies"
```

### Dependency Management

```bash
# Add a new package
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a package
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Show installed packages
uv pip list
```

### Virtual Environment

```bash
# UV creates .venv automatically with `uv sync`

# To activate manually (usually not needed with `uv run`):
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

### Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check --fix .

# Type check
uv run mypy .
```

## Why UV?

- **10-100x faster** than pip
- **Automatic** virtual environment management
- **Better** dependency resolution
- **Compatible** with pip/requirements.txt
- **Built with Rust** for performance

## UV vs pip Comparison

| Task | UV | pip |
|------|-----|-----|
| Install deps | `uv sync` | `pip install -r requirements.txt` |
| Add package | `uv add package` | `pip install package && pip freeze > requirements.txt` |
| Run script | `uv run python script.py` | `source venv/bin/activate && python script.py` |
| Update deps | `uv sync --upgrade` | `pip install -U -r requirements.txt` |

## Tips

1. **Use `uv run`**: No need to activate venv first
2. **Fast reinstalls**: UV caches packages globally
3. **Lock file**: `uv.lock` ensures reproducible builds (gitignored by default)
4. **Compatible**: Can still use pip if needed inside the venv

## Troubleshooting

### UV not found after install

```bash
# Add UV to PATH (already done by installer usually)
export PATH="$HOME/.cargo/bin:$PATH"

# Or restart your terminal
```

### Sync fails

```bash
# Clear cache and retry
rm -rf .venv
uv sync
```

### Want to use pip instead?

```bash
# UV works alongside pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Learn More

- UV Documentation: https://github.com/astral-sh/uv
- Astral (makers of UV): https://astral.sh/
- Python Packaging: https://packaging.python.org/

## Project Files

- `pyproject.toml` - Project metadata, dependencies (UV reads this)
- `requirements.txt` - Fallback for pip users
- `.venv/` - Virtual environment (auto-created by UV)
- `uv.lock` - Lock file for reproducible builds (gitignored)
