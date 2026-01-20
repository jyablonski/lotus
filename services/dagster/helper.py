# debug_feast.py
from feast import FeatureStore
from datetime import datetime, timezone
import pandas as pd

store = FeatureStore(repo_path="feast_repo")

# Check config
print("Online store:", store.config.online_store)
print("Offline store:", store.config.offline_store)

# Get feature view
fv = store.get_feature_view("user_journal_summary_features")
print(f"Feature view online={fv.online}")

# Try materialization
start = datetime(2020, 1, 1, tzinfo=timezone.utc)
end = datetime.now(timezone.utc)

print(f"Materializing from {start} to {end}...")
store.materialize(
    feature_views=["user_journal_summary_features"],
    start_date=start,
    end_date=end,
)

# Check Redis directly
import redis

r = redis.Redis(host="redis", port=6379, db=0)
keys = r.keys("*")
print(f"Redis keys after: {len(keys)}")
print(f"Sample keys: {keys[:5]}")
