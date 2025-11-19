"""
Pytest configuration and fixtures for Google Sheets MCP Server tests.

Uses FastMCP in-memory testing pattern with mocked Google API calls.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastmcp.client import Client


@pytest.fixture
def mock_credentials():
    """Mock Google OAuth credentials."""
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.expired = False
    return mock_creds


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets API service with all methods."""
    service = MagicMock()

    # Mock spreadsheets methods
    spreadsheets = MagicMock()
    service.spreadsheets.return_value = spreadsheets

    # Mock values methods
    values = MagicMock()
    spreadsheets.values.return_value = values

    return service


@pytest.fixture
async def mcp_client(mock_credentials, mock_sheets_service):
    """
    Create in-memory MCP client for testing.

    Patches get_credentials and Google API service to avoid
    actual API calls during testing.
    """
    with patch('src.server.get_credentials', return_value=mock_credentials), \
         patch('src.server.build', return_value=mock_sheets_service):

        # Import the mcp server after patching
        from src.server import mcp

        async with Client(transport=mcp) as client:
            yield client, mock_sheets_service


@pytest.fixture
def sample_spreadsheet_id():
    """Sample spreadsheet ID for testing."""
    return "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"


@pytest.fixture
def sample_sheet_id():
    """Sample sheet ID for testing."""
    return 0


@pytest.fixture
def sample_values():
    """Sample data values for testing."""
    return [
        ["Name", "Age", "City"],
        ["Alice", "30", "New York"],
        ["Bob", "25", "Los Angeles"],
        ["Charlie", "35", "Chicago"]
    ]
