#!/usr/bin/env python3
"""Google Sheets MCP Server - FastMCP with formulas, formatting, charts, validation"""

import os
from typing import Annotated, Optional, List
from dotenv import load_dotenv
from fastmcp import FastMCP, Context
from pydantic import Field
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

mcp = FastMCP("Google Sheets")

_creds: Optional[Credentials] = None


def get_credentials():
    """Get or refresh Google OAuth credentials.

    Supports two modes:
    1. Environment variables (for deployment): GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
    2. File-based (for local dev): GDRIVE_CREDS_DIR with gcp-oauth.keys.json and sheets-token.json
    """
    global _creds
    if _creds:
        return _creds

    # Mode 1: Environment variables (for deployment)
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')

    if client_id and client_secret and refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        creds.refresh(Request())
        _creds = creds
        return creds

    # Mode 2: File-based (for local development)
    creds_dir = os.getenv('GDRIVE_CREDS_DIR', os.path.expanduser('~/.config/mcp-gdrive'))
    token_file = os.path.join(creds_dir, 'sheets-token.json')
    credentials_file = os.path.join(creds_dir, 'gcp-oauth.keys.json')

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(creds_dir, exist_ok=True)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    _creds = creds
    return creds


# ============================================================================
# BASIC DATA OPERATIONS
# ============================================================================

@mcp.tool()
async def sheets_create(
    title: Annotated[str, Field(description="Title of the new spreadsheet")],
    sheet_titles: Annotated[Optional[List[str]], Field(description="Optional list of sheet names to create")] = None,
    ctx: Context = None
) -> str:
    """Create a new spreadsheet"""
    if ctx:
        await ctx.info(f"Creating spreadsheet: {title}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    if not sheet_titles:
        sheet_titles = ["Sheet1"]

    spreadsheet = {
        'properties': {'title': title},
        'sheets': [{'properties': {'title': sheet}} for sheet in sheet_titles]
    }

    result = service.spreadsheets().create(body=spreadsheet).execute()

    if ctx:
        await ctx.info(f"Created spreadsheet: {result['spreadsheetId']}")

    return json.dumps({
        'spreadsheetId': result['spreadsheetId'],
        'spreadsheetUrl': result['spreadsheetUrl']
    }, indent=2)


@mcp.tool()
async def sheets_read(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    range: Annotated[str, Field(description="A1 notation range (e.g., 'Sheet1!A1:B10')")],
    ctx: Context = None
) -> str:
    """Read data from a range"""
    if ctx:
        await ctx.info(f"Reading range: {range}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range
    ).execute()
    return json.dumps(result.get('values', []), indent=2)


@mcp.tool()
async def sheets_write(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    range: Annotated[str, Field(description="A1 notation range (e.g., 'Sheet1!A1')")],
    values: Annotated[List[List[str]], Field(description="2D array of values to write (supports formulas like =SUM(A1:A10))")],
    ctx: Context = None
) -> str:
    """Write data (supports formulas like =SUM(A1:A10))"""
    if ctx:
        await ctx.info(f"Writing to range: {range}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueInputOption='USER_ENTERED',
        body={'values': values}
    ).execute()

    return json.dumps({'updatedCells': result.get('updatedCells')}, indent=2)


@mcp.tool()
async def sheets_append(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    range: Annotated[str, Field(description="A1 notation range to append to")],
    values: Annotated[List[List[str]], Field(description="2D array of values to append")],
    ctx: Context = None
) -> str:
    """Append rows to end of sheet"""
    if ctx:
        await ctx.info(f"Appending to range: {range}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueInputOption='USER_ENTERED',
        body={'values': values}
    ).execute()

    return json.dumps({'updatedCells': result.get('updates', {}).get('updatedCells')}, indent=2)


@mcp.tool()
async def sheets_get_sheet_id(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_name: Annotated[str, Field(description="Name of the sheet to find")],
    ctx: Context = None
) -> str:
    """Get the sheet ID for a given sheet name (needed for delete/insert operations)"""
    if ctx:
        await ctx.info(f"Getting sheet ID for: {sheet_name}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    for sheet in spreadsheet.get('sheets', []):
        if sheet['properties']['title'] == sheet_name:
            return json.dumps({
                'sheetId': sheet['properties']['sheetId'],
                'sheetName': sheet_name
            }, indent=2)

    return json.dumps({'error': f'Sheet "{sheet_name}" not found'}, indent=2)


@mcp.tool()
async def sheets_delete_rows(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID (use sheets_get_sheet_id to find)")],
    start_row: Annotated[int, Field(description="Start row index (0-based, row 2 in UI = index 1)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    ctx: Context = None
) -> str:
    """Delete rows from sheet. Row indices are 0-based."""
    if ctx:
        await ctx.info(f"Deleting rows {start_row} to {end_row}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'deleteDimension': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': start_row,
                'endIndex': end_row
            }
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    deleted_count = end_row - start_row
    return json.dumps({
        'success': True,
        'deletedRows': deleted_count,
        'message': f'Deleted {deleted_count} row(s)'
    }, indent=2)


@mcp.tool()
async def sheets_insert_rows(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Row index to insert at (0-based)", ge=0)],
    num_rows: Annotated[int, Field(description="Number of rows to insert", ge=1)] = 1,
    ctx: Context = None
) -> str:
    """Insert blank rows into sheet. Row indices are 0-based."""
    if ctx:
        await ctx.info(f"Inserting {num_rows} row(s) at index {start_row}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'insertDimension': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'ROWS',
                'startIndex': start_row,
                'endIndex': start_row + num_rows
            },
            'inheritFromBefore': False
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({
        'success': True,
        'insertedRows': num_rows,
        'message': f'Inserted {num_rows} row(s) at row {start_row + 1}'
    }, indent=2)


@mcp.tool()
async def sheets_clear_range(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    range: Annotated[str, Field(description="A1 notation range to clear (e.g., 'Sheet1!A1:B10')")],
    ctx: Context = None
) -> str:
    """Clear values from a range (keeps formatting)."""
    if ctx:
        await ctx.info(f"Clearing range: {range}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range
    ).execute()

    return json.dumps({
        'success': True,
        'message': f'Cleared range: {range}'
    }, indent=2)


@mcp.tool()
async def sheets_find_replace(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    find: Annotated[str, Field(description="Text to find")],
    replacement: Annotated[str, Field(description="Replacement text")],
    sheet_id: Annotated[Optional[int], Field(description="Optional sheet ID to limit search")] = None,
    match_case: Annotated[bool, Field(description="Case-sensitive matching")] = False,
    match_entire_cell: Annotated[bool, Field(description="Match entire cell contents only")] = False,
    ctx: Context = None
) -> str:
    """Find and replace text across sheet(s)."""
    if ctx:
        await ctx.info(f"Finding '{find}' and replacing with '{replacement}'")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    find_replace_spec = {
        'find': find,
        'replacement': replacement,
        'matchCase': match_case,
        'matchEntireCell': match_entire_cell
    }

    if sheet_id is not None:
        find_replace_spec['sheetId'] = sheet_id

    requests = [{'findReplace': find_replace_spec}]

    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    occurrences = result.get('replies', [{}])[0].get('findReplace', {}).get('occurrencesChanged', 0)

    return json.dumps({
        'success': True,
        'replacements': occurrences,
        'message': f'Replaced {occurrences} occurrence(s)'
    }, indent=2)


@mcp.tool()
async def sheets_duplicate_sheet(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    source_sheet_id: Annotated[int, Field(description="Sheet ID to duplicate")],
    new_sheet_name: Annotated[str, Field(description="Name for the new duplicated sheet")],
    ctx: Context = None
) -> str:
    """Duplicate an entire sheet within the same spreadsheet."""
    if ctx:
        await ctx.info(f"Duplicating sheet to: {new_sheet_name}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'duplicateSheet': {
            'sourceSheetId': source_sheet_id,
            'newSheetName': new_sheet_name
        }
    }]

    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    new_sheet = result.get('replies', [{}])[0].get('duplicateSheet', {}).get('properties', {})

    return json.dumps({
        'success': True,
        'newSheetId': new_sheet.get('sheetId'),
        'newSheetName': new_sheet.get('title'),
        'message': f'Duplicated sheet to "{new_sheet_name}"'
    }, indent=2)


@mcp.tool()
async def sheets_delete_duplicates(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    comparison_columns: Annotated[Optional[List[int]], Field(description="Column indices to check for duplicates")] = None,
    ctx: Context = None
) -> str:
    """Delete duplicate rows based on column values."""
    if ctx:
        await ctx.info("Deleting duplicate rows")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    delete_duplicates_spec = {
        'range': {
            'sheetId': sheet_id,
            'startRowIndex': start_row,
            'endRowIndex': end_row,
            'startColumnIndex': start_col,
            'endColumnIndex': end_col
        }
    }

    if comparison_columns:
        delete_duplicates_spec['comparisonColumns'] = [
            {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': col, 'endIndex': col + 1}
            for col in comparison_columns
        ]

    requests = [{'deleteDuplicates': delete_duplicates_spec}]

    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    duplicates = result.get('replies', [{}])[0].get('deleteDuplicates', {}).get('duplicatesRemovedCount', 0)

    return json.dumps({
        'success': True,
        'duplicatesRemoved': duplicates,
        'message': f'Removed {duplicates} duplicate row(s)'
    }, indent=2)


@mcp.tool()
async def sheets_trim_whitespace(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    ctx: Context = None
) -> str:
    """Trim leading/trailing whitespace from all cells in range."""
    if ctx:
        await ctx.info("Trimming whitespace from cells")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'trimWhitespace': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': start_col,
                'endColumnIndex': end_col
            }
        }
    }]

    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    cells_trimmed = result.get('replies', [{}])[0].get('trimWhitespace', {}).get('cellsChangedCount', 0)

    return json.dumps({
        'success': True,
        'cellsTrimmed': cells_trimmed,
        'message': f'Trimmed whitespace from {cells_trimmed} cell(s)'
    }, indent=2)


@mcp.tool()
async def sheets_merge_cells(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    merge_type: Annotated[str, Field(description="Merge type: MERGE_ALL, MERGE_COLUMNS, or MERGE_ROWS")] = 'MERGE_ALL',
    ctx: Context = None
) -> str:
    """Merge cells in range."""
    if ctx:
        await ctx.info(f"Merging cells with type: {merge_type}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'mergeCells': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': start_col,
                'endColumnIndex': end_col
            },
            'mergeType': merge_type
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({
        'success': True,
        'message': f'Merged cells with type: {merge_type}'
    }, indent=2)


@mcp.tool()
async def sheets_copy_paste(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    source_sheet_id: Annotated[int, Field(description="Source sheet ID")],
    source_start_row: Annotated[int, Field(description="Source start row (0-based)", ge=0)],
    source_end_row: Annotated[int, Field(description="Source end row (exclusive)", ge=1)],
    source_start_col: Annotated[int, Field(description="Source start column (0-based)", ge=0)],
    source_end_col: Annotated[int, Field(description="Source end column (exclusive)", ge=1)],
    dest_sheet_id: Annotated[int, Field(description="Destination sheet ID")],
    dest_start_row: Annotated[int, Field(description="Destination start row (0-based)", ge=0)],
    dest_start_col: Annotated[int, Field(description="Destination start column (0-based)", ge=0)],
    paste_type: Annotated[str, Field(description="Paste type: NORMAL, VALUES, FORMAT, FORMULA")] = 'NORMAL',
    ctx: Context = None
) -> str:
    """Copy and paste range."""
    if ctx:
        await ctx.info(f"Copying range with paste type: {paste_type}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'copyPaste': {
            'source': {
                'sheetId': source_sheet_id,
                'startRowIndex': source_start_row,
                'endRowIndex': source_end_row,
                'startColumnIndex': source_start_col,
                'endColumnIndex': source_end_col
            },
            'destination': {
                'sheetId': dest_sheet_id,
                'startRowIndex': dest_start_row,
                'startColumnIndex': dest_start_col
            },
            'pasteType': paste_type
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({
        'success': True,
        'message': f'Copied range with paste type: {paste_type}'
    }, indent=2)


# ============================================================================
# FORMATTING
# ============================================================================

@mcp.tool()
async def sheets_format_cells(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    bold: Annotated[Optional[bool], Field(description="Make text bold")] = None,
    italic: Annotated[Optional[bool], Field(description="Make text italic")] = None,
    font_size: Annotated[Optional[int], Field(description="Font size in points")] = None,
    bg_color: Annotated[Optional[str], Field(description="Background color as hex (e.g., #FF0000)")] = None,
    text_color: Annotated[Optional[str], Field(description="Text color as hex (e.g., #000000)")] = None,
    ctx: Context = None
) -> str:
    """Format cells (bold, italic, font size, colors)."""
    if ctx:
        await ctx.info("Formatting cells")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    cell_format = {}
    text_format = {}

    if bold is not None:
        text_format['bold'] = bold
    if italic is not None:
        text_format['italic'] = italic
    if font_size is not None:
        text_format['fontSize'] = font_size

    if text_color:
        color = text_color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) / 255 for i in (0, 2, 4))
        text_format['foregroundColor'] = {'red': r, 'green': g, 'blue': b}

    if text_format:
        cell_format['textFormat'] = text_format

    if bg_color:
        color = bg_color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) / 255 for i in (0, 2, 4))
        cell_format['backgroundColor'] = {'red': r, 'green': g, 'blue': b}

    requests = [{
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': start_col,
                'endColumnIndex': end_col
            },
            'cell': {'userEnteredFormat': cell_format},
            'fields': 'userEnteredFormat'
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({'success': True}, indent=2)


@mcp.tool()
async def sheets_add_borders(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    style: Annotated[str, Field(description="Border style: SOLID, DASHED, DOTTED")] = "SOLID",
    color: Annotated[str, Field(description="Border color as hex (e.g., #000000)")] = "#000000",
    ctx: Context = None
) -> str:
    """Add borders to cells."""
    if ctx:
        await ctx.info(f"Adding {style} borders")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    hex_color = color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))

    border_style = {
        'style': style,
        'color': {'red': r, 'green': g, 'blue': b}
    }

    requests = [{
        'updateBorders': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': start_col,
                'endColumnIndex': end_col
            },
            'top': border_style,
            'bottom': border_style,
            'left': border_style,
            'right': border_style,
            'innerHorizontal': border_style,
            'innerVertical': border_style
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({'success': True}, indent=2)


# ============================================================================
# CHARTS
# ============================================================================

@mcp.tool()
async def sheets_add_chart(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    chart_type: Annotated[str, Field(description="Chart type: COLUMN, BAR, LINE, PIE, SCATTER")],
    data_range: Annotated[str, Field(description="Data range in A1 notation (e.g., 'Sheet1!A1:B10')")],
    title: Annotated[str, Field(description="Chart title")],
    row: Annotated[int, Field(description="Anchor row for chart position", ge=0)] = 0,
    col: Annotated[int, Field(description="Anchor column for chart position", ge=0)] = 0,
    ctx: Context = None
) -> str:
    """Add a chart."""
    if ctx:
        await ctx.info(f"Adding {chart_type} chart: {title}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'addChart': {
            'chart': {
                'spec': {
                    'title': title,
                    'basicChart': {
                        'chartType': chart_type,
                        'legendPosition': 'RIGHT_LEGEND',
                        'axis': [
                            {'position': 'BOTTOM_AXIS'},
                            {'position': 'LEFT_AXIS'}
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{'sheetId': sheet_id, 'startRowIndex': 0, 'startColumnIndex': 0}]
                                }
                            }
                        }],
                        'series': [{
                            'series': {
                                'sourceRange': {
                                    'sources': [{'sheetId': sheet_id}]
                                }
                            }
                        }]
                    }
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': sheet_id,
                            'rowIndex': row,
                            'columnIndex': col
                        }
                    }
                }
            }
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({'success': True}, indent=2)


# ============================================================================
# DATA VALIDATION & CONDITIONAL FORMATTING
# ============================================================================

@mcp.tool()
async def sheets_add_dropdown(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    values: Annotated[List[str], Field(description="List of dropdown options")],
    ctx: Context = None
) -> str:
    """Add dropdown list validation to cells"""
    if ctx:
        await ctx.info(f"Adding dropdown with {len(values)} options")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'setDataValidation': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': start_col,
                'endColumnIndex': end_col
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_LIST',
                    'values': [{'userEnteredValue': v} for v in values]
                },
                'showCustomUi': True
            }
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({'success': True}, indent=2)


@mcp.tool()
async def sheets_conditional_format(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    condition_type: Annotated[str, Field(description="Condition type: NUMBER_GREATER, NUMBER_LESS, TEXT_CONTAINS, etc.")],
    condition_value: Annotated[str, Field(description="Value to compare against")],
    bg_color: Annotated[str, Field(description="Background color as hex (e.g., #00FF00)")],
    ctx: Context = None
) -> str:
    """Add conditional formatting."""
    if ctx:
        await ctx.info(f"Adding conditional format: {condition_type} {condition_value}")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    hex_color = bg_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))

    requests = [{
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{
                    'sheetId': sheet_id,
                    'startRowIndex': start_row,
                    'endRowIndex': end_row,
                    'startColumnIndex': start_col,
                    'endColumnIndex': end_col
                }],
                'booleanRule': {
                    'condition': {
                        'type': condition_type,
                        'values': [{'userEnteredValue': condition_value}]
                    },
                    'format': {
                        'backgroundColor': {'red': r, 'green': g, 'blue': b}
                    }
                }
            },
            'index': 0
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({'success': True}, indent=2)


# ============================================================================
# SORT & FILTER
# ============================================================================

@mcp.tool()
async def sheets_sort_range(
    spreadsheet_id: Annotated[str, Field(description="The spreadsheet ID")],
    sheet_id: Annotated[int, Field(description="The sheet ID")],
    start_row: Annotated[int, Field(description="Start row index (0-based)", ge=0)],
    end_row: Annotated[int, Field(description="End row index (exclusive)", ge=1)],
    start_col: Annotated[int, Field(description="Start column index (0-based)", ge=0)],
    end_col: Annotated[int, Field(description="End column index (exclusive)", ge=1)],
    sort_column: Annotated[int, Field(description="Column index to sort by (0-based)", ge=0)],
    ascending: Annotated[bool, Field(description="Sort in ascending order")] = True,
    ctx: Context = None
) -> str:
    """Sort a range by a column"""
    if ctx:
        await ctx.info(f"Sorting by column {sort_column} ({'ascending' if ascending else 'descending'})")

    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    requests = [{
        'sortRange': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': start_row,
                'endRowIndex': end_row,
                'startColumnIndex': start_col,
                'endColumnIndex': end_col
            },
            'sortSpecs': [{
                'dimensionIndex': sort_column,
                'sortOrder': 'ASCENDING' if ascending else 'DESCENDING'
            }]
        }
    }]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': requests}
    ).execute()

    return json.dumps({'success': True}, indent=2)


if __name__ == "__main__":
    mcp.run()
