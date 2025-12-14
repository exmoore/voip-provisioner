"""Integration tests for global settings operations."""

import httpx
import pytest


@pytest.mark.integration
class TestSettingsIntegration:
    """Test global settings operations."""

    def test_get_settings(self, api_client: httpx.Client):
        """Test retrieving global settings."""
        response = api_client.get("/api/v1/settings")
        assert response.status_code == 200

        settings = response.json()
        assert "pbx_server" in settings
        assert "pbx_port" in settings
        assert "transport" in settings
        assert "ntp_server" in settings
        assert "timezone" in settings
        assert "codecs" in settings
        assert isinstance(settings["codecs"], list)

    def test_update_settings(
        self, api_client: httpx.Client, test_settings_data: dict
    ):
        """Test updating global settings."""
        # Get original settings
        response = api_client.get("/api/v1/settings")
        original_settings = response.json()

        # Update settings
        response = api_client.put("/api/v1/settings", json=test_settings_data)
        assert response.status_code == 200

        updated_settings = response.json()
        assert updated_settings["pbx_server"] == test_settings_data["pbx_server"]
        assert updated_settings["pbx_port"] == test_settings_data["pbx_port"]
        assert updated_settings["transport"] == test_settings_data["transport"]

        # Restore original settings
        api_client.put("/api/v1/settings", json=original_settings)

    def test_settings_affect_new_phones(
        self, api_client: httpx.Client, test_settings_data: dict, test_phone_data: dict
    ):
        """Test that global settings affect newly created phones."""
        # Update global settings
        response = api_client.put("/api/v1/settings", json=test_settings_data)
        assert response.status_code == 200

        # Create phone without specific settings
        phone_data = {
            **test_phone_data,
            "mac": "ffeeddccbbaa",
            "extension": "401",
            "pbx_server": None,  # Should inherit from global
        }

        response = api_client.post("/api/v1/phones", json=phone_data)
        assert response.status_code == 201

        phone = response.json()
        # effective_settings should contain global settings
        assert phone["effective_settings"] is not None
        assert (
            phone["effective_settings"]["pbx_server"] == test_settings_data["pbx_server"]
        )

        # Cleanup
        api_client.delete(f"/api/v1/phones/{phone_data['mac']}")

    def test_settings_validation(self, api_client: httpx.Client):
        """Test settings validation."""
        # Invalid port
        invalid_settings = {
            "pbx_server": "pbx.test.local",
            "pbx_port": -1,  # Invalid
            "transport": "UDP",
            "ntp_server": "pool.ntp.org",
            "timezone": "America/New_York",
            "codecs": ["PCMU"],
        }

        response = api_client.put("/api/v1/settings", json=invalid_settings)
        assert response.status_code == 422  # Validation error

        # Invalid transport
        invalid_settings = {
            "pbx_server": "pbx.test.local",
            "pbx_port": 5060,
            "transport": "INVALID",  # Invalid
            "ntp_server": "pool.ntp.org",
            "timezone": "America/New_York",
            "codecs": ["PCMU"],
        }

        response = api_client.put("/api/v1/settings", json=invalid_settings)
        assert response.status_code == 422  # Validation error

    def test_settings_persistence(
        self, api_client: httpx.Client, test_settings_data: dict
    ):
        """Test that settings persist across requests."""
        # Update settings
        response = api_client.put("/api/v1/settings", json=test_settings_data)
        assert response.status_code == 200

        # Retrieve settings again
        response = api_client.get("/api/v1/settings")
        assert response.status_code == 200

        settings = response.json()
        assert settings["pbx_server"] == test_settings_data["pbx_server"]
        assert settings["pbx_port"] == test_settings_data["pbx_port"]

    def test_settings_codecs_array(self, api_client: httpx.Client):
        """Test that codecs are properly handled as an array."""
        test_codecs = ["G722", "PCMU", "PCMA", "G729"]

        settings_data = {
            "pbx_server": "pbx.test.local",
            "pbx_port": 5060,
            "transport": "UDP",
            "ntp_server": "pool.ntp.org",
            "timezone": "America/New_York",
            "codecs": test_codecs,
        }

        response = api_client.put("/api/v1/settings", json=settings_data)
        assert response.status_code == 200

        settings = response.json()
        assert settings["codecs"] == test_codecs
        assert isinstance(settings["codecs"], list)
