"""SQL queries for ingestion state that cannot be expressed as DataFrame writes."""

SELECT_INGESTION_WATERMARK_FOR_UPDATE = """
SELECT watermark_at
FROM ingestion_watermarks
WHERE source_name = %s
FOR UPDATE
"""
