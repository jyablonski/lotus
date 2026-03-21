{{
    config(
        materialized='table'
    )
}}

with bets as (
    select * from {{ ref('fct_game_bets') }}
),

balances as (
    select * from {{ ref('stg_user_game_balances') }}
),

users as (
    select * from {{ ref('dim_users') }}
),

user_bet_metrics as (
    select
        user_id,
        count(*) as total_bets,
        count(case when is_win then 1 end) as total_wins,
        count(case when not is_win then 1 end) as total_losses,
        sum(bet_amount) as total_wagered,
        sum(bet_payout) as total_payouts,
        sum(net_result) as net_profit,
        avg(bet_amount) as avg_bet_amount,
        max(bet_payout) as biggest_payout,
        max(net_result) as biggest_win,
        min(net_result) as biggest_loss,

        -- zone breakdown
        count(case when bet_zone = '0' then 1 end) as green_bets,
        count(case when bet_zone = '1-7' then 1 end) as red_bets,
        count(case when bet_zone = '8-14' then 1 end) as black_bets,

        count(case when bet_zone = '0' and is_win then 1 end) as green_wins,
        count(case when bet_zone = '1-7' and is_win then 1 end) as red_wins,
        count(case when bet_zone = '8-14' and is_win then 1 end) as black_wins,

        min(bet_created_at) as first_bet_at,
        max(bet_created_at) as last_bet_at
    from bets
    group by user_id
),

user_bet_metrics_30d as (
    select
        user_id,
        count(*) as total_bets_30d,
        count(case when is_win then 1 end) as total_wins_30d,
        sum(bet_amount) as total_wagered_30d,
        sum(net_result) as net_profit_30d
    from bets
    where date_trunc('day', bet_created_at)::date >= current_date - interval '29 days'
    group by user_id
),

-- win/loss streaks
bet_streaks as (
    select
        user_id,
        is_win,
        bet_created_at,
        row_number() over (partition by user_id order by bet_created_at)
            - row_number() over (partition by user_id, is_win order by bet_created_at) as streak_group
    from bets
),

streak_lengths as (
    select
        user_id,
        is_win,
        count(*) as streak_length
    from bet_streaks
    group by user_id, is_win, streak_group
),

max_streaks as (
    select
        user_id,
        max(case when is_win then streak_length else 0 end) as longest_win_streak,
        max(case when not is_win then streak_length else 0 end) as longest_loss_streak
    from streak_lengths
    group by user_id
),

-- favorite zone (most bets placed)
zone_ranks as (
    select
        user_id,
        bet_zone,
        count(*) as zone_count,
        row_number() over (partition by user_id order by count(*) desc) as rn
    from bets
    group by user_id, bet_zone
),

favorite_zone as (
    select user_id, bet_zone as favorite_zone
    from zone_ranks
    where rn = 1
),

final as (
    select
        users.user_id,
        users.user_email,

        -- all-time metrics
        coalesce(m.total_bets, 0) as total_bets,
        coalesce(m.total_wins, 0) as total_wins,
        coalesce(m.total_losses, 0) as total_losses,
        round(
            coalesce(m.total_wins, 0)::numeric /
            nullif(coalesce(m.total_bets, 0), 0) * 100,
            2
        ) as win_rate,
        coalesce(m.total_wagered, 0) as total_wagered,
        coalesce(m.total_payouts, 0) as total_payouts,
        coalesce(m.net_profit, 0) as net_profit,
        round(m.avg_bet_amount::numeric, 2) as avg_bet_amount,
        coalesce(m.biggest_payout, 0) as biggest_payout,
        coalesce(m.biggest_win, 0) as biggest_win,
        coalesce(m.biggest_loss, 0) as biggest_loss,

        -- zone breakdown
        coalesce(m.green_bets, 0) as green_bets,
        coalesce(m.red_bets, 0) as red_bets,
        coalesce(m.black_bets, 0) as black_bets,
        coalesce(m.green_wins, 0) as green_wins,
        coalesce(m.red_wins, 0) as red_wins,
        coalesce(m.black_wins, 0) as black_wins,

        favorite_zone.favorite_zone,

        -- streaks
        coalesce(max_streaks.longest_win_streak, 0) as longest_win_streak,
        coalesce(max_streaks.longest_loss_streak, 0) as longest_loss_streak,

        -- 30d metrics
        coalesce(m30.total_bets_30d, 0) as total_bets_30d,
        coalesce(m30.total_wins_30d, 0) as total_wins_30d,
        round(
            coalesce(m30.total_wins_30d, 0)::numeric /
            nullif(coalesce(m30.total_bets_30d, 0), 0) * 100,
            2
        ) as win_rate_30d,
        coalesce(m30.total_wagered_30d, 0) as total_wagered_30d,
        coalesce(m30.net_profit_30d, 0) as net_profit_30d,

        -- balance
        balances.current_balance,

        -- timestamps
        m.first_bet_at,
        m.last_bet_at,

        case
            when m.last_bet_at is not null
            then current_date - date_trunc('day', m.last_bet_at)::date
            else null
        end as days_since_last_bet

    from users
    left join user_bet_metrics m on users.user_id = m.user_id
    left join user_bet_metrics_30d m30 on users.user_id = m30.user_id
    left join max_streaks on users.user_id = max_streaks.user_id
    left join favorite_zone on users.user_id = favorite_zone.user_id
    left join balances on users.user_id = balances.user_id
)

select * from final
