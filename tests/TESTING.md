# Google Sheets MCP Server - Testing Guide

This document describes the test suite for the Google Sheets FastMCP server.

## Overview

- **Total Tools Tested**: 20 MCP tools
- **Test Framework**: pytest with pytest-asyncio
- **Testing Pattern**: FastMCP in-memory testing with mocked Google API calls

## Test Structure

```
tests/
  __init__.py           # Package marker
  conftest.py           # Shared fixtures (mcp_client, mocks)
  pytest.ini            # Pytest configuration
  test_server.py        # Comprehensive tests for all 20 tools
```

## Installation

Install test dependencies:

```bash
# Using pip with extras
pip install -e ".[test]"

# Or install individually
pip install pytest pytest-asyncio inline-snapshot dirty-equals pytest-cov
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test Class

```bash
pytest tests/test_server.py::TestSheetsCreate
pytest tests/test_server.py::TestSheetsRead
```

### Run Specific Test

```bash
pytest tests/test_server.py::TestSheetsCreate::test_create_spreadsheet_basic
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html
```

### Run Parametrized Tests Only

```bash
pytest -k "parametrize"
```

## Test Categories

### Basic Data Operations (5 tools)

| Tool | Test Class | Tests |
|------|------------|-------|
| `sheets_create` | `TestSheetsCreate` | Basic creation, multiple sheets |
| `sheets_read` | `TestSheetsRead` | Read data, empty range |
| `sheets_write` | `TestSheetsWrite` | Write data, formulas |
| `sheets_append` | `TestSheetsAppend` | Single row, multiple rows |
| `sheets_get_sheet_id` | `TestSheetsGetSheetId` | Found, not found |

### Row/Cell Operations (3 tools)

| Tool | Test Class | Tests |
|------|------------|-------|
| `sheets_delete_rows` | `TestSheetsDeleteRows` | Single row, multiple rows |
| `sheets_insert_rows` | `TestSheetsInsertRows` | Single row, multiple rows |
| `sheets_clear_range` | `TestSheetsClearRange` | Clear success |

### Data Operations (6 tools)

| Tool | Test Class | Tests |
|------|------------|-------|
| `sheets_find_replace` | `TestSheetsFindReplace` | Basic, options, no matches |
| `sheets_duplicate_sheet` | `TestSheetsDuplicateSheet` | Duplicate success |
| `sheets_delete_duplicates` | `TestSheetsDeleteDuplicates` | All columns, specific columns |
| `sheets_trim_whitespace` | `TestSheetsTrimWhitespace` | Trim success |
| `sheets_merge_cells` | `TestSheetsMergeCells` | Merge all, parametrized types |
| `sheets_copy_paste` | `TestSheetsCopyPaste` | Normal, parametrized paste types |

### Formatting (2 tools)

| Tool | Test Class | Tests |
|------|------------|-------|
| `sheets_format_cells` | `TestSheetsFormatCells` | Bold, multiple options |
| `sheets_add_borders` | `TestSheetsAddBorders` | Default, parametrized styles |

### Charts (1 tool)

| Tool | Test Class | Tests |
|------|------------|-------|
| `sheets_add_chart` | `TestSheetsAddChart` | Column chart, parametrized types, position |

### Validation & Sorting (3 tools)

| Tool | Test Class | Tests |
|------|------------|-------|
| `sheets_add_dropdown` | `TestSheetsAddDropdown` | Basic, many options |
| `sheets_conditional_format` | `TestSheetsConditionalFormat` | Greater than, parametrized types |
| `sheets_sort_range` | `TestSheetsSortRange` | Ascending, descending |

### Edge Cases & Workflows

| Test Class | Tests |
|------------|-------|
| `TestEdgeCases` | Empty values, large range, special characters |
| `TestWorkflows` | Create-populate workflow, format-chart workflow |

## Fixtures

### `mcp_client`
Provides an in-memory FastMCP client with mocked Google API service.

```python
async def test_example(mcp_client):
    client, mock_service = mcp_client

    # Configure mock
    mock_service.spreadsheets().values().get().execute.return_value = {
        'values': [['A', 'B'], ['1', '2']]
    }

    # Call tool
    result = await client.call_tool(
        name="sheets_read",
        arguments={"spreadsheet_id": "...", "range": "A1:B2"}
    )
```

### `sample_spreadsheet_id`
Returns a sample spreadsheet ID for testing.

### `sample_sheet_id`
Returns a sample sheet ID (0) for testing.

### `sample_values`
Returns sample data values for write/read tests.

## Mocking Strategy

All tests mock two key components:

1. **`get_credentials()`** - Returns mock OAuth credentials
2. **`build('sheets', 'v4', credentials=creds)`** - Returns mock Sheets API service

This allows testing all tool functionality without actual Google API calls.

### Mock Configuration Examples

```python
# Mock spreadsheets().create()
mock_service.spreadsheets().create().execute.return_value = {
    'spreadsheetId': 'abc123',
    'spreadsheetUrl': 'https://...'
}

# Mock spreadsheets().values().get()
mock_service.spreadsheets().values().get().execute.return_value = {
    'values': [['data']]
}

# Mock spreadsheets().batchUpdate()
mock_service.spreadsheets().batchUpdate().execute.return_value = {
    'replies': [{'findReplace': {'occurrencesChanged': 5}}]
}
```

## Parametrized Tests

Several tests use `@pytest.mark.parametrize` for comprehensive coverage:

- **Merge types**: MERGE_ALL, MERGE_COLUMNS, MERGE_ROWS
- **Paste types**: NORMAL, VALUES, FORMAT, FORMULA
- **Border styles**: SOLID, DASHED, DOTTED
- **Chart types**: COLUMN, BAR, LINE, PIE, SCATTER
- **Condition types**: NUMBER_GREATER, NUMBER_LESS, TEXT_CONTAINS

## Adding New Tests

1. Create a new test class following the naming pattern `Test{ToolName}`
2. Use the `mcp_client` fixture to get client and mock service
3. Configure mock return values before calling the tool
4. Assert on the result data

Example:

```python
class TestNewTool:
    """Tests for new_tool."""

    async def test_basic_success(self, mcp_client, sample_spreadsheet_id):
        """Test basic functionality."""
        client, mock_service = mcp_client

        # Configure mock
        mock_service.spreadsheets().someMethod().execute.return_value = {
            'result': 'value'
        }

        # Call tool
        result = await client.call_tool(
            name="new_tool",
            arguments={"param": "value"}
        )

        # Assert
        result_data = json.loads(result.data)
        assert result_data['result'] == 'value'
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    pip install -e ".[test]"
    pytest --cov=src --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: coverage.xml
```

## Troubleshooting

### Import Errors

Ensure you're in the project root and have installed the package:

```bash
pip install -e ".[test]"
```

### Async Warnings

The `asyncio_mode = "auto"` in pytest configuration handles async tests automatically. If you see warnings, ensure pytest-asyncio is installed.

### Mock Not Working

Ensure patches are applied before importing the server:

```python
with patch('src.server.get_credentials', return_value=mock_creds), \
     patch('src.server.build', return_value=mock_service):
    from src.server import mcp  # Import after patching
```
