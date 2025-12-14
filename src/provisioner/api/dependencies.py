"""FastAPI dependencies for API routes."""

from fastapi import Depends

from ..config import Config, get_config
from ..persistence import YAMLRepository


def get_repository(config: Config = Depends(get_config)) -> YAMLRepository:
    """Get YAML repository instance.

    Args:
        config: Application configuration

    Returns:
        YAMLRepository instance
    """
    inventory_dir = config.base_dir / config.paths.inventory_dir
    secrets_file = config.base_dir / config.paths.secrets_file

    return YAMLRepository(
        inventory_dir=inventory_dir,
        secrets_file=secrets_file if secrets_file.exists() else None,
    )
