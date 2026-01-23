"""Tests for GoogleSheetsResource."""

import base64
import json
from unittest.mock import MagicMock, patch

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
