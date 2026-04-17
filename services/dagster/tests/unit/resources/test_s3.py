"""Tests for S3Resource."""

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from dagster_project.resources import S3Resource


@pytest.mark.unit
class TestS3Resource:
    def _resource(self, **overrides) -> S3Resource:
        defaults = {"bucket": "test-bucket", "region": "us-east-1", "endpoint_url": ""}
        return S3Resource(**(defaults | overrides))

    def test_initialization_defaults(self):
        resource = S3Resource(bucket="my-bucket")
        assert resource.bucket == "my-bucket"
        assert resource.region == "us-east-1"
        assert resource.endpoint_url == ""

    def test_initialization_custom(self):
        resource = self._resource(
            bucket="custom", region="eu-west-1", endpoint_url="http://localhost:4566"
        )
        assert resource.bucket == "custom"
        assert resource.region == "eu-west-1"
        assert resource.endpoint_url == "http://localhost:4566"

    def test_partition_path(self):
        dt = datetime(2026, 3, 21, 14, 30, 0, tzinfo=timezone.utc)
        path = S3Resource._partition_path("users", dt, "parquet")
        assert path == "users/year=2026/month=03/day=21/users.parquet"

    def test_partition_path_single_digit_month_day(self):
        dt = datetime(2025, 1, 5, tzinfo=timezone.utc)
        path = S3Resource._partition_path("events", dt, "parquet")
        assert path == "events/year=2025/month=01/day=05/events.parquet"

    @patch("dagster_project.resources.s3.boto3.client")
    def test_write_parquet(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        resource = self._resource()
        df = pl.DataFrame({"id": [1, 2], "name": ["alice", "bob"]})
        dt = datetime(2026, 3, 21, tzinfo=timezone.utc)

        key = resource.write_parquet(df, "users", partition_dt=dt)

        assert key == "users/year=2026/month=03/day=21/users.parquet"
        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == key

        written_df = pl.read_parquet(BytesIO(call_kwargs["Body"]))
        assert written_df.shape == (2, 2)
        assert written_df["id"].to_list() == [1, 2]

    @patch("dagster_project.resources.s3.boto3.client")
    def test_write_parquet_uses_utc_now_when_no_dt(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        resource = self._resource()
        df = pl.DataFrame({"x": [1]})

        key = resource.write_parquet(df, "events")

        now = datetime.now(timezone.utc)
        assert f"year={now.year}" in key
        assert f"month={now.month:02d}" in key
        assert f"day={now.day:02d}" in key

    @patch("dagster_project.resources.s3.boto3.client")
    def test_read_parquet(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        original_df = pl.DataFrame({"id": [1, 2], "val": [10.0, 20.0]})
        buf = BytesIO()
        original_df.write_parquet(buf)
        parquet_bytes = buf.getvalue()

        mock_body = MagicMock()
        mock_body.read.return_value = parquet_bytes
        mock_s3.get_object.return_value = {"Body": mock_body}

        resource = self._resource()
        result = resource.read_parquet("users/year=2026/month=03/day=21/users.parquet")

        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="users/year=2026/month=03/day=21/users.parquet",
        )
        assert result.shape == (2, 2)
        assert result["id"].to_list() == [1, 2]

    @patch("dagster_project.resources.s3.boto3.client")
    def test_endpoint_url_passed_to_client(self, mock_boto_client):
        resource = self._resource(endpoint_url="http://localhost:4566")
        resource._client()
        mock_boto_client.assert_called_once_with(
            "s3", region_name="us-east-1", endpoint_url="http://localhost:4566"
        )

    @patch("dagster_project.resources.s3.boto3.client")
    def test_no_endpoint_url_omitted_from_client(self, mock_boto_client):
        resource = self._resource()
        resource._client()
        mock_boto_client.assert_called_once_with("s3", region_name="us-east-1")
