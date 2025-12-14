"""Yealink phone configuration generator."""

from typing import Any

from .base import BaseGenerator


class YealinkGenerator(BaseGenerator):
    """Generator for Yealink phones (T23G, etc.)."""
    
    VENDOR = "yealink"
    TEMPLATE_DIR = "yealink_t23g"
    CONFIG_TEMPLATE = "mac.cfg.j2"
    PHONEBOOK_TEMPLATE = "phonebook.xml.j2"
    
    def generate_config(self, settings: dict[str, Any]) -> str:
        """Generate Yealink CFG configuration.
        
        Yealink uses a simple key=value format with #!version header.
        """
        return self.render_template(self.CONFIG_TEMPLATE, **settings)
    
    def generate_phonebook(
        self, 
        entries: list[dict[str, str]], 
        phonebook_name: str = "Directory"
    ) -> str:
        """Generate Yealink XML phonebook.
        
        Yealink uses a specific XML format for remote phonebook.
        """
        return self.render_template(
            self.PHONEBOOK_TEMPLATE,
            entries=entries,
            phonebook_name=phonebook_name,
        )
