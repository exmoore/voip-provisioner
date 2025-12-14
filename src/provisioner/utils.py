"""Utility functions for the provisioning server."""

import re
from typing import Literal


def normalize_mac(mac: str) -> str:
    """Normalize MAC address to lowercase without separators.

    Accepts formats:
    - 001565123456
    - 00:15:65:12:34:56
    - 00-15-65-12-34-56
    - 0015.6512.3456

    Returns:
        12-character lowercase hex string (e.g., "001565123456")

    Raises:
        ValueError: If MAC address is invalid.
    """
    # Remove all separators
    mac_clean = re.sub(r"[:\-.]", "", mac.strip().lower())

    # Validate format
    if not re.match(r"^[0-9a-f]{12}$", mac_clean):
        raise ValueError(f"Invalid MAC address: {mac}")

    return mac_clean


def format_mac(mac: str, separator: str = ":", uppercase: bool = False) -> str:
    """Format MAC address with separators.

    Args:
        mac: MAC address in any format
        separator: Separator to use (":", "-", ".", or "")
        uppercase: If True, use uppercase hex

    Returns:
        Formatted MAC address
    """
    mac_clean = normalize_mac(mac)

    if uppercase:
        mac_clean = mac_clean.upper()

    if separator == "":
        return mac_clean
    elif separator == ".":
        # Cisco style: 0015.6512.3456
        return f"{mac_clean[0:4]}.{mac_clean[4:8]}.{mac_clean[8:12]}"
    else:
        # Standard: 00:15:65:12:34:56
        pairs = [mac_clean[i : i + 2] for i in range(0, 12, 2)]
        return separator.join(pairs)


def get_mac_oui(mac: str) -> str:
    """Extract OUI (first 3 bytes) from MAC address.

    Args:
        mac: MAC address in any format

    Returns:
        6-character uppercase OUI (e.g., "001565")
    """
    mac_clean = normalize_mac(mac)
    return mac_clean[:6].upper()


def detect_vendor(mac: str, oui_map: dict[str, list[str]]) -> str | None:
    """Detect phone vendor from MAC OUI.

    Args:
        mac: MAC address
        oui_map: Dict mapping vendor name to list of OUI prefixes

    Returns:
        Vendor name (e.g., "yealink", "fanvil") or None if unknown
    """
    oui = get_mac_oui(mac)

    for vendor, prefixes in oui_map.items():
        # Normalize prefixes for comparison
        normalized_prefixes = [p.upper().replace(":", "").replace("-", "") for p in prefixes]
        if oui in normalized_prefixes:
            return vendor.lower()

    return None


def model_to_vendor(model: str) -> Literal["yealink", "fanvil"] | None:
    """Extract vendor from model name.

    Args:
        model: Model string like "yealink_t23g" or "fanvil_v64"

    Returns:
        Vendor name or None
    """
    model_lower = model.lower()
    if model_lower.startswith("yealink"):
        return "yealink"
    elif model_lower.startswith("fanvil"):
        return "fanvil"
    return None
