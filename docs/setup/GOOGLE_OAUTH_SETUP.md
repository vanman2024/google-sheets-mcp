# Google OAuth Setup Guide

This guide explains how to set up Google OAuth credentials for the Google Sheets MCP Server.

## Prerequisites

- Google account
- Access to Google Cloud Console

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "MCP Sheets Server")
5. Click "Create"

## Step 2: Enable the Google Sheets API

1. In the Cloud Console, go to **APIs & Services > Library**
2. Search for "Google Sheets API"
3. Click on it and click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Select **External** (or Internal if using Google Workspace)
3. Click **Create**
4. Fill in the required fields:
   - App name: "Google Sheets MCP"
   - User support email: Your email
   - Developer contact email: Your email
5. Click **Save and Continue**
6. On the Scopes page, click **Add or Remove Scopes**
7. Add: `https://www.googleapis.com/auth/spreadsheets`
8. Click **Save and Continue**
9. Add test users (your email address)
10. Click **Save and Continue**

## Step 4: Create OAuth Client ID

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Select **Desktop app** as the application type
4. Enter a name (e.g., "MCP Sheets Desktop")
5. Click **Create**
6. Click **Download JSON** to download the credentials
7. Rename the downloaded file to `gcp-oauth.keys.json`

## Step 5: Configure the MCP Server

1. Create the credentials directory:

```bash
mkdir -p ~/.config/mcp-gdrive
```

2. Move the credentials file:

```bash
mv ~/Downloads/gcp-oauth.keys.json ~/.config/mcp-gdrive/
```

3. Set the environment variable (optional, if not using default):

```bash
export GDRIVE_CREDS_DIR=~/.config/mcp-gdrive
```

## Step 6: First-time Authentication

1. Start the MCP server for the first time:

```bash
cd /path/to/google-sheets
./scripts/start.sh
```

2. The server will open a browser window for OAuth consent
3. Log in with your Google account
4. Grant the requested permissions
5. The server will save the token to `sheets-token.json`

## Troubleshooting

### "Access blocked: Authorization Error"

- Make sure you've added your email as a test user in the OAuth consent screen
- Verify the app is not published (keep it in "Testing" mode)

### "Invalid OAuth credentials"

- Re-download the OAuth credentials JSON from Cloud Console
- Make sure the file is named `gcp-oauth.keys.json`
- Verify the file is in the correct directory

### Token Expiration

Tokens automatically refresh. If you encounter persistent auth errors:

```bash
rm ~/.config/mcp-gdrive/sheets-token.json
```

Then restart the server to re-authenticate.

## Security Considerations

- Keep `gcp-oauth.keys.json` secure - it identifies your application
- Never commit credentials to version control
- The `sheets-token.json` contains your access tokens - keep it private
- Consider using a service account for production deployments

## Production Deployment

For production, consider:

1. **Publish the OAuth app**: Go through Google's verification process
2. **Service Account**: Use a service account for server-to-server communication
3. **Domain-wide delegation**: For Google Workspace organizations
