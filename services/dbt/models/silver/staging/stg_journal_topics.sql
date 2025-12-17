{{
    config(
        materialized='incremental',
        unique_key='topic_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'journal_topics') }}

    {% if is_incremental() %}
    where created_at > (select max(created_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        id as topic_id,
        journal_id,
        topic_name,
        confidence as topic_confidence,
        ml_model_version,
        created_at
    from source
)

select * from renamed
