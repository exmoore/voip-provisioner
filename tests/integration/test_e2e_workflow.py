"""End-to-end integration tests for complete workflows."""

import httpx
import pytest


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_phone_lifecycle(
        self, api_client: httpx.Client, test_phone_data: dict
    ):
        """Test complete phone lifecycle: create, read, update, delete."""
        mac = test_phone_data["mac"]

        # 1. Verify phone doesn't exist
        response = api_client.get(f"/api/v1/phones/{mac}")
        assert response.status_code == 404

        # 2. Create phone
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201
        phone = response.json()
        assert phone["extension"] == "201"

        # 3. Read phone
        response = api_client.get(f"/api/v1/phones/{mac}")
        assert response.status_code == 200
        phone = response.json()
        assert phone["mac"] == mac

        # 4. Preview config
        response = api_client.get(f"/api/v1/phones/{mac}/config")
        assert response.status_code == 200
        config = response.json()
        assert len(config["config"]) > 0

        # 5. Update phone
        update_data = {"extension": "202", "display_name": "Updated Phone"}
        response = api_client.put(f"/api/v1/phones/{mac}", json=update_data)
        assert response.status_code == 200
        phone = response.json()
        assert phone["extension"] == "202"

        # 6. Verify update
        response = api_client.get(f"/api/v1/phones/{mac}")
        assert response.status_code == 200
        phone = response.json()
        assert phone["extension"] == "202"
        assert phone["display_name"] == "Updated Phone"

        # 7. Delete phone
        response = api_client.delete(f"/api/v1/phones/{mac}")
        assert response.status_code == 204

        # 8. Verify deletion
        response = api_client.get(f"/api/v1/phones/{mac}")
        assert response.status_code == 404

    def test_phone_with_settings_override(
        self, api_client: httpx.Client, test_phone_data: dict, test_settings_data: dict
    ):
        """Test phone creation with global settings and overrides."""
        # 1. Set global settings
        response = api_client.put("/api/v1/settings", json=test_settings_data)
        assert response.status_code == 200

        # 2. Create phone with some overrides
        phone_data = {
            **test_phone_data,
            "mac": "112233445566",
            "extension": "301",
            "pbx_server": "custom.pbx.local",  # Override
            "pbx_port": None,  # Use global
        }

        response = api_client.post("/api/v1/phones", json=phone_data)
        assert response.status_code == 201
        phone = response.json()

        # 3. Verify effective settings
        assert phone["pbx_server"] == "custom.pbx.local"  # Overridden
        assert (
            phone["effective_settings"]["pbx_port"] == test_settings_data["pbx_port"]
        )  # From global

        # Cleanup
        api_client.delete(f"/api/v1/phones/{phone_data['mac']}")

    def test_provisioning_workflow(
        self, api_client: httpx.Client, test_phone_data: dict
    ):
        """Test complete provisioning workflow."""
        mac = test_phone_data["mac"]

        # 1. Create phone
        response = api_client.post("/api/v1/phones", json=test_phone_data)
        assert response.status_code == 201

        # 2. Phone requests its config
        response = api_client.get(f"/{mac}.cfg")
        assert response.status_code == 200
        config = response.text
        assert len(config) > 0
        assert test_phone_data["extension"] in config

        # 3. Phone requests phonebook
        response = api_client.get("/phonebook.xml")
        assert response.status_code == 200
        assert "<?xml" in response.text

        # Cleanup
        api_client.delete(f"/api/v1/phones/{mac}")

    def test_multi_tenant_scenario(
        self, api_client: httpx.Client, test_phone_data: dict
    ):
        """Test multiple phones with different configurations."""
        phones = [
            {
                **test_phone_data,
                "mac": "111111111111",
                "extension": "101",
                "label": "Office 1",
            },
            {
                **test_phone_data,
                "mac": "222222222222",
                "extension": "102",
                "label": "Office 2",
            },
            {
                **test_phone_data,
                "mac": "333333333333",
                "extension": "103",
                "label": "Office 3",
            },
        ]

        created_macs = []

        # Create all phones
        for phone_data in phones:
            response = api_client.post("/api/v1/phones", json=phone_data)
            assert response.status_code == 201
            created_macs.append(phone_data["mac"])

        # Verify all exist
        response = api_client.get("/api/v1/phones")
        assert response.status_code == 200
        all_phones = response.json()["phones"]
        assert len([p for p in all_phones if p["mac"] in created_macs]) == 3

        # Verify each can get its config
        for phone_data in phones:
            response = api_client.get(f"/{phone_data['mac']}.cfg")
            assert response.status_code == 200
            assert phone_data["extension"] in response.text

        # Cleanup
        for mac in created_macs:
            api_client.delete(f"/api/v1/phones/{mac}")

    def test_stats_and_health_endpoints(self, api_client: httpx.Client):
        """Test system stats and health endpoints."""
        # Health check
        response = api_client.get("/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"

        # Stats
        response = api_client.get("/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "phones_configured" in stats
        assert "phonebook_entries" in stats
        assert "vendors" in stats

    def test_reload_inventory(self, api_client: httpx.Client):
        """Test inventory reload endpoint."""
        response = api_client.get("/reload")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "reloaded"
        assert "phones" in data
        assert "phonebook_entries" in data
