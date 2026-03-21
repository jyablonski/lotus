"""Auto-imports every module in this package.

Drop a .py file in jobs/ that defines a JobDefinition or ScheduleDefinition
and it's automatically registered — no manual imports needed.
"""

import importlib
import pkgutil

# Import every submodule so their top-level objects are visible via vars(jobs)
for _importer, module_name, _ispkg in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_name}")
