from pathlib import Path

import dagster as dg

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

defs = dg.load_from_defs_folder(path_within_project=_PROJECT_ROOT)

all_jobs = list(defs.jobs or [])
all_schedules = list(defs.schedules or [])
all_sensors = list(defs.sensors or [])
all_resources = dict(defs.resources or {})
