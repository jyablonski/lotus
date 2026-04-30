{{
    config(
        materialized='incremental',
        unique_key='topic_id'
    )
}}

with topics as (
    select * from {{ ref('stg_journal_topics') }}

    {% if is_incremental() %}
        where created_at > coalesce((select max(topic_created_at) from {{ this }}), '1970-01-01'::timestamp)
    {% endif %}
),

final as (
    select
        topic_id,
        journal_id,
        topic_name,
        subtopic_name,
        topic_confidence,
        ml_model_version as topic_model_version,
        created_at as topic_created_at
    from topics
)

select * from final
