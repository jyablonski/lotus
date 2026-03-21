from datetime import datetime, timezone
from io import BytesIO

import boto3
import polars as pl
from dagster import ConfigurableResource, EnvVar


class S3Resource(ConfigurableResource):
    bucket: str
    region: str = "us-east-1"
    endpoint_url: str = ""  # for LocalStack / MinIO in dev

    def _client(self):
        kwargs: dict = {"region_name": self.region}
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        return boto3.client("s3", **kwargs)

    @staticmethod
    def _partition_path(table_name: str, dt: datetime, extension: str) -> str:
        return (
            f"{table_name}"
            f"/year={dt.year}"
            f"/month={dt.month:02d}"
            f"/day={dt.day:02d}"
            f"/{table_name}.{extension}"
        )

    def write_parquet(
        self,
        df: pl.DataFrame,
        table_name: str,
        *,
        partition_dt: datetime | None = None,
    ) -> str:
        """Write a Polars DataFrame to S3 as Parquet, partitioned by year/month/day.

        Returns the full S3 key that was written.
        """
        dt = partition_dt or datetime.now(timezone.utc)
        key = self._partition_path(table_name, dt, "parquet")

        buf = BytesIO()
        df.write_parquet(buf)
        buf.seek(0)

        self._client().put_object(Bucket=self.bucket, Key=key, Body=buf.getvalue())
        return key

    def read_parquet(self, key: str) -> pl.DataFrame:
        """Read a single Parquet file from S3 into a Polars DataFrame."""
        resp = self._client().get_object(Bucket=self.bucket, Key=key)
        return pl.read_parquet(BytesIO(resp["Body"].read()))


s3_resource = S3Resource(
    bucket=EnvVar("DAGSTER_S3_BUCKET"),
    region=EnvVar("DAGSTER_S3_REGION"),
    endpoint_url=EnvVar("DAGSTER_S3_ENDPOINT_URL"),
)
