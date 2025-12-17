# all assets within this folder will automatically be pulled into the definitions.py file
# and be available in the Dagster UI
from .api_assets import *  # noqa

# Import dbt_assets - it now handles missing manifest gracefully
# If manifest doesn't exist, dbt_analytics will be None and won't be loaded as an asset
from .dbt_assets import *  # noqa

from .example_assets import *  # noqa
from .sales_data import *  # noqa
