{{
    config(
        materialized='incremental',
        unique_key='bet_id'
    )
}}

with bets as (
    select * from {{ ref('stg_user_game_bets') }}

    {% if is_incremental() %}
    where created_at > (select max(bet_created_at) from {{ this }})
    {% endif %}
),

final as (
    select
        bet_id,
        user_id,
        bet_zone,
        bet_amount,
        roll_result,
        bet_payout,

        -- derived fields
        case
            when roll_result = 0 then 'green'
            when roll_result between 1 and 7 then 'red'
            when roll_result between 8 and 14 then 'black'
        end as roll_color,

        case
            when bet_zone = '0' then 14
            else 2
        end as zone_multiplier,

        bet_payout > 0 as is_win,
        bet_payout - bet_amount as net_result,

        created_at as bet_created_at
    from bets
)

select * from final
