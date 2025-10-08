{{
    config(
        materialized='incremental',
        unique_key='sentiment_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'journal_sentiments') }}

    {% if is_incremental() %}
    where created_at > (select max(created_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        id as sentiment_id,
        journal_id,
        sentiment,
        confidence as sentiment_confidence,
        confidence_level,
        is_reliable,
        ml_model_version,
        all_scores as sentiment_scores_json,
        created_at
    from source
)

select * from renamed
