{{
    config(
        materialized='incremental',
        unique_key='user_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'users') }}

    {% if is_incremental() %}
    where modified_at > (select max(modified_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        id as user_id,
        email as user_email,
        password as password_hash,
        salt as password_salt,
        oauth_provider,
        role as user_role,
        timezone as user_timezone,
        created_at,
        modified_at
    from source
)

select * from renamed
