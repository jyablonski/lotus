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


# generate the base64-encoded credentials from the json file w/ `cat credentials.json | base64 | tr -d '\n'`
feature_flags_google_sheet = GoogleSheetsResource(
    sheet_url=EnvVar("FEATURE_FLAGS_GOOGLE_SHEET_URL"),
    credentials_json_b64=EnvVar("FEATURE_FLAGS_GOOGLE_SHEET_CREDENTIALS_JSON"),
)

# Example: Create a second instance for a different sheet if you had multiple jobs involving different sheets
# google_sheets_other = GoogleSheetsResource(
#     sheet_url=os.getenv("GOOGLE_SHEETS_OTHER_URL", "PLACEHOLDER_SHEET_URL_2"),
#     credentials_json=os.getenv(
#         "GOOGLE_SHEETS_CREDENTIALS_JSON", "PLACEHOLDER_GCP_CREDENTIALS_JSON"
#     ),
# )
