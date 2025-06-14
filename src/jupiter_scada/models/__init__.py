# -*- coding: utf-8 -*-
"""
Jupiter SCADA Data Models Package.

This package contains the Pydantic models used throughout the application.
These models define the data structures for:
- API request and response bodies.
- Configuration objects parsed from YAML files.
- Internal representation of SCADA data points (tags).

By centralizing these models, we ensure data consistency across the API,
the core logic, and configuration handling.
"""

from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, Field


class ConfigTag(BaseModel):
    """
    Represents a single tag's configuration as defined in config.yaml.
    """
    node_id: str = Field(
        ...,
        description="The OPC UA Node ID for the tag.",
        examples=["ns=2;i=2"]
    )
    name: str = Field(
        ...,
        description="A unique, human-readable name for the tag.",
        examples=["Machine_1_Speed"]
    )
    description: Optional[str] = Field(
        default=None,
        description="An optional description of what the tag represents.",
        examples=["RPM of the main motor on Machine 1."]
    )


class TagData(BaseModel):
    """
    Represents the real-time data for a monitored tag.
    This model is typically used in API responses.
    """
    name: str = Field(
        ...,
        description="The unique name of the tag.",
        examples=["Machine_1_Speed"]
    )
    value: Any = Field(
        ...,
        description="The current value of the tag. Can be any data type.",
        examples=[1500.5, True, "Running"]
    )
    source_timestamp: Optional[datetime] = Field(
        default=None,
        description="The timestamp from the OPC UA server when the value was recorded (SourceTimestamp)."
    )
    server_timestamp: Optional[datetime] = Field(
        default=None,
        description="The timestamp from the OPC UA server when the value was received by the server (ServerTimestamp)."
    )
    status_code: Optional[int] = Field(
        default=None,
        description="The OPC UA status code for the value.",
        examples=[0]  # 0 typically means Good
    )
    status_text: Optional[str] = Field(
        default=None,
        description="A human-readable representation of the status code.",
        examples=["Good"]
    )


class AllTagsResponse(BaseModel):
    """
    API response model for a request to get all monitored tags.
    """
    tags: List[TagData] = Field(
        ...,
        description="A list of all currently monitored tags and their data."
    )
    last_updated: datetime = Field(
        ...,
        description="The timestamp when this data set was generated."
    )


# Define the public API of this module
__all__ = [
    "ConfigTag",
    "TagData",
    "AllTagsResponse",
]