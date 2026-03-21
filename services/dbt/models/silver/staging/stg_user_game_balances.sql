{{
    config(
        materialized='incremental',
        unique_key='user_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'user_game_balances') }}

    {% if is_incremental() %}
    where modified_at > (select max(modified_at) from {{ this }})
    {% endif %}
),

renamed as (
    select
        user_id,
        balance as current_balance,
        created_at,
        modified_at
    from source
)

select * from renamed
