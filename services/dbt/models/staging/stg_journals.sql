{{
    config(
        materialized='incremental',
        unique_key='journal_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'journals') }}

    {% if is_incremental() %}
    where modified_at > (select max(modified_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        id as journal_id,
        user_id,
        journal_text,
        mood_score,
        created_at,
        modified_at
    from source
)

select * from renamed
