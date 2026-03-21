{{
    config(
        materialized='incremental',
        unique_key='bet_id'
    )
}}

with source as (
    select *
    from {{ source('application_db', 'user_game_bets') }}

    {% if is_incremental() %}
    where created_at > coalesce((select max(created_at) from {{ this }}), '1970-01-01'::timestamp)
    {% endif %}
),

renamed as (
    select
        id as bet_id,
        user_id,
        zone as bet_zone,
        amount as bet_amount,
        roll_result,
        payout as bet_payout,
        created_at
    from source
)

select * from renamed
