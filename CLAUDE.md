# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based HTTP provisioning server for VOIP phones. Generates MAC-based configuration files for Fanvil V64 and Yealink T23G phones from YAML inventory files, using Jinja2 templates.

## Common Commands

### Development Setup
```bash
# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### Running the Server
```bash
# Run server directly
python -m provisioner.server

# Or use entry point
voip-provisioner

# Run with Docker
docker-compose up -d
docker-compose logs -f
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_inventory.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=provisioner
```

### Linting
```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

## Architecture

### Core Components

**FastAPI Application** (`server.py`):
- Uses lifespan handler to load config and inventory on startup
- Creates global generator instances (Yealink, Fanvil) at startup
- Singleton pattern for config and inventory (via `get_config()`, `get_inventory()`)
- Endpoints support both auto-detection (`/{mac}.cfg`) and vendor-specific paths (`/yealink/{mac}.cfg`)
- Structured logging with JSON format for Loki integration

**Generator Pattern** (`generators/`):
- Abstract base class `BaseGenerator` defines interface for all vendors
- Each vendor subclass (YealinkGenerator, FanvilGenerator) implements `generate_config()` and `generate_phonebook()`
- Generators are initialized once at startup with templates directory
- Jinja2 environment configured per-generator with custom filters (e.g., `format_mac`)
- Templates loaded from vendor-specific subdirectories (e.g., `templates/yealink_t23g/`)

**Inventory System** (`inventory.py`):
- Pydantic models for type validation: `PhoneEntry`, `GlobalSettings`, `PhonebookEntry`
- MAC normalization happens at validation time via `@field_validator`
- Internal MAC index (`_mac_index`) built in `model_post_init` for O(1) lookups
- Settings inheritance: phone-specific settings override global defaults via `get_effective_settings()`
- Secrets file (`inventory/secrets.yml`) overrides passwords from main phones.yml

**Vendor Detection** (`utils.py`):
- Automatic vendor detection by MAC OUI prefix (first 6 hex characters)
- OUI mappings configured in `config.yml` under `vendor_oui`
- Fallback to model-based detection if OUI unknown
- MAC normalization strips all separators and lowercases (stored as 12 hex chars)

### Request Flow

1. Phone requests `/{mac}.cfg` or `/vendor/{mac}.cfg`
2. MAC normalized and looked up in inventory MAC index
3. Vendor detected from MAC OUI or model name
4. Settings merged: global defaults + phone-specific overrides
5. Generator renders Jinja2 template with merged settings
6. Configuration returned with vendor-specific content-type

### Configuration Loading

- Config loaded once at startup from `config.yml`
- Inventory loaded from `inventory/` directory (phones.yml, phonebook.yml, secrets.yml)
- `/reload` endpoint allows hot-reloading inventory without server restart
- All paths resolved relative to `config.base_dir` (working directory)

### Adding New Vendors

1. Create template directory: `templates/{vendor}_{model}/`
2. Add templates: `mac.cfg.j2`, `phonebook.xml.j2`
3. Create generator class in `src/provisioner/generators/`:
   - Inherit from `BaseGenerator`
   - Set `VENDOR`, `TEMPLATE_DIR` constants
   - Implement `generate_config()` and `generate_phonebook()`
4. Initialize generator in `server.py` lifespan handler
5. Add OUI prefixes to `config.yml` under `vendor_oui`

## Key Files

- `src/provisioner/server.py` - FastAPI application and endpoints
- `src/provisioner/inventory.py` - YAML inventory loader and Pydantic models
- `src/provisioner/generators/base.py` - Abstract generator interface
- `src/provisioner/utils.py` - MAC normalization and vendor detection
- `config.yml` - Server configuration and OUI mappings
- `inventory/phones.yml` - Phone definitions (MAC, extension, credentials)
- `inventory/phonebook.yml` - Shared directory entries
- `templates/{vendor}/` - Jinja2 templates per vendor

## Notes

- MAC addresses stored internally as 12 lowercase hex chars without separators
- Passwords should be in `inventory/secrets.yml` (gitignored), not `phones.yml`
- JSON logging enabled by default (`config.server.json_logs`) for Loki integration
- Template context always includes merged settings from `get_effective_settings()`
- Ruff configured for line length 100, Python 3.9+ compatibility
