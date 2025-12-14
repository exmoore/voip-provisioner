"""Pytest fixtures for integration tests."""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Generator

import httpx
import pytest
from panoramisk import Manager


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    """Return path to docker-compose test file."""
    return Path(__file__).parent / "docker" / "docker-compose.test.yml"


@pytest.fixture(scope="session")
def docker_services(docker_compose_file: Path) -> Generator[None, None, None]:
    """Start Docker services for testing."""
    # Use podman compose
    compose_cmd = ["podman", "compose"]

    # Start services
    subprocess.run(
        compose_cmd + ["-f", str(docker_compose_file), "up", "-d", "--build"],
        check=True,
        cwd=docker_compose_file.parent,
    )

    # Wait for services to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get("http://localhost:8080/health", timeout=2.0)
            if response.status_code == 200:
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            if i == max_retries - 1:
                raise
            time.sleep(2)

    yield

    # Cleanup: Stop and remove services
    subprocess.run(
        compose_cmd + ["-f", str(docker_compose_file), "down", "-v"],
        check=True,
        cwd=docker_compose_file.parent,
    )


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Return base URL for API."""
    return "http://localhost:8080"


@pytest.fixture
def api_client(docker_services: None, api_base_url: str) -> httpx.Client:
    """Create HTTP client for API testing."""
    return httpx.Client(base_url=api_base_url, timeout=10.0)


@pytest.fixture
async def ami_client(docker_services: None) -> Manager:
    """Create Asterisk AMI client."""
    manager = Manager(
        host="localhost",
        port=5038,
        username="admin",
        secret="testsecret",
        ping_delay=10,
    )
    await manager.connect()
    yield manager
    if manager.close and callable(manager.close):
        close_result = manager.close()
        if close_result is not None:
            await close_result


@pytest.fixture(autouse=True)
def cleanup_between_tests(api_client: httpx.Client):
    """Clean up test data between tests."""
    yield
    # Cleanup: Delete all phones and phonebook entries after each test
    try:
        # Delete all phones
        response = api_client.get("/api/v1/phones")
        if response.status_code == 200:
            phones = response.json().get("phones", [])
            for phone in phones:
                api_client.delete(f"/api/v1/phones/{phone['mac']}")

        # Delete all phonebook entries
        response = api_client.get("/api/v1/phonebook")
        if response.status_code == 200:
            entries = response.json().get("entries", [])
            for entry in entries:
                api_client.delete(f"/api/v1/phonebook/{entry['name']}")
    except Exception:
        # If cleanup fails, continue (tests may have already cleaned up)
        pass


@pytest.fixture
def test_phone_data() -> dict:
    """Return test phone data."""
    return {
        "mac": "001122334455",
        "model": "yealink_t23g",
        "extension": "201",
        "display_name": "Test Phone",
        "password": "testpass123",
        "pbx_server": None,
        "pbx_port": None,
        "transport": None,
        "label": "Integration Test",
        "codecs": None,
    }


@pytest.fixture
def test_phonebook_entry() -> dict:
    """Return test phonebook entry data."""
    return {
        "name": "Test Contact",
        "number": "555-1234",
    }


@pytest.fixture
def test_settings_data() -> dict:
    """Return test settings data."""
    return {
        "pbx_server": "pbx.test.local",
        "pbx_port": 5060,
        "transport": "UDP",
        "ntp_server": "pool.ntp.org",
        "timezone": "America/New_York",
        "codecs": ["PCMU", "PCMA", "G722"],
    }
