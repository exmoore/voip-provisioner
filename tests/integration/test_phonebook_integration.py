"""Integration tests for phonebook operations."""

import httpx
import pytest


@pytest.mark.integration
class TestPhonebookIntegration:
    """Test phonebook CRUD operations."""

    def test_list_phonebook_entries(self, api_client: httpx.Client):
        """Test listing phonebook entries."""
        response = api_client.get("/api/v1/phonebook")
        assert response.status_code == 200

        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert "phonebook_name" in data
        assert isinstance(data["entries"], list)

    def test_create_phonebook_entry(self, api_client: httpx.Client, test_phonebook_entry: dict):
        """Test creating a phonebook entry."""
        # Get initial count
        response = api_client.get("/api/v1/phonebook")
        initial_count = response.json()["total"]

        # Create entry
        response = api_client.post("/api/v1/phonebook", json=test_phonebook_entry)
        assert response.status_code == 201

        entry = response.json()
        assert entry["name"] == test_phonebook_entry["name"]
        assert entry["number"] == test_phonebook_entry["number"]
        assert "id" in entry

        # Verify count increased
        response = api_client.get("/api/v1/phonebook")
        assert response.json()["total"] == initial_count + 1

        # Cleanup
        api_client.delete(f"/api/v1/phonebook/{entry['id']}")

    def test_update_phonebook_entry(self, api_client: httpx.Client, test_phonebook_entry: dict):
        """Test updating a phonebook entry."""
        # Create entry first
        response = api_client.post("/api/v1/phonebook", json=test_phonebook_entry)
        assert response.status_code == 201
        entry_id = response.json()["id"]

        # Update entry
        update_data = {
            "name": "Updated Contact",
            "number": "555-5678",
        }
        response = api_client.put(f"/api/v1/phonebook/{entry_id}", json=update_data)
        assert response.status_code == 200

        updated_entry = response.json()
        assert updated_entry["name"] == "Updated Contact"
        assert updated_entry["number"] == "555-5678"

        # Cleanup
        api_client.delete(f"/api/v1/phonebook/{entry_id}")

    def test_delete_phonebook_entry(self, api_client: httpx.Client, test_phonebook_entry: dict):
        """Test deleting a phonebook entry."""
        # Create entry first
        response = api_client.post("/api/v1/phonebook", json=test_phonebook_entry)
        assert response.status_code == 201
        entry_id = response.json()["id"]

        # Get initial count
        response = api_client.get("/api/v1/phonebook")
        initial_count = response.json()["total"]

        # Delete entry
        response = api_client.delete(f"/api/v1/phonebook/{entry_id}")
        assert response.status_code == 204

        # Verify count decreased
        response = api_client.get("/api/v1/phonebook")
        assert response.json()["total"] == initial_count - 1

    def test_phonebook_xml_generation_yealink(self, api_client: httpx.Client):
        """Test Yealink phonebook XML generation."""
        response = api_client.get("/phonebook.xml")
        assert response.status_code == 200
        assert "xml" in response.headers.get("content-type", "").lower()

        xml_content = response.text
        assert "<?xml" in xml_content
        assert "YealinkIPPhoneDirectory" in xml_content

    def test_phonebook_xml_generation_fanvil(self, api_client: httpx.Client):
        """Test Fanvil phonebook XML generation."""
        response = api_client.get("/fanvil/phonebook.xml")
        assert response.status_code == 200
        assert "xml" in response.headers.get("content-type", "").lower()

        xml_content = response.text
        assert "<?xml" in xml_content
        # Fanvil format check

    def test_multiple_phonebook_entries(self, api_client: httpx.Client, test_phonebook_entry: dict):
        """Test creating multiple phonebook entries."""
        entries_data = [
            {**test_phonebook_entry, "name": "Contact 1", "number": "111-1111"},
            {**test_phonebook_entry, "name": "Contact 2", "number": "222-2222"},
            {**test_phonebook_entry, "name": "Contact 3", "number": "333-3333"},
        ]

        created_ids = []

        # Create multiple entries
        for entry_data in entries_data:
            response = api_client.post("/api/v1/phonebook", json=entry_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        # Verify all entries exist
        response = api_client.get("/api/v1/phonebook")
        assert response.status_code == 200
        entries = response.json()["entries"]

        created_names = {e["name"] for e in entries_data}
        api_names = {e["name"] for e in entries}

        assert created_names.issubset(api_names)

        # Cleanup
        for entry_id in created_ids:
            api_client.delete(f"/api/v1/phonebook/{entry_id}")
