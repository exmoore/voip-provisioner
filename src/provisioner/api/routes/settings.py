"""Global settings API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ...inventory import GlobalSettings, get_inventory
from ...persistence import YAMLRepository
from ..dependencies import get_repository
from ..schemas import GlobalSettingsRequest, GlobalSettingsResponse

router = APIRouter()
logger = logging.getLogger("provisioner.api.settings")


@router.get("", response_model=GlobalSettingsResponse)
async def get_global_settings() -> GlobalSettingsResponse:
    """Get current global settings.

    Returns:
        Global settings response
    """
    inventory = get_inventory()
    settings = inventory.global_settings

    return GlobalSettingsResponse(
        pbx_server=settings.pbx_server,
        pbx_port=settings.pbx_port,
        transport=settings.transport,
        ntp_server=settings.ntp_server,
        timezone=settings.timezone,
        codecs=settings.codecs,
    )


@router.put("", response_model=GlobalSettingsResponse)
async def update_global_settings(
    settings_data: GlobalSettingsRequest,
    repository: YAMLRepository = Depends(get_repository),
) -> GlobalSettingsResponse:
    """Update global settings.

    Args:
        settings_data: New global settings
        repository: YAML repository dependency

    Returns:
        Updated global settings response

    Raises:
        HTTPException: If update fails
    """
    try:
        # Create GlobalSettings from request
        settings = GlobalSettings(
            pbx_server=settings_data.pbx_server,
            pbx_port=settings_data.pbx_port,
            transport=settings_data.transport,
            ntp_server=settings_data.ntp_server,
            timezone=settings_data.timezone,
            codecs=settings_data.codecs,
        )

        # Update via repository
        repository.update_global_settings(settings)

        logger.info("Updated global settings")

        return GlobalSettingsResponse(
            pbx_server=settings.pbx_server,
            pbx_port=settings.pbx_port,
            transport=settings.transport,
            ntp_server=settings.ntp_server,
            timezone=settings.timezone,
            codecs=settings.codecs,
        )

    except Exception as e:
        logger.error(f"Failed to update global settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update global settings: {str(e)}",
        )
