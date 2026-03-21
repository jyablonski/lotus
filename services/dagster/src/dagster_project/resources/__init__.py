from .example_api import ApiClientResource, api_client
from .google_sheets import GoogleSheetsResource, feature_flags_google_sheet
from .postgres import PostgresResource, postgres_conn
from .redis import RedisResource, redis_conn
from .feast import FeastResource, feast_store
from .s3 import S3Resource, s3_resource
from .slack import SlackResource, slack_resource

__all__ = [
    "ApiClientResource",
    "GoogleSheetsResource",
    "PostgresResource",
    "RedisResource",
    "FeastResource",
    "S3Resource",
    "SlackResource",
    "api_client",
    "feature_flags_google_sheet",
    "postgres_conn",
    "redis_conn",
    "feast_store",
    "s3_resource",
    "slack_resource",
]

# Explicit resource registry — every resource used by assets must be listed here.
# This avoids the fragility of auto-discovery (name collisions, accidentally
# picking up imported classes, etc.).  When you add a new resource, add an entry.
RESOURCES: dict = {
    "api_client": api_client,
    "feature_flags_google_sheet": feature_flags_google_sheet,
    "postgres_conn": postgres_conn,
    "redis_conn": redis_conn,
    "feast_store": feast_store,
    "s3_resource": s3_resource,
    "slack_resource": slack_resource,
}
