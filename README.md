# VOIP Phone Provisioning Server

A lightweight Python-based HTTP provisioning server for VOIP phones. Generates configuration files for Fanvil V64 and Yealink T23G phones from YAML inventory files.

## Features

- **MAC-based provisioning**: Phones request config by MAC address
- **Multi-vendor support**: Fanvil V64 and Yealink T23G
- **YAML inventory**: Ansible-friendly phone definitions
- **Jinja2 templates**: Clean separation of config format from logic
- **Shared phonebook**: XML directory for all phones
- **Auto-detection**: Identifies vendor by MAC OUI prefix

## Quick Start

### Installation

```bash
# Clone or copy the project
cd voip-provisioner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m provisioner.server
```

### Configuration

1. Edit `config.yml` to set server port and paths
2. Define phones in `inventory/phones.yml`
3. Define phonebook in `inventory/phonebook.yml`
4. (Optional) Store secrets in `inventory/secrets.yml`

### DHCP Setup

Configure DHCP Option 66 on your DHCP server:
```
option tftp-server-name "http://provisioner.example.com:8080/";
```

Or use DNS SRV records for automatic discovery.

## Project Structure

```
voip-provisioner/
├── config.yml                    # Server configuration
├── inventory/
│   ├── phones.yml               # Phone definitions (MAC, extension, etc.)
│   ├── phonebook.yml            # Directory entries
│   └── secrets.yml              # Passwords (gitignored)
├── templates/
│   ├── yealink_t23g/
│   │   └── mac.cfg.j2           # Yealink config template
│   ├── fanvil_v64/
│   │   └── mac.cfg.j2           # Fanvil config template
│   └── phonebook.xml.j2         # Shared phonebook template
└── src/provisioner/
    ├── server.py                # FastAPI application
    ├── config.py                # Configuration loader
    ├── inventory.py             # YAML inventory loader
    └── generators/              # Vendor-specific generators
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{mac}.cfg` | Auto-detect vendor, return config |
| GET | `/yealink/{mac}.cfg` | Yealink-specific config |
| GET | `/fanvil/{mac}.cfg` | Fanvil-specific config |
| GET | `/phonebook.xml` | Yealink XML phonebook |
| GET | `/fanvil/phonebook.xml` | Fanvil XML phonebook |
| GET | `/health` | Health check endpoint |
| GET | `/docs` | OpenAPI documentation |

## Inventory Format

### phones.yml

```yaml
global:
  pbx_server: "pbx.example.com"
  pbx_port: 5060
  ntp_server: "pool.ntp.org"
  timezone: "America/New_York"

phones:
  - mac: "001565123456"
    model: "yealink_t23g"
    extension: "101"
    display_name: "Front Office"
    password: "secret123"
```

### phonebook.yml

```yaml
phonebook:
  - name: "Front Office"
    number: "101"
  - name: "Main Office"
    number: "102"
```

## MAC Address Formats

The server accepts MAC addresses in various formats:
- `001565123456` (no separators)
- `00:15:65:12:34:56` (colons)
- `00-15-65-12-34-56` (dashes)
- `0015.6512.3456` (dots)

## Vendor Detection

Automatic vendor detection uses MAC OUI prefixes:

| Vendor | OUI Prefixes |
|--------|--------------|
| Yealink | 00:15:65, 80:5E:0C, 80:5E:C0 |
| Fanvil | 0C:38:3E |

## Docker Deployment

```bash
docker build -t voip-provisioner .
docker run -p 8080:8080 -v $(pwd)/inventory:/app/inventory voip-provisioner
```

## Integration with Asterisk

The provisioning server provides SIP credentials that phones use to register with Asterisk. Ensure your Asterisk `pjsip.conf` or `sip.conf` has matching credentials for each extension.

## Monitoring

The server logs all provisioning requests in JSON format, compatible with Loki/Promtail:

```json
{"timestamp": "2024-01-15T10:30:00Z", "mac": "001565123456", "vendor": "yealink", "status": "success"}
```

## License

MIT License
