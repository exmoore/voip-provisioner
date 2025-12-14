# VOIP Phone Provisioning Server

A comprehensive Python-based VOIP provisioning system with automatic Asterisk integration and modern web UI. Supports Fanvil V64 and Yealink T23G phones with automatic configuration generation, Asterisk endpoint management, and intuitive web interface.

## Features

### 🚀 Core Provisioning
- **MAC-based provisioning**: Phones automatically fetch configurations by MAC address
- **Multi-vendor support**: Fanvil V64 and Yealink T23G with extensible architecture
- **Auto-detection**: Identifies vendor by MAC OUI prefix
- **Jinja2 templates**: Clean separation of configuration format from business logic
- **Shared phonebook**: XML directory synchronized across all phones

### 🔧 REST API
- **Full CRUD operations**: Manage phones, phonebook entries, and global settings via REST API
- **Atomic YAML persistence**: Safe concurrent writes with automatic backups
- **Input validation**: Pydantic schemas ensure data integrity
- **OpenAPI documentation**: Interactive API docs at `/docs`
- **Config preview**: Preview generated configurations before deployment

### 🔄 Asterisk Integration
- **Automatic config generation**: Creates `pjsip.conf` and `extensions.conf` from inventory
- **AMI-based reload**: Automatically reloads Asterisk after configuration changes
- **Endpoint management**: Creates PJSIP endpoints, authentication, and AORs
- **Dialplan generation**: Generates extension entries for all phones
- **Error handling**: Configurable retry logic and rollback on failures

### 🎨 Web Interface
- **Modern React UI**: Intuitive interface for managing all aspects of provisioning
- **Phone management**: Create, edit, delete phones with form validation
- **Phonebook editor**: Manage shared directory entries
- **Settings dashboard**: Configure global defaults with live preview
- **Real-time updates**: React Query provides optimistic updates and automatic refetching

### 🧪 Testing & CI/CD
- **Integration tests**: 26 comprehensive tests with real Asterisk in Docker
- **Unit tests**: Full coverage of core business logic
- **GitHub Actions**: Automated testing on every commit
- **Docker-based tests**: Verify complete workflows in isolated containers

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/brcs/voip-provisioner.git
cd voip-provisioner

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with all dependencies
pip install -e ".[dev]"

# Run the server
python -m provisioner.server
```

The server will start on `http://localhost:8080`

### Docker Deployment

```bash
# Build and run
docker build -t voip-provisioner .
docker run -p 8080:8080 -v $(pwd)/inventory:/app/inventory voip-provisioner

# With Docker Compose
docker-compose up -d
```

## Configuration

### Basic Configuration (`config.yml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  log_level: "info"
  json_logs: true  # For Loki/Promtail integration

paths:
  inventory_dir: "inventory"
  templates_dir: "templates"
  secrets_file: "inventory/secrets.yml"

vendor_oui:
  yealink:
    - "001565"
    - "805E0C"
    - "805EC0"
  fanvil:
    - "0C383E"

# Optional: Asterisk Integration
asterisk:
  enabled: false  # Set to true to enable
  host: "asterisk.example.com"
  port: 5038
  username: "admin"
  password: "secret"
  pjsip_config_path: "/etc/asterisk/pjsip.conf"
  extensions_config_path: "/etc/asterisk/extensions.conf"
  context: "from-internal"
  transport: "transport-udp"
  fail_on_ami_error: false
  retry_on_failure: true
  retry_max_attempts: 3
  retry_delay_seconds: 5
```

### Inventory Configuration

#### `inventory/phones.yml`

```yaml
global:
  pbx_server: "pbx.example.com"
  pbx_port: 5060
  transport: "UDP"
  ntp_server: "pool.ntp.org"
  timezone: "America/New_York"
  codecs:
    - "PCMU"
    - "PCMA"
    - "G722"

phones:
  - mac: "001565123456"
    model: "yealink_t23g"
    extension: "101"
    display_name: "Front Office"
    label: "Reception"

  - mac: "0c383eaabbcc"
    model: "fanvil_v64"
    extension: "102"
    display_name: "Main Office"
    pbx_server: "backup.pbx.local"  # Override global
```

#### `inventory/secrets.yml` (gitignored)

```yaml
phone_passwords:
  "101": "secure_password_101"
  "102": "secure_password_102"
```

#### `inventory/phonebook.yml`

```yaml
phonebook_name: "Company Directory"
phonebook:
  - name: "Front Office"
    number: "101"
  - name: "Main Office"
    number: "102"
  - name: "Voicemail"
    number: "*97"
```

## Architecture

### System Overview

```
┌─────────────────┐      REST API        ┌──────────────────┐
│   React Web UI  │◄────────────────────►│  FastAPI Server  │
│   (Frontend)    │      HTTP/JSON       │   (Backend)      │
└─────────────────┘                      └────────┬─────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────┐
                    │                             │                     │
                    ▼                             ▼                     ▼
            ┌───────────────┐           ┌─────────────────┐   ┌─────────────┐
            │ YAML Storage  │           │ Config Generator│   │ AMI Client  │
            │  (Inventory)  │           │   (Jinja2)      │   │ (Asterisk)  │
            └───────────────┘           └─────────────────┘   └──────┬──────┘
                    │                             │                   │
                    │                             │                   │
                    └─────────────┬───────────────┘                   │
                                  │                                   │
                                  ▼                                   ▼
                         ┌──────────────────┐              ┌──────────────────┐
                         │  VOIP Phones     │              │    Asterisk      │
                         │ (Yealink/Fanvil) │◄────SIP─────►│   PBX Server     │
                         └──────────────────┘              └──────────────────┘
```

### Project Structure

```
voip-provisioner/
├── frontend/                     # React web interface
│   ├── src/
│   │   ├── api/                 # API client and TypeScript types
│   │   ├── components/          # React components
│   │   ├── hooks/               # React Query hooks
│   │   └── pages/               # Page components
│   ├── package.json
│   └── vite.config.ts
├── src/provisioner/
│   ├── server.py                # FastAPI application
│   ├── config.py                # Configuration loader
│   ├── inventory.py             # Inventory management
│   ├── api/                     # REST API endpoints
│   │   ├── routes/
│   │   │   ├── phones.py       # Phone CRUD
│   │   │   ├── phonebook.py    # Phonebook CRUD
│   │   │   └── settings.py     # Settings management
│   │   └── schemas.py           # Pydantic models
│   ├── asterisk/                # Asterisk integration
│   │   ├── ami_client.py       # AMI communication
│   │   └── config_generator.py # Config file generation
│   ├── persistence/             # YAML persistence layer
│   │   ├── yaml_repository.py  # Atomic YAML operations
│   │   └── backup.py            # Backup management
│   ├── generators/              # Vendor-specific generators
│   │   ├── base.py
│   │   ├── yealink.py
│   │   └── fanvil.py
│   └── utils.py                 # Utilities
├── templates/
│   ├── yealink_t23g/           # Yealink templates
│   ├── fanvil_v64/             # Fanvil templates
│   └── asterisk/               # Asterisk config templates
├── inventory/
│   ├── phones.yml              # Phone definitions
│   ├── phonebook.yml           # Directory entries
│   └── secrets.yml             # Passwords (gitignored)
├── tests/
│   ├── integration/            # Integration tests
│   │   ├── docker/            # Docker test environment
│   │   └── test_*.py          # Test files
│   └── unit/                   # Unit tests
├── config.yml                  # Server configuration
└── pyproject.toml              # Python package configuration
```

## API Documentation

### Provisioning Endpoints (Legacy)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{mac}.cfg` | Auto-detect vendor, return config |
| GET | `/yealink/{mac}.cfg` | Yealink-specific config |
| GET | `/fanvil/{mac}.cfg` | Fanvil-specific config |
| GET | `/phonebook.xml` | Yealink XML phonebook |
| GET | `/fanvil/phonebook.xml` | Fanvil XML phonebook |

### REST API v1 (`/api/v1`)

#### Phone Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/phones` | List all phones |
| POST | `/api/v1/phones` | Create a phone |
| GET | `/api/v1/phones/{mac}` | Get phone by MAC |
| PUT | `/api/v1/phones/{mac}` | Update phone |
| DELETE | `/api/v1/phones/{mac}` | Delete phone |
| GET | `/api/v1/phones/{mac}/config` | Preview generated config |

#### Phonebook Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/phonebook` | List all entries |
| POST | `/api/v1/phonebook` | Create entry |
| PUT | `/api/v1/phonebook/{id}` | Update entry |
| DELETE | `/api/v1/phonebook/{id}` | Delete entry |

#### Settings Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/settings` | Get global settings |
| PUT | `/api/v1/settings` | Update global settings |

#### System Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/stats` | System statistics |
| GET | `/reload` | Reload inventory from disk |
| GET | `/docs` | OpenAPI documentation |

### API Examples

#### Create a Phone

```bash
curl -X POST http://localhost:8080/api/v1/phones \
  -H "Content-Type: application/json" \
  -d '{
    "mac": "001122334455",
    "model": "yealink_t23g",
    "extension": "201",
    "display_name": "Conference Room",
    "password": "secure123",
    "label": "Building A"
  }'
```

#### Update Global Settings

```bash
curl -X PUT http://localhost:8080/api/v1/settings \
  -H "Content-Type: application/json" \
  -d '{
    "pbx_server": "pbx.example.com",
    "pbx_port": 5060,
    "transport": "UDP",
    "ntp_server": "pool.ntp.org",
    "timezone": "America/New_York",
    "codecs": ["PCMU", "PCMA", "G722"]
  }'
```

#### List All Phones

```bash
curl http://localhost:8080/api/v1/phones
```

## Web Interface

Access the web interface at `http://localhost:8080/ui` (after building the frontend).

### Building the Frontend

```bash
cd frontend
npm install
npm run build
```

The built files will be served automatically by the backend at `/ui`.

### Development Mode

```bash
# Terminal 1: Start backend
python -m provisioner.server

# Terminal 2: Start frontend dev server
cd frontend
npm run dev
```

Frontend dev server runs on `http://localhost:5173` with API proxy to backend.

## Asterisk Integration

### Setup

1. **Enable Asterisk Integration** in `config.yml`:
   ```yaml
   asterisk:
     enabled: true
     host: "asterisk.example.com"
     port: 5038
     username: "admin"
     password: "your-ami-password"
   ```

2. **Configure AMI** in Asterisk's `manager.conf`:
   ```ini
   [general]
   enabled = yes
   port = 5038
   bindaddr = 0.0.0.0

   [admin]
   secret = your-ami-password
   read = all
   write = all
   ```

3. **Shared Configuration Directory** (if using Docker):
   ```yaml
   # docker-compose.yml
   volumes:
     - asterisk-configs:/etc/asterisk
   ```

### How It Works

1. **Phone Created/Updated** → REST API endpoint called
2. **YAML Updated** → Phone added to `inventory/phones.yml`
3. **Asterisk Config Generated** → `pjsip.conf` and `extensions.conf` created
4. **AMI Reload Triggered** → Asterisk reloads configuration
5. **Phone Registers** → Endpoint active and ready for calls

### Generated Asterisk Configuration

#### PJSIP Endpoint (pjsip.conf)
```ini
[201]
type=endpoint
context=from-internal
disallow=all
allow=PCMU,PCMA,G722
auth=201
aors=201
transport=transport-udp
callerid="Conference Room" <201>
direct_media=no

[201]
type=auth
auth_type=userpass
username=201
password=secure123

[201]
type=aor
max_contacts=1
remove_existing=yes
```

#### Dialplan Entry (extensions.conf)
```ini
; Conference Room - Extension 201
exten => 201,1,Dial(PJSIP/201,30)
 same => n,Hangup()
```

## Testing

### Unit Tests

```bash
# Run all unit tests
pytest tests/ -v -m "not integration"

# With coverage
pytest tests/ -v --cov=provisioner --cov-report=html
```

### Integration Tests

Integration tests require Docker or Podman:

```bash
# Run all integration tests
pytest tests/integration/ -v -m integration

# Run specific test file
pytest tests/integration/test_phone_asterisk_integration.py -v

# Manual Docker setup
cd tests/integration/docker
docker-compose -f docker-compose.test.yml up -d --build
pytest ../../integration/ -v
docker-compose -f docker-compose.test.yml down -v
```

**Test Coverage:**
- 8 Phone + Asterisk integration tests
- 7 Phonebook operation tests
- 6 Settings management tests
- 6 End-to-end workflow tests

## Development

### Running in Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with auto-reload
uvicorn provisioner.server:app --reload --host 0.0.0.0 --port 8080
```

### Code Quality

```bash
# Lint with ruff
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Adding a New Vendor

1. **Create template directory**: `templates/vendor_model/`
2. **Add Jinja2 templates**: `mac.cfg.j2`, `phonebook.xml.j2`
3. **Create generator class**:
   ```python
   from .base import BaseGenerator

   class VendorGenerator(BaseGenerator):
       VENDOR = "vendor"
       TEMPLATE_DIR = "vendor_model"
       # Implement generate_config() and generate_phonebook()
   ```
4. **Register in server.py**: Add to `generators` dict in lifespan
5. **Add OUI prefixes**: Update `config.yml` vendor_oui section

## Deployment

### Production Checklist

- [ ] Set strong passwords in `inventory/secrets.yml`
- [ ] Configure `json_logs: true` for centralized logging
- [ ] Set up reverse proxy (nginx/Apache) for SSL/TLS
- [ ] Configure firewall rules (allow port 8080)
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure log aggregation (Loki, ELK stack)
- [ ] Set up automated backups for `inventory/` directory
- [ ] Test Asterisk AMI connectivity
- [ ] Configure DHCP Option 66 or DNS SRV records
- [ ] Test phone provisioning end-to-end

### Environment Variables

```bash
export ASTERISK_ENABLED=true
export ASTERISK_HOST=asterisk.example.com
export ASTERISK_USERNAME=admin
export ASTERISK_PASSWORD=secret
```

### Systemd Service

```ini
[Unit]
Description=VOIP Provisioning Server
After=network.target

[Service]
Type=simple
User=provisioner
WorkingDirectory=/opt/voip-provisioner
Environment="PATH=/opt/voip-provisioner/.venv/bin"
ExecStart=/opt/voip-provisioner/.venv/bin/python -m provisioner.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name provisioner.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Structured Logging

All provisioning requests are logged in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Provisioned 001565123456 (yealink)",
  "mac": "001565123456",
  "vendor": "yealink",
  "status": "success",
  "client_ip": "192.168.1.100"
}
```

### Health Check

```bash
curl http://localhost:8080/health
# {"status": "healthy"}
```

### Statistics

```bash
curl http://localhost:8080/stats
# {
#   "phones_configured": 10,
#   "phonebook_entries": 25,
#   "vendors": ["yealink", "fanvil"]
# }
```

## MAC Address Formats

The server accepts MAC addresses in various formats:
- `001565123456` (no separators) - **recommended**
- `00:15:65:12:34:56` (colons)
- `00-15-65-12-34-56` (dashes)
- `0015.6512.3456` (dots)

All formats are normalized internally to 12 lowercase hex characters.

## Vendor Detection

Automatic vendor detection uses MAC OUI prefixes:

| Vendor | OUI Prefixes | Example MAC |
|--------|--------------|-------------|
| Yealink | 00:15:65, 80:5E:0C, 80:5E:C0 | 001565123456 |
| Fanvil | 0C:38:3E | 0c383eaabbcc |

Fallback detection uses model name if OUI is unknown.

## Troubleshooting

### Phone Not Provisioning

1. **Check phone can reach server**: `ping provisioner.example.com`
2. **Verify DHCP Option 66**: Check phone's network settings
3. **Check server logs**: Look for provisioning requests
4. **Verify MAC in inventory**: `curl http://localhost:8080/api/v1/phones`
5. **Test config generation**: `curl http://localhost:8080/{mac}.cfg`

### Asterisk Not Reloading

1. **Check AMI connectivity**: `telnet asterisk.example.com 5038`
2. **Verify AMI credentials**: Check `manager.conf`
3. **Check server logs**: Look for AMI errors
4. **Test config files**: Verify `pjsip.conf` and `extensions.conf` were generated
5. **Manual reload**: `asterisk -rx "pjsip reload"`

### Web UI Not Loading

1. **Build frontend**: `cd frontend && npm run build`
2. **Check frontend dist**: Verify `frontend/dist/` exists
3. **Check server logs**: Look for static file serving errors
4. **Development mode**: Use `npm run dev` for frontend dev server

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide (enforced by ruff)
- Add tests for new features
- Update documentation
- Ensure all tests pass: `pytest -v`
- Run linter: `ruff check .`

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- Asterisk AMI client: [Panoramisk](https://github.com/gawel/panoramisk)
- Template engine: [Jinja2](https://jinja.palletsprojects.com/)

## Support

- **Documentation**: See `CLAUDE.md` for developer guidance
- **Issues**: https://github.com/brcs/voip-provisioner/issues
- **Integration Tests**: See `tests/integration/README.md`
