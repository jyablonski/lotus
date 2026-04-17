"""Tests for GoogleSheetsResource."""

import base64
import json
from unittest.mock import MagicMock, patch

import gspread
import pytest

from dagster_project.resources.google_sheets import GoogleSheetsResource


@pytest.mark.unit
class TestGoogleSheetsResource:
    """Test the GoogleSheetsResource."""

    def test_google_sheets_resource_initialization_defaults(self):
        """Test resource initialization with defaults."""
        resource = GoogleSheetsResource()
        assert resource.sheet_url == "PLACEHOLDER_SHEET_URL"
        assert resource.credentials_json_b64 == "PLACEHOLDER_GCP_CREDENTIALS_JSON_B64"

    def test_google_sheets_resource_custom_config(self):
        """Test resource initialization with custom config."""
        test_url = "https://docs.google.com/spreadsheets/d/test123"
        test_creds_b64 = base64.b64encode(b'{"type": "service_account"}').decode()

        resource = GoogleSheetsResource(
            sheet_url=test_url,
            credentials_json_b64=test_creds_b64,
        )
        assert resource.sheet_url == test_url
        assert resource.credentials_json_b64 == test_creds_b64

    def test_get_client_raises_error_with_placeholder_credentials(self):
        """Test get_client raises error when credentials are placeholder."""
        resource = GoogleSheetsResource()

        with pytest.raises(
            ValueError,
            match="Please configure GCP credentials. Set credentials_json_b64",
        ):
            resource.get_client()

    @patch("dagster_project.resources.google_sheets.gspread.authorize")
    @patch(
        "dagster_project.resources.google_sheets.Credentials.from_service_account_info"
    )
    def test_get_client_success(self, mock_credentials, mock_authorize):
        """Test get_client successfully creates authenticated client."""
        # Create valid base64-encoded credentials
        creds_dict = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
        }
        creds_json = json.dumps(creds_dict)
        creds_b64 = base64.b64encode(creds_json.encode()).decode()

        mock_credential_obj = MagicMock()
        mock_credentials.return_value = mock_credential_obj

        mock_client = MagicMock()
        mock_authorize.return_value = mock_client

        resource = GoogleSheetsResource(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            credentials_json_b64=creds_b64,
        )

        client = resource.get_client()

        assert client == mock_client
        mock_credentials.assert_called_once()
        # Verify credentials were decoded and parsed correctly
        call_args = mock_credentials.call_args[0][0]
        assert call_args == creds_dict
        assert mock_credentials.call_args[1]["scopes"] == [
            "https://www.googleapis.com/auth/spreadsheets"
        ]
        mock_authorize.assert_called_once_with(mock_credential_obj)

    @patch("dagster_project.resources.google_sheets.gspread.authorize")
    @patch(
        "dagster_project.resources.google_sheets.Credentials.from_service_account_info"
    )
    def test_get_client_invalid_base64(self, mock_credentials, mock_authorize):
        """Test get_client raises error with invalid base64 credentials."""
        resource = GoogleSheetsResource(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            credentials_json_b64="invalid_base64!!!",
        )

        with pytest.raises(Exception):  # base64.b64decode will raise an exception
            resource.get_client()

    @patch("dagster_project.resources.google_sheets.gspread.authorize")
    @patch(
        "dagster_project.resources.google_sheets.Credentials.from_service_account_info"
    )
    def test_get_client_invalid_json(self, mock_credentials, mock_authorize):
        """Test get_client raises error with invalid JSON in credentials."""
        invalid_json_b64 = base64.b64encode(b"not valid json").decode()

        resource = GoogleSheetsResource(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            credentials_json_b64=invalid_json_b64,
        )

        with pytest.raises(json.JSONDecodeError):
            resource.get_client()

    @patch("dagster_project.resources.google_sheets.gspread.authorize")
    @patch(
        "dagster_project.resources.google_sheets.Credentials.from_service_account_info"
    )
    def test_get_sheet_success(self, mock_credentials, mock_authorize):
        """Test get_sheet successfully opens spreadsheet."""
        creds_dict = {
            "type": "service_account",
            "project_id": "test-project",
        }
        creds_json = json.dumps(creds_dict)
        creds_b64 = base64.b64encode(creds_json.encode()).decode()

        mock_credential_obj = MagicMock()
        mock_credentials.return_value = mock_credential_obj

        mock_client = MagicMock()
        mock_authorize.return_value = mock_client

        mock_sheet = MagicMock()
        mock_client.open_by_url.return_value = mock_sheet

        resource = GoogleSheetsResource(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            credentials_json_b64=creds_b64,
        )

        sheet = resource.get_sheet()

        assert sheet == mock_sheet
        mock_client.open_by_url.assert_called_once_with(
            "https://docs.google.com/spreadsheets/d/test123"
        )

    @patch("dagster_project.resources.google_sheets.gspread.authorize")
    @patch(
        "dagster_project.resources.google_sheets.Credentials.from_service_account_info"
    )
    def test_get_sheet_calls_get_client(self, mock_credentials, mock_authorize):
        """Test get_sheet calls get_client to authenticate."""
        creds_dict = {
            "type": "service_account",
            "project_id": "test-project",
        }
        creds_json = json.dumps(creds_dict)
        creds_b64 = base64.b64encode(creds_json.encode()).decode()

        mock_credential_obj = MagicMock()
        mock_credentials.return_value = mock_credential_obj

        mock_client = MagicMock()
        mock_authorize.return_value = mock_client

        mock_sheet = MagicMock()
        mock_client.open_by_url.return_value = mock_sheet

        resource = GoogleSheetsResource(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            credentials_json_b64=creds_b64,
        )

        resource.get_sheet()

        # Verify get_client was called (via authorize)
        mock_authorize.assert_called_once()
        # Verify get_sheet was called (via open_by_url)
        mock_client.open_by_url.assert_called_once()


@pytest.mark.unit
class TestGoogleSheetsResourceHelpers:
    """Test the reusable helpers on GoogleSheetsResource."""

    def _resource_with_mock_sheet(self, mock_sheet: MagicMock) -> GoogleSheetsResource:
        """Build a resource whose get_sheet() returns *mock_sheet*."""
        resource = GoogleSheetsResource(
            sheet_url="https://docs.google.com/spreadsheets/d/test123",
            credentials_json_b64="unused",
        )
        resource.get_sheet = MagicMock(return_value=mock_sheet)  # type: ignore[method-assign]
        return resource

    def test_read_cell_strips_value(self):
        mock_worksheet = MagicMock()
        mock_worksheet.acell.return_value.value = "  hello  "
        mock_sheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        assert resource.read_cell("Prompt", "B1") == "hello"
        mock_sheet.worksheet.assert_called_once_with("Prompt")
        mock_worksheet.acell.assert_called_once_with("B1")

    def test_read_cell_returns_empty_when_none(self):
        mock_worksheet = MagicMock()
        mock_worksheet.acell.return_value.value = None
        mock_sheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        assert resource.read_cell("Prompt", "B1") == ""

    def test_get_or_create_worksheet_returns_existing(self):
        mock_worksheet = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        result = resource.get_or_create_worksheet("Existing")

        assert result is mock_worksheet
        mock_sheet.worksheet.assert_called_once_with("Existing")
        mock_sheet.add_worksheet.assert_not_called()

    def test_get_or_create_worksheet_creates_when_missing(self):
        mock_sheet = MagicMock()
        mock_sheet.worksheet.side_effect = gspread.WorksheetNotFound("nope")
        new_worksheet = MagicMock()
        mock_sheet.add_worksheet.return_value = new_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        result = resource.get_or_create_worksheet("NewTab", rows=500, cols=10)

        assert result is new_worksheet
        mock_sheet.add_worksheet.assert_called_once_with(
            title="NewTab", rows=500, cols=10
        )

    def test_append_row_with_header_writes_header_when_empty(self):
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = []
        mock_sheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        resource.append_row_with_header("Responses", row=["1", "2"], header=["a", "b"])

        mock_worksheet.update.assert_called_once_with(
            "A1", [["a", "b"]], value_input_option="RAW"
        )
        mock_worksheet.append_row.assert_called_once_with(
            ["1", "2"], value_input_option="RAW"
        )

    def test_append_row_with_header_skips_header_when_not_empty(self):
        mock_worksheet = MagicMock()
        mock_worksheet.get_all_values.return_value = [["a", "b"], ["x", "y"]]
        mock_sheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        resource.append_row_with_header("Responses", row=["1", "2"], header=["a", "b"])

        mock_worksheet.update.assert_not_called()
        mock_worksheet.append_row.assert_called_once_with(
            ["1", "2"], value_input_option="RAW"
        )

    def test_overwrite_with_rows_clears_and_updates(self):
        mock_worksheet = MagicMock()
        mock_sheet = MagicMock()
        mock_sheet.worksheet.return_value = mock_worksheet
        resource = self._resource_with_mock_sheet(mock_sheet)

        resource.overwrite_with_rows(
            "Feature Flags",
            header=["a", "b"],
            rows=[["1", "2"], ["3", "4"]],
        )

        mock_worksheet.clear.assert_called_once()
        mock_worksheet.update.assert_called_once_with(
            "A1",
            [["a", "b"], ["1", "2"], ["3", "4"]],
            value_input_option="RAW",
        )
