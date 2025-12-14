"""Tests for inventory loading."""

import tempfile
from pathlib import Path

import pytest
import yaml

from provisioner.inventory import (
    GlobalSettings,
    Inventory,
    PhoneEntry,
    PhonebookEntry,
    load_inventory,
)


class TestPhoneEntry:
    """Tests for PhoneEntry model."""
    
    def test_mac_normalization(self):
        phone = PhoneEntry(
            mac="00:15:65:12:34:56",
            model="yealink_t23g",
            extension="101",
            display_name="Test Phone",
            password="secret",
        )
        assert phone.mac == "001565123456"
    
    def test_line_label_default(self):
        phone = PhoneEntry(
            mac="001565123456",
            model="yealink_t23g",
            extension="101",
            display_name="Test Phone",
            password="secret",
        )
        assert phone.line_label == "Test Phone"
    
    def test_line_label_custom(self):
        phone = PhoneEntry(
            mac="001565123456",
            model="yealink_t23g",
            extension="101",
            display_name="Test Phone",
            password="secret",
            label="Custom Label",
        )
        assert phone.line_label == "Custom Label"


class TestInventory:
    """Tests for Inventory model."""
    
    @pytest.fixture
    def sample_inventory(self):
        return Inventory(
            global_settings=GlobalSettings(
                pbx_server="pbx.example.com",
                pbx_port=5060,
            ),
            phones=[
                PhoneEntry(
                    mac="001565123456",
                    model="yealink_t23g",
                    extension="101",
                    display_name="Phone 1",
                    password="pass1",
                ),
                PhoneEntry(
                    mac="0c383eabcdef",
                    model="fanvil_v64",
                    extension="102",
                    display_name="Phone 2",
                    password="pass2",
                ),
            ],
            phonebook=[
                PhonebookEntry(name="Phone 1", number="101"),
                PhonebookEntry(name="Phone 2", number="102"),
            ],
        )
    
    def test_get_phone_by_mac(self, sample_inventory):
        phone = sample_inventory.get_phone_by_mac("00:15:65:12:34:56")
        assert phone is not None
        assert phone.extension == "101"
    
    def test_get_phone_by_mac_not_found(self, sample_inventory):
        phone = sample_inventory.get_phone_by_mac("AA:BB:CC:DD:EE:FF")
        assert phone is None
    
    def test_get_effective_settings(self, sample_inventory):
        phone = sample_inventory.phones[0]
        settings = sample_inventory.get_effective_settings(phone)
        
        assert settings["pbx_server"] == "pbx.example.com"
        assert settings["pbx_port"] == 5060
        assert settings["extension"] == "101"
        assert settings["password"] == "pass1"
    
    def test_get_effective_settings_with_override(self, sample_inventory):
        # Add override to first phone
        sample_inventory.phones[0].pbx_server = "override.example.com"
        
        settings = sample_inventory.get_effective_settings(sample_inventory.phones[0])
        assert settings["pbx_server"] == "override.example.com"


class TestLoadInventory:
    """Tests for loading inventory from files."""
    
    def test_load_phones(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            phones_yml = {
                "global": {
                    "pbx_server": "test-pbx.local",
                    "pbx_port": 5060,
                },
                "phones": [
                    {
                        "mac": "00:15:65:11:22:33",
                        "model": "yealink_t23g",
                        "extension": "100",
                        "display_name": "Test",
                        "password": "testpass",
                    }
                ],
            }
            
            with open(tmpdir / "phones.yml", "w") as f:
                yaml.dump(phones_yml, f)
            
            inventory = load_inventory(tmpdir)
            
            assert len(inventory.phones) == 1
            assert inventory.phones[0].extension == "100"
            assert inventory.global_settings.pbx_server == "test-pbx.local"
    
    def test_load_phonebook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Empty phones file
            with open(tmpdir / "phones.yml", "w") as f:
                yaml.dump({"phones": []}, f)
            
            phonebook_yml = {
                "phonebook_name": "Test Directory",
                "phonebook": [
                    {"name": "Alice", "number": "101"},
                    {"name": "Bob", "number": "102"},
                ],
            }
            
            with open(tmpdir / "phonebook.yml", "w") as f:
                yaml.dump(phonebook_yml, f)
            
            inventory = load_inventory(tmpdir)
            
            assert len(inventory.phonebook) == 2
            assert inventory.phonebook_name == "Test Directory"
    
    def test_load_with_secrets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            phones_yml = {
                "phones": [
                    {
                        "mac": "001565112233",
                        "model": "yealink_t23g",
                        "extension": "100",
                        "display_name": "Test",
                        "password": "placeholder",
                    }
                ],
            }
            
            secrets_yml = {
                "phone_passwords": {
                    "100": "real_secret_password",
                }
            }
            
            with open(tmpdir / "phones.yml", "w") as f:
                yaml.dump(phones_yml, f)
            
            secrets_file = tmpdir / "secrets.yml"
            with open(secrets_file, "w") as f:
                yaml.dump(secrets_yml, f)
            
            inventory = load_inventory(tmpdir, secrets_file)
            
            assert inventory.phones[0].password == "real_secret_password"
