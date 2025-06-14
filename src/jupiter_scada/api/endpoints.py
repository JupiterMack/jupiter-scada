# -*- coding: utf-8 -*-
"""
Defines the REST API endpoints for the Jupiter SCADA application.

This module uses FastAPI's APIRouter to create routes for accessing
OPC UA tag data. The endpoints interact with the singleton OpcuaClient
instance to retrieve real-time or cached data.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

# This import assumes the OpcuaClient class is defined in this location.
# It's a relative import because this module is part of the 'api' package.
from ..opcua.client import OpcuaClient

# --- Pydantic Models for API Responses ---


class TagData(BaseModel):
    """
    Represents the data for a single OPC UA tag.
    """
    value: Any = Field(..., description="The current value of the tag.")
    source_timestamp: datetime | None = Field(
        ..., description="The timestamp from the source (OPC UA Server)."
    )
    server_timestamp: datetime | None = Field(
        ...,
        description="The timestamp from the server when the value was received.",
    )
    status_code: int = Field(
        ..., description="The numeric status code of the value (0 indicates good quality)."
    )
    status_text: str = Field(
        ..., description="A human-readable status of the tag value (e.g., 'Good')."
    )

    class Config:
        # Pydantic v2 config
        json_schema_extra = {
            "example": {
                "value": 123.45,
                "source_timestamp": "2023-10-27T10:00:00Z",
                "server_timestamp": "2023-10-27T10:00:01Z",
                "status_code": 0,
                "status_text": "Good",
            }
        }


class AllTagsResponse(BaseModel):
    """
    Response model for the endpoint that retrieves all tags.
    """
    tags: Dict[str, TagData] = Field(
        ..., description="A dictionary of all monitored tags and their data."
    )


# --- Router and Dependencies ---

router = APIRouter(
    prefix="/api",
    tags=["OPC UA Tags"],
)

logger = logging.getLogger(__name__)


def get_opcua_client(request: Request) -> OpcuaClient:
    """
    FastAPI dependency to get the singleton OpcuaClient instance.

    The client is expected to be initialized and attached to the app's state
    during the application startup lifecycle event.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The running OpcuaClient instance.

    Raises:
        RuntimeError: If the OpcuaClient is not found in the app state,
                      indicating a server startup problem.
    """
    if not hasattr(request.app.state, "opcua_client"):
        logger.error("OpcuaClient not found in application state. It may not have been initialized correctly.")
        # This is a server error, not a client error.
        raise RuntimeError("OpcuaClient not initialized or attached to app state.")
    return request.app.state.opcua_client


# --- API Endpoints ---


@router.get(
    "/tags",
    response_model=AllTagsResponse,
    summary="Get all monitored tags",
    description="Retrieves the latest known values for all OPC UA tags configured for monitoring.",
)
async def get_all_tags(
    client: OpcuaClient = Depends(get_opcua_client),
) -> AllTagsResponse:
    """
    Endpoint to fetch data for all monitored OPC UA tags.

    This reads the current values from the client's internal data cache, which is
    updated by the background OPC UA subscription.
    """
    logger.info("API request received for all tags.")
    all_data = await client.get_all_tag_data()

    # Format the data to match the Pydantic model
    formatted_tags: Dict[str, TagData] = {}
    for tag_name, data_value in all_data.items():
        if data_value:
            formatted_tags[tag_name] = TagData(
                value=data_value.Value.Value,
                source_timestamp=data_value.SourceTimestamp,
                server_timestamp=data_value.ServerTimestamp,
                status_code=data_value.StatusCode.Value,
                status_text=data_value.StatusCode.name,
            )
        else:
            # Handle case where a tag is configured but has no data yet
            formatted_tags[tag_name] = TagData(
                value=None,
                source_timestamp=None,
                server_timestamp=None,
                status_code=0x80000000, # Bad
                status_text="NoData",
            )

    return AllTagsResponse(tags=formatted_tags)


@router.get(
    "/tags/{tag_name}",
    response_model=TagData,
    summary="Get a specific tag by name",
    description="Retrieves the latest known value for a single, specified OPC UA tag.",
    responses={404: {"description": "Tag not found or not monitored."}},
)
async def get_tag_by_name(
    tag_name: str, client: OpcuaClient = Depends(get_opcua_client)
) -> TagData:
    """
    Endpoint to fetch data for a specific OPC UA tag by its configured name.

    Args:
        tag_name: The name of the tag as defined in the configuration.
        client: The injected OpcuaClient instance.

    Returns:
        The data for the requested tag.

    Raises:
        HTTPException: If the tag is not found in the client's monitored tags.
    """
    logger.info(f"API request received for tag: {tag_name}")
    data_value = await client.get_tag_data(tag_name)

    if data_value is None:
        logger.warning(f"Tag '{tag_name}' not found for API request.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag '{tag_name}' not found. It might not be configured for monitoring or has not received data yet.",
        )

    return TagData(
        value=data_value.Value.Value,
        source_timestamp=data_value.SourceTimestamp,
        server_timestamp=data_value.ServerTimestamp,
        status_code=data_value.StatusCode.Value,
        status_text=data_value.StatusCode.name,
    )
```