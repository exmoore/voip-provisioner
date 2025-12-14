"""FastAPI provisioning server application."""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import Config, get_config, load_config, set_config
from .generators import FanvilGenerator, YealinkGenerator
from .generators.base import BaseGenerator
from .inventory import get_inventory, load_inventory, set_inventory
from .utils import detect_vendor, normalize_mac

# Logger setup
logger = logging.getLogger("provisioner")


class JSONFormatter(logging.Formatter):
    """JSON log formatter for Loki/Promtail integration."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Add extra fields
        if hasattr(record, "mac"):
            log_data["mac"] = record.mac
        if hasattr(record, "vendor"):
            log_data["vendor"] = record.vendor
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip
        return json.dumps(log_data)


def setup_logging(config: Config) -> None:
    """Configure logging based on config."""
    level = getattr(logging, config.server.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if config.server.json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    logger.setLevel(level)
    logger.addHandler(handler)

    # Also set uvicorn loggers
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logging.getLogger(name).handlers = [handler]


# Generator instances (initialized on startup)
generators: dict[str, BaseGenerator] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - load config and inventory on startup."""
    # Load configuration
    config_path = Path.cwd() / "config.yml"
    config = load_config(config_path)
    set_config(config)

    # Setup logging
    setup_logging(config)

    # Load inventory
    inventory_dir = config.base_dir / config.paths.inventory_dir
    secrets_file = config.base_dir / config.paths.secrets_file
    inventory = load_inventory(inventory_dir, secrets_file if secrets_file.exists() else None)
    set_inventory(inventory)

    # Initialize generators
    templates_dir = config.base_dir / config.paths.templates_dir
    generators["yealink"] = YealinkGenerator(templates_dir)
    generators["fanvil"] = FanvilGenerator(templates_dir)

    logger.info(
        f"Provisioner started: {len(inventory.phones)} phones, "
        f"{len(inventory.phonebook)} phonebook entries"
    )

    yield

    logger.info("Provisioner shutting down")


# Create FastAPI app
app = FastAPI(
    title="VOIP Provisioning Server",
    description="Generates configuration files for Fanvil V64 and Yealink T23G phones",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API router for REST endpoints
from .api import api_router

app.include_router(api_router, prefix="/api/v1")

# Serve frontend static files if available
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/ui", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_dist}")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def log_provisioning(
    request: Request, mac: str, vendor: str | None, status: str, message: str = ""
) -> None:
    """Log a provisioning request."""
    extra = {
        "mac": mac,
        "vendor": vendor or "unknown",
        "status": status,
        "client_ip": get_client_ip(request),
    }
    if status == "success":
        logger.info(f"Provisioned {mac} ({vendor})", extra=extra)
    else:
        logger.warning(f"Provisioning failed for {mac}: {message}", extra=extra)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/stats")
async def stats() -> dict[str, Any]:
    """Return provisioning statistics."""
    inventory = get_inventory()
    return {
        "phones_configured": len(inventory.phones),
        "phonebook_entries": len(inventory.phonebook),
        "vendors": list(generators.keys()),
    }


@app.get("/{mac}.cfg")
async def provision_auto(mac: str, request: Request) -> Response:
    """Auto-detect vendor and return configuration.

    The phone vendor is detected from the MAC OUI prefix.
    """
    try:
        normalized_mac = normalize_mac(mac.replace(".cfg", ""))
    except ValueError as e:
        log_provisioning(request, mac, None, "error", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    config = get_config()
    inventory = get_inventory()

    # Look up phone
    phone = inventory.get_phone_by_mac(normalized_mac)
    if not phone:
        log_provisioning(request, normalized_mac, None, "not_found", "Phone not in inventory")
        raise HTTPException(status_code=404, detail="Phone not found in inventory")

    # Detect vendor from MAC or model
    oui_map = {
        "yealink": config.vendor_oui.yealink,
        "fanvil": config.vendor_oui.fanvil,
    }
    vendor = detect_vendor(normalized_mac, oui_map)

    # Fall back to model-based detection
    if not vendor:
        model_lower = phone.model.lower()
        if "yealink" in model_lower:
            vendor = "yealink"
        elif "fanvil" in model_lower:
            vendor = "fanvil"

    if not vendor or vendor not in generators:
        log_provisioning(request, normalized_mac, vendor, "error", "Unknown vendor")
        raise HTTPException(status_code=400, detail="Cannot determine phone vendor")

    # Generate config
    generator = generators[vendor]
    settings = inventory.get_effective_settings(phone)
    content = generator.generate_config(settings)

    log_provisioning(request, normalized_mac, vendor, "success")

    return PlainTextResponse(
        content=content,
        media_type=generator.config_content_type,
    )


@app.get("/yealink/{mac}.cfg")
async def provision_yealink(mac: str, request: Request) -> Response:
    """Return Yealink configuration for specific MAC."""
    return await _provision_vendor("yealink", mac, request)


@app.get("/fanvil/{mac}.cfg")
async def provision_fanvil(mac: str, request: Request) -> Response:
    """Return Fanvil configuration for specific MAC."""
    return await _provision_vendor("fanvil", mac, request)


async def _provision_vendor(vendor: str, mac: str, request: Request) -> Response:
    """Internal handler for vendor-specific provisioning."""
    try:
        normalized_mac = normalize_mac(mac.replace(".cfg", ""))
    except ValueError as e:
        log_provisioning(request, mac, vendor, "error", str(e))
        raise HTTPException(status_code=400, detail=str(e))

    inventory = get_inventory()

    # Look up phone
    phone = inventory.get_phone_by_mac(normalized_mac)
    if not phone:
        log_provisioning(request, normalized_mac, vendor, "not_found", "Phone not in inventory")
        raise HTTPException(status_code=404, detail="Phone not found in inventory")

    if vendor not in generators:
        log_provisioning(request, normalized_mac, vendor, "error", "Unknown vendor")
        raise HTTPException(status_code=400, detail=f"Unknown vendor: {vendor}")

    # Generate config
    generator = generators[vendor]
    settings = inventory.get_effective_settings(phone)
    content = generator.generate_config(settings)

    log_provisioning(request, normalized_mac, vendor, "success")

    return PlainTextResponse(
        content=content,
        media_type=generator.config_content_type,
    )


@app.get("/phonebook.xml")
async def phonebook_yealink() -> Response:
    """Return Yealink-format phonebook."""
    return await _phonebook("yealink")


@app.get("/fanvil/phonebook.xml")
async def phonebook_fanvil() -> Response:
    """Return Fanvil-format phonebook."""
    return await _phonebook("fanvil")


async def _phonebook(vendor: str) -> Response:
    """Internal handler for phonebook generation."""
    inventory = get_inventory()

    if vendor not in generators:
        raise HTTPException(status_code=400, detail=f"Unknown vendor: {vendor}")

    generator = generators[vendor]
    entries = [{"name": e.name, "number": e.number} for e in inventory.phonebook]
    content = generator.generate_phonebook(entries, inventory.phonebook_name)

    return Response(
        content=content,
        media_type=generator.phonebook_content_type,
    )


@app.get("/reload")
async def reload_inventory() -> dict[str, str]:
    """Reload inventory from disk (useful for config updates)."""
    config = get_config()
    inventory_dir = config.base_dir / config.paths.inventory_dir
    secrets_file = config.base_dir / config.paths.secrets_file

    inventory = load_inventory(inventory_dir, secrets_file if secrets_file.exists() else None)
    set_inventory(inventory)

    logger.info(f"Inventory reloaded: {len(inventory.phones)} phones")

    return {
        "status": "reloaded",
        "phones": str(len(inventory.phones)),
        "phonebook_entries": str(len(inventory.phonebook)),
    }


def main() -> None:
    """Entry point for running the server."""
    # Load config for server settings
    config_path = Path.cwd() / "config.yml"
    config = load_config(config_path)

    uvicorn.run(
        "provisioner.server:app",
        host=config.server.host,
        port=config.server.port,
        log_level=config.server.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()
