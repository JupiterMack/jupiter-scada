# -*- coding: utf-8 -*-
"""
Unit tests for the Jupiter SCADA FastAPI API endpoints.

This module uses pytest and httpx to test the API layer in isolation.
The OpcuaClient dependency is mocked to simulate interactions with an
OPC UA server, allowing for predictable testing of the API's logic,
status codes, and response formats.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from fastapi import status

# The FastAPI app instance from the main application
from src.jupiter_scada.api.server import app
from src.jupiter_scada.api.dependencies import get_opcua_client
from src.jupiter_scada.models.opc import TagData

# Sample data for mocking
# Using a fixed datetime for reproducible tests
FIXED_DATETIME = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)

SAMPLE_TAG_1 = TagData(
    id="ns=2;s=Device1.Temperature",
    name="Temperature",
    value=25.5,
    status="Good",
    timestamp=FIXED_DATETIME
)

SAMPLE_TAG_2 = TagData(
    id="ns=2;s=Device1.Pressure",
    name="Pressure",
    value=101.3,
    status="Good",
    timestamp=FIXED_DATETIME
)

ALL_TAGS_DATA = [SAMPLE_TAG_1, SAMPLE_TAG_2]

# Use pytest-asyncio for all async tests in this module
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_opcua_client() -> AsyncMock:
    """
    Fixture to create a mock of the OpcuaClient.

    This mock simulates OPC UA interactions without needing a real server.
    It provides predictable return values for testing the API layer.
    """
    mock_client = AsyncMock()

    # Mock the get_all_tags_data method
    mock_client.get_all_tags_data.return_value = ALL_TAGS_DATA

    # Mock the get_tag_data method with a side effect to handle different inputs
    def get_tag_side_effect(tag_id: str) -> TagData | None:
        if tag_id == SAMPLE_TAG_1.id:
            return SAMPLE_TAG_1
        if tag_id == SAMPLE_TAG_2.id:
            return SAMPLE_TAG_2
        return None

    mock_client.get_tag_data.side_effect = get_tag_side_effect

    # Mock the is_connected method, default to True
    mock_client.is_connected.return_value = True

    return mock_client


@pytest.fixture
async def test_client(mock_opcua_client: AsyncMock) -> httpx.AsyncClient:
    """
    Fixture to create an httpx.AsyncClient for the FastAPI app.

    It uses FastAPI's dependency override mechanism to replace the real
    `get_opcua_client` dependency with the mock client for the duration
    of a test.
    """
    # This is the key part: override the dependency with our mock
    app.dependency_overrides[get_opcua_client] = lambda: mock_opcua_client

    # Create the async test client within an async context manager
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up the dependency override after the test has run
    app.dependency_overrides.clear()


# --- Test Cases ---

async def test_read_root(test_client: httpx.AsyncClient):
    """
    Test the root endpoint (`/`) which should serve the main HTML page.
    """
    response = await test_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    # Check for a key element from index.html
    assert "<title>Jupiter SCADA Dashboard</title>" in response.text


async def test_get_all_tags_success(test_client: httpx.AsyncClient):
    """
    Test GET /api/v1/tags endpoint for a successful retrieval of all tags.
    """
    response = await test_client.get("/api/v1/tags")
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert len(response_data) == 2
    # Check if the response data matches the mocked data
    assert response_data[0]["id"] == SAMPLE_TAG_1.id
    assert response_data[0]["name"] == SAMPLE_TAG_1.name
    assert response_data[0]["value"] == SAMPLE_TAG_1.value
    assert response_data[1]["id"] == SAMPLE_TAG_2.id


async def test_get_all_tags_empty(test_client: httpx.AsyncClient, mock_opcua_client: AsyncMock):
    """
    Test GET /api/v1/tags when the OPC UA client returns no tags.
    """
    # Override the mock's return value for this specific test
    mock_opcua_client.get_all_tags_data.return_value = []

    response = await test_client.get("/api/v1/tags")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_get_single_tag_success(test_client: httpx.AsyncClient):
    """
    Test GET /api/v1/tags/{tag_id} for a successful retrieval of a single tag.
    """
    tag_id_to_find = SAMPLE_TAG_1.id
    # httpx handles URL encoding of the tag_id
    response = await test_client.get(f"/api/v1/tags/{tag_id_to_find}")

    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data["id"] == SAMPLE_TAG_1.id
    assert response_data["name"] == SAMPLE_TAG_1.name
    assert response_data["value"] == SAMPLE_TAG_1.value
    assert "timestamp" in response_data
    assert response_data["timestamp"] == SAMPLE_TAG_1.timestamp.isoformat().replace('+00:00', 'Z')


async def test_get_single_tag_not_found(test_client: httpx.AsyncClient):
    """
    Test GET /api/v1/tags/{tag_id} when the requested tag does not exist.
    """
    non_existent_tag_id = "ns=0;s=Unknown.Tag"
    response = await test_client.get(f"/api/v1/tags/{non_existent_tag_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": f"Tag with id '{non_existent_tag_id}' not found"}


async def test_health_check_ok(test_client: httpx.AsyncClient, mock_opcua_client: AsyncMock):
    """
    Test GET /api/v1/health when the OPC UA client is connected.
    """
    # Ensure the mock reports a connected state
    mock_opcua_client.is_connected.return_value = True

    response = await test_client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "opcua_connected": True}


async def test_health_check_error(test_client: httpx.AsyncClient, mock_opcua_client: AsyncMock):
    """
    Test GET /api/v1/health when the OPC UA client is not connected.
    """
    # Set the mock to report a disconnected state for this test
    mock_opcua_client.is_connected.return_value = False

    response = await test_client.get("/api/v1/health")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"status": "error", "opcua_connected": False}
```