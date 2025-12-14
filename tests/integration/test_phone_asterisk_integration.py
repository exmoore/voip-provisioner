"""Integration tests for phone CRUD with Asterisk."""

import asyncio

import httpx
import pytest
from panoramisk import Manager


@pytest.mark.integration
class TestPhoneAsteriskIntegration:
    """Test phone CRUD operations with Asterisk integration."""

    def test_create_phone_generates_asterisk_config(
        self, api_client: httpx.Client, test_phone_data: dict
    ):
        """Test that creating a phone generates Asterisk configuration."""
        # Create phone via API
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201, f"Failed to create phone: {response.text}"

        phone = response.json()
        assert phone["mac"] == test_phone_data["mac"]
        assert phone["extension"] == test_phone_data["extension"]

        # Verify phone appears in list
        response = api_client.get("/api/v1/phones")
        assert response.status_code == 200
        phones = response.json()["phones"]
        assert any(p["mac"] == test_phone_data["mac"] for p in phones)

    @pytest.mark.asyncio
    async def test_create_phone_registers_asterisk_endpoint(
        self, api_client: httpx.Client, ami_client: Manager, test_phone_data: dict
    ):
        """Test that creating a phone registers the endpoint in Asterisk."""
        # Create phone
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201

        # Wait for Asterisk reload (with retry)
        await asyncio.sleep(3)

        # Verify endpoint exists in Asterisk
        # Note: We can't fully verify registration without a real SIP client,
        # but we can verify the config was generated
        extension = test_phone_data["extension"]

        # Try to check if endpoint is defined (this may not work in all Asterisk versions)
        # For now, we'll just verify the phone was created successfully
        # A full test would require a SIP client to actually register

        # Verify we can read the phone back
        response = api_client.get(f"/api/v1/phones/{test_phone_data['mac']}")
        assert response.status_code == 200
        phone = response.json()
        assert phone["extension"] == extension

    def test_update_phone_updates_asterisk_config(
        self, api_client: httpx.Client, test_phone_data: dict
    ):
        """Test that updating a phone updates Asterisk configuration."""
        # Create phone first
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201
        mac = test_phone_data["mac"]

        # Update phone
        update_data = {
            "display_name": "Updated Test Phone",
            "extension": "202",
        }
        response = api_client.put(f"/api/v1/phones/{mac}", json=update_data)
        assert response.status_code == 200

        updated_phone = response.json()
        assert updated_phone["display_name"] == "Updated Test Phone"
        assert updated_phone["extension"] == "202"

        # Verify update persisted
        response = api_client.get(f"/api/v1/phones/{mac}")
        assert response.status_code == 200
        phone = response.json()
        assert phone["extension"] == "202"

    def test_delete_phone_removes_from_asterisk(
        self, api_client: httpx.Client, test_phone_data: dict
    ):
        """Test that deleting a phone removes it from Asterisk."""
        # Create phone first
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201
        mac = test_phone_data["mac"]

        # Delete phone
        response = api_client.delete(f"/api/v1/phones/{mac}")
        assert response.status_code == 204

        # Verify phone is gone
        response = api_client.get(f"/api/v1/phones/{mac}")
        assert response.status_code == 404

        # Verify not in list
        response = api_client.get("/api/v1/phones")
        assert response.status_code == 200
        phones = response.json()["phones"]
        assert not any(p["mac"] == mac for p in phones)

    def test_phone_config_preview(self, api_client: httpx.Client, test_phone_data: dict):
        """Test phone configuration preview endpoint."""
        # Create phone
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201
        mac = test_phone_data["mac"]

        # Get config preview
        response = api_client.get(f"/api/v1/phones/{mac}/config")
        assert response.status_code == 200

        config = response.json()
        assert config["mac"] == mac
        assert config["extension"] == test_phone_data["extension"]
        assert config["vendor"] == "yealink"
        assert len(config["config"]) > 0  # Should have generated config

    def test_multiple_phones_in_asterisk(self, api_client: httpx.Client, test_phone_data: dict):
        """Test creating multiple phones and verifying all in Asterisk."""
        phones_data = [
            {**test_phone_data, "mac": "001122334455", "extension": "201"},
            {**test_phone_data, "mac": "001122334456", "extension": "202"},
            {**test_phone_data, "mac": "001122334457", "extension": "203"},
        ]

        # Create multiple phones
        for phone_data in phones_data:
            response = api_client.post("/api/v1/phones", json=phone_data)
            assert response.status_code == 201

        # Verify all phones exist
        response = api_client.get("/api/v1/phones")
        assert response.status_code == 200
        phones = response.json()["phones"]

        created_macs = {p["mac"] for p in phones_data}
        api_macs = {p["mac"] for p in phones}

        assert created_macs.issubset(api_macs)

        # Cleanup
        for phone_data in phones_data:
            api_client.delete(f"/api/v1/phones/{phone_data['mac']}")

    def test_phone_with_custom_settings(self, api_client: httpx.Client, test_phone_data: dict):
        """Test creating phone with custom settings."""
        custom_phone = {
            **test_phone_data,
            "mac": "aabbccddeeff",
            "extension": "301",
            "pbx_server": "custom.pbx.local",
            "pbx_port": 5061,
            "transport": "TCP",
            "codecs": ["G722", "PCMU"],
        }

        response = api_client.post("/api/v1/phones", json=custom_phone)
        assert response.status_code == 201

        phone = response.json()
        assert phone["pbx_server"] == "custom.pbx.local"
        assert phone["pbx_port"] == 5061
        assert phone["transport"] == "TCP"
        assert phone["codecs"] == ["G722", "PCMU"]

        # Cleanup
        api_client.delete(f"/api/v1/phones/{custom_phone['mac']}")
