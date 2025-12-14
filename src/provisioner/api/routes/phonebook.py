"""Phonebook CRUD API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ...exceptions import PhonebookEntryNotFoundError
from ...inventory import PhonebookEntry, get_inventory
from ...persistence import YAMLRepository
from ..dependencies import get_repository
from ..schemas import (
    CreatePhonebookEntryRequest,
    PhonebookEntryResponse,
    PhonebookListResponse,
    UpdatePhonebookEntryRequest,
)

router = APIRouter()
logger = logging.getLogger("provisioner.api.phonebook")


@router.get("", response_model=PhonebookListResponse)
async def list_phonebook_entries() -> PhonebookListResponse:
    """List all phonebook entries.

    Returns:
        PhonebookListResponse with all entries
    """
    inventory = get_inventory()

    # Build phonebook entry responses with index as ID
    entry_responses = [
        PhonebookEntryResponse(id=i, name=entry.name, number=entry.number)
        for i, entry in enumerate(inventory.phonebook)
    ]

    return PhonebookListResponse(
        phonebook_name=inventory.phonebook_name,
        entries=entry_responses,
        total=len(entry_responses),
    )


@router.post("", response_model=PhonebookEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_phonebook_entry(
    entry_data: CreatePhonebookEntryRequest,
    repository: YAMLRepository = Depends(get_repository),
) -> PhonebookEntryResponse:
    """Create a new phonebook entry.

    Args:
        entry_data: Phonebook entry data to create
        repository: YAML repository dependency

    Returns:
        Created phonebook entry response

    Raises:
        HTTPException: If creation fails
    """
    try:
        # Create PhonebookEntry from request
        entry = PhonebookEntry(name=entry_data.name, number=entry_data.number)

        # Get current count for new ID
        inventory = get_inventory()
        new_id = len(inventory.phonebook)

        # Add entry via repository
        repository.add_phonebook_entry(entry)

        logger.info(f"Created phonebook entry: {entry.name}")

        return PhonebookEntryResponse(id=new_id, name=entry.name, number=entry.number)

    except Exception as e:
        logger.error(f"Failed to create phonebook entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create phonebook entry: {str(e)}",
        )


@router.get("/{entry_id}", response_model=PhonebookEntryResponse)
async def get_phonebook_entry(entry_id: int) -> PhonebookEntryResponse:
    """Get a phonebook entry by ID.

    Args:
        entry_id: Entry index (0-based)

    Returns:
        Phonebook entry response

    Raises:
        HTTPException: If entry not found
    """
    inventory = get_inventory()

    if entry_id < 0 or entry_id >= len(inventory.phonebook):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phonebook entry {entry_id} not found",
        )

    entry = inventory.phonebook[entry_id]
    return PhonebookEntryResponse(id=entry_id, name=entry.name, number=entry.number)


@router.put("/{entry_id}", response_model=PhonebookEntryResponse)
async def update_phonebook_entry(
    entry_id: int,
    entry_data: UpdatePhonebookEntryRequest,
    repository: YAMLRepository = Depends(get_repository),
) -> PhonebookEntryResponse:
    """Update a phonebook entry by ID.

    Args:
        entry_id: Entry index (0-based)
        entry_data: Fields to update
        repository: YAML repository dependency

    Returns:
        Updated phonebook entry response

    Raises:
        HTTPException: If entry not found or update fails
    """
    # Get current entry
    inventory = get_inventory()

    if entry_id < 0 or entry_id >= len(inventory.phonebook):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phonebook entry {entry_id} not found",
        )

    current_entry = inventory.phonebook[entry_id]

    # Build updated entry
    updated_entry = PhonebookEntry(
        name=entry_data.name if entry_data.name is not None else current_entry.name,
        number=entry_data.number if entry_data.number is not None else current_entry.number,
    )

    try:
        repository.update_phonebook_entry(entry_id, updated_entry)

        logger.info(f"Updated phonebook entry {entry_id}: {updated_entry.name}")

        return PhonebookEntryResponse(
            id=entry_id,
            name=updated_entry.name,
            number=updated_entry.number,
        )

    except PhonebookEntryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update phonebook entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update phonebook entry: {str(e)}",
        )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phonebook_entry(
    entry_id: int,
    repository: YAMLRepository = Depends(get_repository),
) -> None:
    """Delete a phonebook entry by ID.

    Args:
        entry_id: Entry index (0-based)
        repository: YAML repository dependency

    Raises:
        HTTPException: If entry not found or deletion fails
    """
    try:
        repository.delete_phonebook_entry(entry_id)
        logger.info(f"Deleted phonebook entry {entry_id}")

    except PhonebookEntryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete phonebook entry {entry_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete phonebook entry: {str(e)}",
        )
