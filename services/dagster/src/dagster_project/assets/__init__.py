from .api_assets import *  # noqa

# Import dbt_assets - it now handles missing manifest gracefully
# If manifest doesn't exist, dbt_analytics will be None and won't be loaded as an asset
from .dbt_assets import *  # noqa
