"""API module for REST endpoints."""

from fastapi import APIRouter

from .routes import phones, phonebook, settings

# Create main API router
api_router = APIRouter()

# Include subrouters
api_router.include_router(phones.router, prefix="/phones", tags=["phones"])
api_router.include_router(phonebook.router, prefix="/phonebook", tags=["phonebook"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])

__all__ = ["api_router"]
