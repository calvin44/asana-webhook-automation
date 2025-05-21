import gspread
from loguru import logger
from oauth2client.service_account import ServiceAccountCredentials

from utils.resources import G_SHEET_CREDENTIAL

# Define Google API scopes
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_sheet_client() -> gspread.Client | None:
    """
    Initializes and returns a Google Sheets API client using service account credentials.

    Returns:
        gspread.Client: An authorized client for accessing Google Sheets.
        None: If authorization fails.
    """
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            G_SHEET_CREDENTIAL, scope)
        client = gspread.authorize(creds)
        logger.info("✅ Google Sheets API client successfully initialized.")
        return client
    except Exception as e:  # pylint: disable=broad-except
        logger.error(f"❌ Failed to initialize Google Sheets API client: {e}")
        return None
