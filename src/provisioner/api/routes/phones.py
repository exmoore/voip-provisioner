"""Phone CRUD API endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ...config import Config, get_config
from ...exceptions import (
    DuplicateExtensionError,
    DuplicateMACError,
    InvalidMACError,
    PhoneNotFoundError,
)
from ...inventory import PhoneEntry, get_inventory
from ...persistence import YAMLRepository
from ...utils import detect_vendor, normalize_mac
from ..dependencies import get_repository
from ..schemas import (
    CreatePhoneRequest,
    PhoneConfigResponse,
    PhoneListResponse,
    PhoneResponse,
    UpdatePhoneRequest,
)

router = APIRouter()
logger = logging.getLogger("provisioner.api.phones")


@router.get("", response_model=PhoneListResponse)
async def list_phones() -> PhoneListResponse:
    """List all phones in inventory.

    Returns:
        PhoneListResponse with all phones
    """
    inventory = get_inventory()
    config = get_config()

    # Build phone responses with vendor detection
    phone_responses = []
    oui_map = {
        "yealink": config.vendor_oui.yealink,
        "fanvil": config.vendor_oui.fanvil,
    }

    for phone in inventory.phones:
        # Detect vendor
        vendor = detect_vendor(phone.mac, oui_map)
        if not vendor:
            model_lower = phone.model.lower()
            if "yealink" in model_lower:
                vendor = "yealink"
            elif "fanvil" in model_lower:
                vendor = "fanvil"

        # Get effective settings
        effective_settings = inventory.get_effective_settings(phone)

        phone_responses.append(
            PhoneResponse(
                mac=phone.mac,
                model=phone.model,
                extension=phone.extension,
                display_name=phone.display_name,
                pbx_server=phone.pbx_server,
                pbx_port=phone.pbx_port,
                transport=phone.transport,
                label=phone.label,
                codecs=phone.codecs,
                vendor=vendor,
                effective_settings=effective_settings,
            )
        )

    return PhoneListResponse(phones=phone_responses, total=len(phone_responses))


@router.post("", response_model=PhoneResponse, status_code=status.HTTP_201_CREATED)
async def create_phone(
    phone_data: CreatePhoneRequest,
    repository: YAMLRepository = Depends(get_repository),
) -> PhoneResponse:
    """Create a new phone in inventory.

    Args:
        phone_data: Phone data to create
        repository: YAML repository dependency

    Returns:
        Created phone response

    Raises:
        HTTPException: If phone MAC already exists, extension in use, or write fails
    """
    try:
        # Create PhoneEntry from request
        phone = PhoneEntry(
            mac=phone_data.mac,
            model=phone_data.model,
            extension=phone_data.extension,
            display_name=phone_data.display_name,
            password=phone_data.password,
            pbx_server=phone_data.pbx_server,
            pbx_port=phone_data.pbx_port,
            transport=phone_data.transport,
            label=phone_data.label,
            codecs=phone_data.codecs,
        )

        # Add phone via repository
        repository.add_phone(phone)

        # Get updated inventory
        inventory = get_inventory()
        config = get_config()

        # Detect vendor
        oui_map = {
            "yealink": config.vendor_oui.yealink,
            "fanvil": config.vendor_oui.fanvil,
        }
        vendor = detect_vendor(phone.mac, oui_map)

        # Get effective settings
        effective_settings = inventory.get_effective_settings(phone)

        logger.info(f"Created phone {phone.mac} (extension {phone.extension})")

        return PhoneResponse(
            mac=phone.mac,
            model=phone.model,
            extension=phone.extension,
            display_name=phone.display_name,
            pbx_server=phone.pbx_server,
            pbx_port=phone.pbx_port,
            transport=phone.transport,
            label=phone.label,
            codecs=phone.codecs,
            vendor=vendor,
            effective_settings=effective_settings,
        )

    except DuplicateMACError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except DuplicateExtensionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidMACError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create phone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create phone: {str(e)}",
        )


@router.get("/{mac}", response_model=PhoneResponse)
async def get_phone(mac: str) -> PhoneResponse:
    """Get a phone by MAC address.

    Args:
        mac: MAC address (will be normalized)

    Returns:
        Phone response

    Raises:
        HTTPException: If phone not found
    """
    try:
        normalized_mac = normalize_mac(mac)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    inventory = get_inventory()
    phone = inventory.get_phone_by_mac(normalized_mac)

    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone {normalized_mac} not found",
        )

    # Detect vendor
    config = get_config()
    oui_map = {
        "yealink": config.vendor_oui.yealink,
        "fanvil": config.vendor_oui.fanvil,
    }
    vendor = detect_vendor(phone.mac, oui_map)

    # Get effective settings
    effective_settings = inventory.get_effective_settings(phone)

    return PhoneResponse(
        mac=phone.mac,
        model=phone.model,
        extension=phone.extension,
        display_name=phone.display_name,
        pbx_server=phone.pbx_server,
        pbx_port=phone.pbx_port,
        transport=phone.transport,
        label=phone.label,
        codecs=phone.codecs,
        vendor=vendor,
        effective_settings=effective_settings,
    )


@router.put("/{mac}", response_model=PhoneResponse)
async def update_phone(
    mac: str,
    phone_data: UpdatePhoneRequest,
    repository: YAMLRepository = Depends(get_repository),
) -> PhoneResponse:
    """Update a phone by MAC address.

    Args:
        mac: MAC address (will be normalized)
        phone_data: Fields to update
        repository: YAML repository dependency

    Returns:
        Updated phone response

    Raises:
        HTTPException: If phone not found, extension in use, or update fails
    """
    try:
        normalized_mac = normalize_mac(mac)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Build updates dict (only include fields that are set)
    updates = {}
    if phone_data.model is not None:
        updates["model"] = phone_data.model
    if phone_data.extension is not None:
        updates["extension"] = phone_data.extension
    if phone_data.display_name is not None:
        updates["display_name"] = phone_data.display_name
    if phone_data.password is not None:
        updates["password"] = phone_data.password
    if phone_data.pbx_server is not None:
        updates["pbx_server"] = phone_data.pbx_server
    if phone_data.pbx_port is not None:
        updates["pbx_port"] = phone_data.pbx_port
    if phone_data.transport is not None:
        updates["transport"] = phone_data.transport
    if phone_data.label is not None:
        updates["label"] = phone_data.label
    if phone_data.codecs is not None:
        updates["codecs"] = phone_data.codecs

    try:
        repository.update_phone(normalized_mac, updates)

        # Get updated phone
        inventory = get_inventory()
        phone = inventory.get_phone_by_mac(normalized_mac)

        if not phone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phone {normalized_mac} not found after update",
            )

        # Detect vendor
        config = get_config()
        oui_map = {
            "yealink": config.vendor_oui.yealink,
            "fanvil": config.vendor_oui.fanvil,
        }
        vendor = detect_vendor(phone.mac, oui_map)

        # Get effective settings
        effective_settings = inventory.get_effective_settings(phone)

        logger.info(f"Updated phone {normalized_mac}")

        return PhoneResponse(
            mac=phone.mac,
            model=phone.model,
            extension=phone.extension,
            display_name=phone.display_name,
            pbx_server=phone.pbx_server,
            pbx_port=phone.pbx_port,
            transport=phone.transport,
            label=phone.label,
            codecs=phone.codecs,
            vendor=vendor,
            effective_settings=effective_settings,
        )

    except PhoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateExtensionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update phone {normalized_mac}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update phone: {str(e)}",
        )


@router.delete("/{mac}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phone(
    mac: str,
    repository: YAMLRepository = Depends(get_repository),
) -> None:
    """Delete a phone by MAC address.

    Args:
        mac: MAC address (will be normalized)
        repository: YAML repository dependency

    Raises:
        HTTPException: If phone not found or deletion fails
    """
    try:
        normalized_mac = normalize_mac(mac)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        repository.delete_phone(normalized_mac)
        logger.info(f"Deleted phone {normalized_mac}")

    except PhoneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete phone {normalized_mac}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete phone: {str(e)}",
        )


@router.get("/{mac}/config", response_model=PhoneConfigResponse)
async def preview_phone_config(mac: str) -> PhoneConfigResponse:
    """Preview the generated configuration for a phone.

    Args:
        mac: MAC address (will be normalized)

    Returns:
        Phone configuration preview

    Raises:
        HTTPException: If phone not found or vendor not supported
    """
    try:
        normalized_mac = normalize_mac(mac)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    inventory = get_inventory()
    phone = inventory.get_phone_by_mac(normalized_mac)

    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone {normalized_mac} not found",
        )

    # Detect vendor
    config = get_config()
    oui_map = {
        "yealink": config.vendor_oui.yealink,
        "fanvil": config.vendor_oui.fanvil,
    }
    vendor = detect_vendor(phone.mac, oui_map)

    if not vendor:
        model_lower = phone.model.lower()
        if "yealink" in model_lower:
            vendor = "yealink"
        elif "fanvil" in model_lower:
            vendor = "fanvil"

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot determine vendor for phone {normalized_mac}",
        )

    # Import generators (avoid circular import)
    from ...generators import FanvilGenerator, YealinkGenerator

    # Generate config
    templates_dir = config.base_dir / config.paths.templates_dir
    if vendor == "yealink":
        generator = YealinkGenerator(templates_dir)
    elif vendor == "fanvil":
        generator = FanvilGenerator(templates_dir)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported vendor: {vendor}",
        )

    settings = inventory.get_effective_settings(phone)
    config_content = generator.generate_config(settings)

    return PhoneConfigResponse(
        mac=phone.mac,
        extension=phone.extension,
        vendor=vendor,
        config=config_content,
    )
