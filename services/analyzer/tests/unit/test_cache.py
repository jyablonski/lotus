from src.routers.v1.cache import invalidate_cache


def test_cache_invalidation_endpoint():
    response = invalidate_cache()

    assert response == {
        "message": "Cache invalidation requested",
        "status": "success",
    }
