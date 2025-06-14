# -*- coding: utf-8 -*-
"""
Pydantic models for representing OPC UA data structures.

This module defines the data models used for configuration and for representing
live tag data within the Jupiter SCADA application. These models are used for
parsing configuration files, for internal data management, and for defining
the schemas for API responses.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TagConfig(BaseModel):
    """
    Represents the static configuration for a single OPC UA tag.

    This model is used to parse the tag definitions from the `config.yaml` file.
    """
    name: str = Field(
        ...,
        description="A unique, human-readable name for the tag.",
        examples=["MotorSpeed", "TankLevel"]
    )
    node_id: str = Field(
        ...,
        description="The OPC UA NodeId in string format.",
        examples=["ns=2;i=1024", "ns=3;s=My.PLC.Tag"]
    )


class TagData(TagConfig):
    """
    Represents the live data for a monitored OPC UA tag.

    This model extends the static configuration with dynamic values read from
    the OPC UA server, such as the current value, timestamp, and status.
    It is the primary model used for API responses.
    """
    value: Optional[Any] = Field(
        None,
        description="The current value of the tag. Can be any data type.",
        examples=[123.45, True, "Running", 42]
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="The server or source timestamp for the current value (in UTC)."
    )
    status: str = Field(
        "Uncertain",
        description="The quality status of the tag value (e.g., 'Good', 'Bad', 'Uncertain').",
        examples=["Good", "Bad_NodeIdUnknown"]
    )
    error: Optional[str] = Field(
        None,
        description="An error message if reading the tag failed, otherwise null.",
        examples=["The node id does not exist."]
    )

    class Config:
        """Pydantic model configuration."""
        # Allows the model to be populated from object attributes,
        # which is useful for creating this model from other class instances.
        from_attributes = True


class TagValueUpdate(BaseModel):
    """
    Represents a minimal update for a tag's value, suitable for WebSocket pushes.
    """
    name: str = Field(
        ...,
        description="The unique name of the tag being updated.",
        examples=["MotorSpeed"]
    )
    value: Optional[Any] = Field(
        ...,
        description="The new value of the tag.",
        examples=[125.5]
    )
    timestamp: datetime = Field(
        ...,
        description="The timestamp of the new value."
    )
    status: str = Field(
        ...,
        description="The quality status of the new value.",
        examples=["Good"]
    )
```