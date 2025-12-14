"""Fanvil phone configuration generator."""

from typing import Any

from .base import BaseGenerator


class FanvilGenerator(BaseGenerator):
    """Generator for Fanvil phones (V64, etc.)."""
    
    VENDOR = "fanvil"
    TEMPLATE_DIR = "fanvil_v64"
    CONFIG_TEMPLATE = "mac.cfg.j2"
    PHONEBOOK_TEMPLATE = "phonebook.xml.j2"
    
    def generate_config(self, settings: dict[str, Any]) -> str:
        """Generate Fanvil CFG configuration.
        
        Fanvil uses a specific format with module headers and
        a 64-character file header.
        """
        return self.render_template(self.CONFIG_TEMPLATE, **settings)
    
    def generate_phonebook(
        self, 
        entries: list[dict[str, str]], 
        phonebook_name: str = "Directory"
    ) -> str:
        """Generate Fanvil XML phonebook.
        
        Fanvil uses a similar but slightly different XML format.
        """
        return self.render_template(
            self.PHONEBOOK_TEMPLATE,
            entries=entries,
            phonebook_name=phonebook_name,
        )
