# Notes

```
uvx create-dagster@latest project dagster

cd dagster

uv sync
uv add polars boto3

dg scaffold defs dagster.asset assets.py

mkdir src/dagster/defs/data && touch src/dagster/defs/data/sample_data.csv

dg list defs
dg check defs
```
