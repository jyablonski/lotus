{{
    config(
        materialized='table'
    )
}}

with users as (
    select * from {{ ref('stg_users') }}
),

final as (
    select
        user_id,
        user_email,
        user_role,
        oauth_provider,
        user_timezone,
        created_at as user_created_at,
        modified_at as user_modified_at
    from users
)

select * from final
