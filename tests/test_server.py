"""
Comprehensive tests for Google Sheets MCP Server.

Tests all 20 tools with success cases, error handling, and edge cases.
Uses FastMCP in-memory testing pattern with mocked Google API calls.
"""

import pytest
import json
from unittest.mock import MagicMock


# ============================================================================
# BASIC DATA OPERATIONS TESTS
# ============================================================================

class TestSheetsCreate:
    """Tests for sheets_create tool."""

    async def test_create_spreadsheet_basic(self, mcp_client, sample_spreadsheet_id):
        """Test creating a basic spreadsheet with default sheet."""
        client, mock_service = mcp_client

        # Configure mock response
        mock_service.spreadsheets().create().execute.return_value = {
            'spreadsheetId': sample_spreadsheet_id,
            'spreadsheetUrl': f'https://docs.google.com/spreadsheets/d/{sample_spreadsheet_id}'
        }

        result = await client.call_tool(
            name="sheets_create",
            arguments={"title": "Test Spreadsheet"}
        )

        result_data = json.loads(result.data)
        assert 'spreadsheetId' in result_data
        assert 'spreadsheetUrl' in result_data
        assert result_data['spreadsheetId'] == sample_spreadsheet_id

    async def test_create_spreadsheet_with_multiple_sheets(self, mcp_client, sample_spreadsheet_id):
        """Test creating spreadsheet with multiple named sheets."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().create().execute.return_value = {
            'spreadsheetId': sample_spreadsheet_id,
            'spreadsheetUrl': f'https://docs.google.com/spreadsheets/d/{sample_spreadsheet_id}'
        }

        result = await client.call_tool(
            name="sheets_create",
            arguments={
                "title": "Multi-Sheet Spreadsheet",
                "sheet_titles": ["Data", "Summary", "Charts"]
            }
        )

        result_data = json.loads(result.data)
        assert result_data['spreadsheetId'] == sample_spreadsheet_id


class TestSheetsRead:
    """Tests for sheets_read tool."""

    async def test_read_data_success(self, mcp_client, sample_spreadsheet_id, sample_values):
        """Test reading data from a range."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': sample_values
        }

        result = await client.call_tool(
            name="sheets_read",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:C4"
            }
        )

        result_data = json.loads(result.data)
        assert len(result_data) == 4
        assert result_data[0] == ["Name", "Age", "City"]

    async def test_read_empty_range(self, mcp_client, sample_spreadsheet_id):
        """Test reading from an empty range."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().get().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_read",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!Z1:Z10"
            }
        )

        result_data = json.loads(result.data)
        assert result_data == []


class TestSheetsWrite:
    """Tests for sheets_write tool."""

    async def test_write_data_success(self, mcp_client, sample_spreadsheet_id, sample_values):
        """Test writing data to a range."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().update().execute.return_value = {
            'updatedCells': 12
        }

        result = await client.call_tool(
            name="sheets_write",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:C4",
                "values": sample_values
            }
        )

        result_data = json.loads(result.data)
        assert result_data['updatedCells'] == 12

    async def test_write_with_formula(self, mcp_client, sample_spreadsheet_id):
        """Test writing formulas to cells."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().update().execute.return_value = {
            'updatedCells': 3
        }

        result = await client.call_tool(
            name="sheets_write",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!D1:D3",
                "values": [["=SUM(A1:C1)"], ["=AVERAGE(A2:C2)"], ["=COUNT(A3:C3)"]]
            }
        )

        result_data = json.loads(result.data)
        assert result_data['updatedCells'] == 3


class TestSheetsAppend:
    """Tests for sheets_append tool."""

    async def test_append_rows_success(self, mcp_client, sample_spreadsheet_id):
        """Test appending rows to sheet."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().append().execute.return_value = {
            'updates': {'updatedCells': 3}
        }

        result = await client.call_tool(
            name="sheets_append",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A:C",
                "values": [["David", "40", "Seattle"]]
            }
        )

        result_data = json.loads(result.data)
        assert result_data['updatedCells'] == 3

    async def test_append_multiple_rows(self, mcp_client, sample_spreadsheet_id):
        """Test appending multiple rows at once."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().append().execute.return_value = {
            'updates': {'updatedCells': 6}
        }

        result = await client.call_tool(
            name="sheets_append",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A:C",
                "values": [
                    ["Eve", "28", "Boston"],
                    ["Frank", "32", "Denver"]
                ]
            }
        )

        result_data = json.loads(result.data)
        assert result_data['updatedCells'] == 6


class TestSheetsGetSheetId:
    """Tests for sheets_get_sheet_id tool."""

    async def test_get_sheet_id_success(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test getting sheet ID for existing sheet."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().get().execute.return_value = {
            'sheets': [
                {'properties': {'title': 'Sheet1', 'sheetId': sample_sheet_id}},
                {'properties': {'title': 'Sheet2', 'sheetId': 1}}
            ]
        }

        result = await client.call_tool(
            name="sheets_get_sheet_id",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_name": "Sheet1"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['sheetId'] == sample_sheet_id
        assert result_data['sheetName'] == "Sheet1"

    async def test_get_sheet_id_not_found(self, mcp_client, sample_spreadsheet_id):
        """Test getting sheet ID for non-existent sheet."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().get().execute.return_value = {
            'sheets': [
                {'properties': {'title': 'Sheet1', 'sheetId': 0}}
            ]
        }

        result = await client.call_tool(
            name="sheets_get_sheet_id",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_name": "NonExistent"
            }
        )

        result_data = json.loads(result.data)
        assert 'error' in result_data
        assert 'not found' in result_data['error']


# ============================================================================
# ROW/CELL OPERATIONS TESTS
# ============================================================================

class TestSheetsDeleteRows:
    """Tests for sheets_delete_rows tool."""

    async def test_delete_single_row(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test deleting a single row."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_delete_rows",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1,
                "end_row": 2
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['deletedRows'] == 1

    async def test_delete_multiple_rows(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test deleting multiple rows."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_delete_rows",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1,
                "end_row": 5
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['deletedRows'] == 4


class TestSheetsInsertRows:
    """Tests for sheets_insert_rows tool."""

    async def test_insert_single_row(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test inserting a single row."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_insert_rows",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['insertedRows'] == 1

    async def test_insert_multiple_rows(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test inserting multiple rows."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_insert_rows",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 5,
                "num_rows": 10
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['insertedRows'] == 10


class TestSheetsClearRange:
    """Tests for sheets_clear_range tool."""

    async def test_clear_range_success(self, mcp_client, sample_spreadsheet_id):
        """Test clearing a range."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().clear().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_clear_range",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:C10"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert "Sheet1!A1:C10" in result_data['message']


# ============================================================================
# DATA OPERATIONS TESTS
# ============================================================================

class TestSheetsFindReplace:
    """Tests for sheets_find_replace tool."""

    async def test_find_replace_basic(self, mcp_client, sample_spreadsheet_id):
        """Test basic find and replace."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'findReplace': {'occurrencesChanged': 5}}]
        }

        result = await client.call_tool(
            name="sheets_find_replace",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "find": "old",
                "replacement": "new"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['replacements'] == 5

    async def test_find_replace_with_options(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test find and replace with match options."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'findReplace': {'occurrencesChanged': 2}}]
        }

        result = await client.call_tool(
            name="sheets_find_replace",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "find": "Test",
                "replacement": "Production",
                "sheet_id": sample_sheet_id,
                "match_case": True,
                "match_entire_cell": True
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['replacements'] == 2

    async def test_find_replace_no_matches(self, mcp_client, sample_spreadsheet_id):
        """Test find and replace with no matches."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'findReplace': {'occurrencesChanged': 0}}]
        }

        result = await client.call_tool(
            name="sheets_find_replace",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "find": "nonexistent",
                "replacement": "something"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['replacements'] == 0


class TestSheetsDuplicateSheet:
    """Tests for sheets_duplicate_sheet tool."""

    async def test_duplicate_sheet_success(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test duplicating a sheet."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{
                'duplicateSheet': {
                    'properties': {
                        'sheetId': 123,
                        'title': 'Sheet1 Copy'
                    }
                }
            }]
        }

        result = await client.call_tool(
            name="sheets_duplicate_sheet",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "source_sheet_id": sample_sheet_id,
                "new_sheet_name": "Sheet1 Copy"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['newSheetId'] == 123
        assert result_data['newSheetName'] == 'Sheet1 Copy'


class TestSheetsDeleteDuplicates:
    """Tests for sheets_delete_duplicates tool."""

    async def test_delete_duplicates_all_columns(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test deleting duplicates using all columns."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'deleteDuplicates': {'duplicatesRemovedCount': 3}}]
        }

        result = await client.call_tool(
            name="sheets_delete_duplicates",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 100,
                "start_col": 0,
                "end_col": 5
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['duplicatesRemoved'] == 3

    async def test_delete_duplicates_specific_columns(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test deleting duplicates using specific columns."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'deleteDuplicates': {'duplicatesRemovedCount': 5}}]
        }

        result = await client.call_tool(
            name="sheets_delete_duplicates",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 100,
                "start_col": 0,
                "end_col": 5,
                "comparison_columns": [0, 2]
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['duplicatesRemoved'] == 5


class TestSheetsTrimWhitespace:
    """Tests for sheets_trim_whitespace tool."""

    async def test_trim_whitespace_success(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test trimming whitespace from cells."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'trimWhitespace': {'cellsChangedCount': 15}}]
        }

        result = await client.call_tool(
            name="sheets_trim_whitespace",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 10,
                "start_col": 0,
                "end_col": 5
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert result_data['cellsTrimmed'] == 15


class TestSheetsMergeCells:
    """Tests for sheets_merge_cells tool."""

    async def test_merge_all_cells(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test merging all cells in a range."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_merge_cells",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 2,
                "start_col": 0,
                "end_col": 3
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert 'MERGE_ALL' in result_data['message']

    @pytest.mark.parametrize("merge_type", ["MERGE_ALL", "MERGE_COLUMNS", "MERGE_ROWS"])
    async def test_merge_types(self, mcp_client, sample_spreadsheet_id, sample_sheet_id, merge_type):
        """Test different merge types."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_merge_cells",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 2,
                "start_col": 0,
                "end_col": 3,
                "merge_type": merge_type
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert merge_type in result_data['message']


class TestSheetsCopyPaste:
    """Tests for sheets_copy_paste tool."""

    async def test_copy_paste_normal(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test normal copy/paste operation."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_copy_paste",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "source_sheet_id": sample_sheet_id,
                "source_start_row": 0,
                "source_end_row": 5,
                "source_start_col": 0,
                "source_end_col": 3,
                "dest_sheet_id": sample_sheet_id,
                "dest_start_row": 10,
                "dest_start_col": 0
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert 'NORMAL' in result_data['message']

    @pytest.mark.parametrize("paste_type", ["NORMAL", "VALUES", "FORMAT", "FORMULA"])
    async def test_paste_types(self, mcp_client, sample_spreadsheet_id, sample_sheet_id, paste_type):
        """Test different paste types."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_copy_paste",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "source_sheet_id": sample_sheet_id,
                "source_start_row": 0,
                "source_end_row": 5,
                "source_start_col": 0,
                "source_end_col": 3,
                "dest_sheet_id": sample_sheet_id,
                "dest_start_row": 10,
                "dest_start_col": 0,
                "paste_type": paste_type
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True
        assert paste_type in result_data['message']


# ============================================================================
# FORMATTING TESTS
# ============================================================================

class TestSheetsFormatCells:
    """Tests for sheets_format_cells tool."""

    async def test_format_bold(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test applying bold formatting."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_format_cells",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 1,
                "start_col": 0,
                "end_col": 3,
                "bold": True
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    async def test_format_multiple_options(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test applying multiple formatting options."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_format_cells",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 1,
                "start_col": 0,
                "end_col": 3,
                "bold": True,
                "italic": True,
                "font_size": 14,
                "bg_color": "#FFFF00",
                "text_color": "#0000FF"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True


class TestSheetsAddBorders:
    """Tests for sheets_add_borders tool."""

    async def test_add_borders_default(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test adding borders with default style."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_add_borders",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 10,
                "start_col": 0,
                "end_col": 5
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    @pytest.mark.parametrize("style", ["SOLID", "DASHED", "DOTTED"])
    async def test_border_styles(self, mcp_client, sample_spreadsheet_id, sample_sheet_id, style):
        """Test different border styles."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_add_borders",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 10,
                "start_col": 0,
                "end_col": 5,
                "style": style,
                "color": "#FF0000"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True


# ============================================================================
# CHARTS TESTS
# ============================================================================

class TestSheetsAddChart:
    """Tests for sheets_add_chart tool."""

    async def test_add_column_chart(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test adding a column chart."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_add_chart",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "chart_type": "COLUMN",
                "data_range": "Sheet1!A1:B10",
                "title": "Sales Chart"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    @pytest.mark.parametrize("chart_type", ["COLUMN", "BAR", "LINE", "PIE", "SCATTER"])
    async def test_chart_types(self, mcp_client, sample_spreadsheet_id, sample_sheet_id, chart_type):
        """Test different chart types."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_add_chart",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "chart_type": chart_type,
                "data_range": "Sheet1!A1:B10",
                "title": f"{chart_type} Chart"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    async def test_add_chart_with_position(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test adding chart at specific position."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_add_chart",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "chart_type": "LINE",
                "data_range": "Sheet1!A1:C20",
                "title": "Positioned Chart",
                "row": 5,
                "col": 10
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True


# ============================================================================
# VALIDATION & CONDITIONAL FORMATTING TESTS
# ============================================================================

class TestSheetsAddDropdown:
    """Tests for sheets_add_dropdown tool."""

    async def test_add_dropdown_basic(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test adding dropdown validation."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_add_dropdown",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1,
                "end_row": 10,
                "start_col": 2,
                "end_col": 3,
                "values": ["Yes", "No", "Maybe"]
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    async def test_add_dropdown_many_options(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test adding dropdown with many options."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        options = ["High", "Medium", "Low", "Critical", "None", "N/A"]

        result = await client.call_tool(
            name="sheets_add_dropdown",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 100,
                "start_col": 0,
                "end_col": 1,
                "values": options
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True


class TestSheetsConditionalFormat:
    """Tests for sheets_conditional_format tool."""

    async def test_conditional_format_greater_than(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test conditional formatting with NUMBER_GREATER."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_conditional_format",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1,
                "end_row": 100,
                "start_col": 1,
                "end_col": 2,
                "condition_type": "NUMBER_GREATER",
                "condition_value": "100",
                "bg_color": "#00FF00"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    @pytest.mark.parametrize("condition_type,value", [
        ("NUMBER_GREATER", "50"),
        ("NUMBER_LESS", "10"),
        ("TEXT_CONTAINS", "error"),
    ])
    async def test_conditional_format_types(self, mcp_client, sample_spreadsheet_id, sample_sheet_id, condition_type, value):
        """Test different conditional format types."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_conditional_format",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 50,
                "start_col": 0,
                "end_col": 5,
                "condition_type": condition_type,
                "condition_value": value,
                "bg_color": "#FF0000"
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True


class TestSheetsSortRange:
    """Tests for sheets_sort_range tool."""

    async def test_sort_ascending(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test sorting range in ascending order."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_sort_range",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1,
                "end_row": 100,
                "start_col": 0,
                "end_col": 5,
                "sort_column": 0,
                "ascending": True
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True

    async def test_sort_descending(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test sorting range in descending order."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        result = await client.call_tool(
            name="sheets_sort_range",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 1,
                "end_row": 100,
                "start_col": 0,
                "end_col": 5,
                "sort_column": 2,
                "ascending": False
            }
        )

        result_data = json.loads(result.data)
        assert result_data['success'] is True


# ============================================================================
# EDGE CASE AND ERROR HANDLING TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    async def test_empty_values_write(self, mcp_client, sample_spreadsheet_id):
        """Test writing empty values."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().update().execute.return_value = {
            'updatedCells': 0
        }

        result = await client.call_tool(
            name="sheets_write",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:A1",
                "values": [[""]]
            }
        )

        result_data = json.loads(result.data)
        assert 'updatedCells' in result_data

    async def test_large_range_read(self, mcp_client, sample_spreadsheet_id):
        """Test reading a large range."""
        client, mock_service = mcp_client

        # Generate large mock data
        large_data = [[f"Cell {i},{j}" for j in range(100)] for i in range(1000)]
        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': large_data
        }

        result = await client.call_tool(
            name="sheets_read",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:CV1000"
            }
        )

        result_data = json.loads(result.data)
        assert len(result_data) == 1000
        assert len(result_data[0]) == 100

    async def test_special_characters_in_values(self, mcp_client, sample_spreadsheet_id):
        """Test writing special characters."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().values().update().execute.return_value = {
            'updatedCells': 4
        }

        special_values = [
            ["Unicode: \u00e9\u00e8\u00f1"],
            ["Quotes: \"test\""],
            ["Newline: line1\nline2"],
            ["Tab: col1\tcol2"]
        ]

        result = await client.call_tool(
            name="sheets_write",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:A4",
                "values": special_values
            }
        )

        result_data = json.loads(result.data)
        assert result_data['updatedCells'] == 4


# ============================================================================
# INTEGRATION-LIKE TESTS (Multiple Operations)
# ============================================================================

class TestWorkflows:
    """Tests for common workflows combining multiple operations."""

    async def test_create_and_populate_workflow(self, mcp_client, sample_spreadsheet_id, sample_values):
        """Test workflow: create spreadsheet, write data, read back."""
        client, mock_service = mcp_client

        # Mock create
        mock_service.spreadsheets().create().execute.return_value = {
            'spreadsheetId': sample_spreadsheet_id,
            'spreadsheetUrl': f'https://docs.google.com/spreadsheets/d/{sample_spreadsheet_id}'
        }

        # Create spreadsheet
        create_result = await client.call_tool(
            name="sheets_create",
            arguments={"title": "Workflow Test"}
        )

        create_data = json.loads(create_result.data)
        assert create_data['spreadsheetId'] == sample_spreadsheet_id

        # Mock write
        mock_service.spreadsheets().values().update().execute.return_value = {
            'updatedCells': 12
        }

        # Write data
        write_result = await client.call_tool(
            name="sheets_write",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:C4",
                "values": sample_values
            }
        )

        write_data = json.loads(write_result.data)
        assert write_data['updatedCells'] == 12

        # Mock read
        mock_service.spreadsheets().values().get().execute.return_value = {
            'values': sample_values
        }

        # Read back
        read_result = await client.call_tool(
            name="sheets_read",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "range": "Sheet1!A1:C4"
            }
        )

        read_data = json.loads(read_result.data)
        assert read_data == sample_values

    async def test_format_and_chart_workflow(self, mcp_client, sample_spreadsheet_id, sample_sheet_id):
        """Test workflow: format header, add borders, create chart."""
        client, mock_service = mcp_client

        mock_service.spreadsheets().batchUpdate().execute.return_value = {}

        # Format header
        format_result = await client.call_tool(
            name="sheets_format_cells",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 1,
                "start_col": 0,
                "end_col": 5,
                "bold": True,
                "bg_color": "#4285F4",
                "text_color": "#FFFFFF"
            }
        )

        assert json.loads(format_result.data)['success'] is True

        # Add borders
        border_result = await client.call_tool(
            name="sheets_add_borders",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "start_row": 0,
                "end_row": 20,
                "start_col": 0,
                "end_col": 5
            }
        )

        assert json.loads(border_result.data)['success'] is True

        # Add chart
        chart_result = await client.call_tool(
            name="sheets_add_chart",
            arguments={
                "spreadsheet_id": sample_spreadsheet_id,
                "sheet_id": sample_sheet_id,
                "chart_type": "COLUMN",
                "data_range": "Sheet1!A1:B20",
                "title": "Data Visualization"
            }
        )

        assert json.loads(chart_result.data)['success'] is True
