"""Base class for phone configuration generators."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class BaseGenerator(ABC):
    """Abstract base class for phone configuration generators."""

    # Subclasses must define these
    VENDOR: str = ""
    TEMPLATE_DIR: str = ""
    CONFIG_TEMPLATE: str = "mac.cfg.j2"
    PHONEBOOK_TEMPLATE: str = "phonebook.xml.j2"

    def __init__(self, templates_dir: Path | str):
        """Initialize generator with templates directory.

        Args:
            templates_dir: Base templates directory (contains vendor subdirs)
        """
        self.templates_dir = Path(templates_dir)
        self.vendor_templates = self.templates_dir / self.TEMPLATE_DIR

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(
                [
                    str(self.vendor_templates),
                    str(self.templates_dir),  # Fallback to base templates
                ]
            ),
            autoescape=select_autoescape(["xml", "html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters["format_mac"] = self._format_mac_filter

    @staticmethod
    def _format_mac_filter(mac: str, separator: str = ":", uppercase: bool = False) -> str:
        """Jinja2 filter for MAC formatting."""
        from ..utils import format_mac

        return format_mac(mac, separator, uppercase)

    @abstractmethod
    def generate_config(self, settings: dict[str, Any]) -> str:
        """Generate phone configuration.

        Args:
            settings: Merged phone settings from inventory

        Returns:
            Configuration file contents as string
        """
        pass

    @abstractmethod
    def generate_phonebook(
        self, entries: list[dict[str, str]], phonebook_name: str = "Directory"
    ) -> str:
        """Generate phonebook/directory file.

        Args:
            entries: List of {"name": ..., "number": ...} dicts
            phonebook_name: Name/title of the phonebook

        Returns:
            Phonebook file contents as string
        """
        pass

    def render_template(self, template_name: str, **context: Any) -> str:
        """Render a Jinja2 template.

        Args:
            template_name: Template filename
            **context: Variables to pass to template

        Returns:
            Rendered template string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    @property
    def config_content_type(self) -> str:
        """HTTP Content-Type for config files."""
        return "text/plain; charset=utf-8"

    @property
    def phonebook_content_type(self) -> str:
        """HTTP Content-Type for phonebook files."""
        return "application/xml; charset=utf-8"
