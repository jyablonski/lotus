from contextlib import contextmanager

from dagster import ConfigurableResource, EnvVar
import redis


class RedisResource(ConfigurableResource):
    """Redis resource for connecting to Redis instance."""

    host: str = "redis"
    port: int = 6379
    db: int = 0
    password: str | None = None
    decode_responses: bool = True

    @contextmanager
    def get_client(self):
        """Get a Redis client connection."""
        client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=self.decode_responses,
        )
        try:
            yield client
        finally:
            client.close()


# Default Redis connection instance
redis_conn = RedisResource(
    host=EnvVar("REDIS_HOST"),
    port=EnvVar.int("REDIS_PORT"),
    db=EnvVar.int("REDIS_DB"),
    password=EnvVar("REDIS_PASSWORD"),
    decode_responses=True,
)
