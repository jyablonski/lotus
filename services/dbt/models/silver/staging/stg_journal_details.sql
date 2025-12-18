{{
    config(
        materialized='incremental',
        unique_key='journal_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'journal_details') }}

    {% if is_incremental() %}
    where modified_at > (select max(modified_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        journal_id,
        sentiment_score,
        mood_label,
        keywords,
        created_at,
        modified_at
    from source
)

select * from renamed
