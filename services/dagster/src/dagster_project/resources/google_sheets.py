import base64
import json

from dagster import ConfigurableResource, EnvVar
import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsResource(ConfigurableResource):
    """Resource for interacting with Google Sheets API."""

    sheet_url: str = "PLACEHOLDER_SHEET_URL"
    credentials_json_b64: str = "PLACEHOLDER_GCP_CREDENTIALS_JSON_B64"

    def get_client(self) -> gspread.Client:
        """Get authenticated Google Sheets client."""
        if self.credentials_json_b64 == "PLACEHOLDER_GCP_CREDENTIALS_JSON_B64":
            raise ValueError(
                "Please configure GCP credentials. Set credentials_json_b64 to your base64-encoded service account JSON."
            )

        # Decode base64 and parse credentials
        credentials_json = base64.b64decode(self.credentials_json_b64).decode()
        creds_dict = json.loads(credentials_json)
        credentials = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return gspread.authorize(credentials)

    def get_sheet(self) -> gspread.Spreadsheet:
        """Get the spreadsheet object."""
        client = self.get_client()
        return client.open_by_url(self.sheet_url)

    def read_cell(self, worksheet_name: str, cell: str) -> str:
        """Read a single cell's value, stripped. Example: read_cell("Prompt", "B1")."""
        ws = self.get_sheet().worksheet(worksheet_name)
        return (ws.acell(cell).value or "").strip()

    def get_or_create_worksheet(
        self, title: str, rows: int = 1000, cols: int = 20
    ) -> gspread.Worksheet:
        """Fetch a worksheet, creating it if it does not exist."""
        sheet = self.get_sheet()
        try:
            return sheet.worksheet(title)
        except gspread.WorksheetNotFound:
            return sheet.add_worksheet(title=title, rows=rows, cols=cols)

    def append_row_with_header(
        self, worksheet_name: str, row: list[str], header: list[str]
    ) -> None:
        """Append a row to `worksheet_name`. Writes `header` first if the tab is empty."""
        ws = self.get_or_create_worksheet(worksheet_name)
        if not ws.get_all_values():
            ws.update("A1", [header], value_input_option="RAW")
        ws.append_row(row, value_input_option="RAW")

    def overwrite_with_rows(
        self, worksheet_name: str, header: list[str], rows: list[list[str]]
    ) -> None:
        """Clear `worksheet_name` and rewrite it with `header` followed by `rows`."""
        ws = self.get_or_create_worksheet(worksheet_name)
        ws.clear()
        ws.update("A1", [header, *rows], value_input_option="RAW")


# generate the base64-encoded credentials from the json file w/ `cat credentials.json | base64 | tr -d '\n'`
feature_flags_google_sheet = GoogleSheetsResource(
    sheet_url=EnvVar("FEATURE_FLAGS_GOOGLE_SHEET_URL"),
    credentials_json_b64=EnvVar("FEATURE_FLAGS_GOOGLE_SHEET_CREDENTIALS_JSON"),
)

llm_prompt_google_sheet = GoogleSheetsResource(
    sheet_url=EnvVar("LLM_PROMPT_GOOGLE_SHEET_URL"),
    credentials_json_b64=EnvVar("LLM_PROMPT_GOOGLE_SHEET_CREDENTIALS_JSON"),
)

# Example: Create a second instance for a different sheet if you had multiple jobs involving different sheets
# google_sheets_other = GoogleSheetsResource(
#     sheet_url=EnvVar("GOOGLE_SHEETS_OTHER_URL"),
#     credentials_json_b64=EnvVar("GOOGLE_SHEETS_CREDENTIALS_JSON"),
# )
