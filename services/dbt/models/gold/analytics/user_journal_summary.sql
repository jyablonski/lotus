{{
    config(
        materialized='table'
    )
}}

with journal_entries as (
    select * from {{ ref('fct_journal_entries') }}
),

users as (
    select * from {{ ref('dim_users') }}
),

user_metrics as (
    select
        journal_entries.user_id,
        count(distinct journal_entries.journal_id) as total_journals,
        count(distinct date_trunc('day', journal_entries.journal_created_at)) as active_days,
        avg(journal_entries.mood_score) as avg_mood_score,
        min(journal_entries.mood_score) as min_mood_score,
        max(journal_entries.mood_score) as max_mood_score,
        stddev(journal_entries.mood_score) as mood_score_stddev,
        count(case when journal_entries.sentiment = 'positive' then 1 end) as positive_entries,
        count(case when journal_entries.sentiment = 'negative' then 1 end) as negative_entries,
        count(case when journal_entries.sentiment = 'neutral' then 1 end) as neutral_entries,
        avg(journal_entries.sentiment_score) as avg_sentiment_score,
        avg(length(journal_entries.journal_text)) as avg_journal_length,
        min(journal_entries.journal_created_at) as first_journal_at,
        max(journal_entries.journal_created_at) as last_journal_at,
        max(journal_entries.journal_modified_at) as last_modified_at

    from journal_entries
    group by journal_entries.user_id
),

user_metrics_30d as (
    select
        journal_entries.user_id,
        count(distinct journal_entries.journal_id) as total_journals_30d,
        avg(journal_entries.mood_score) as avg_mood_score_30d,
        min(journal_entries.mood_score) as min_mood_score_30d,
        max(journal_entries.mood_score) as max_mood_score_30d
    from journal_entries
    where date_trunc('day', journal_entries.journal_created_at)::date >= current_date - interval '29 days'
    group by journal_entries.user_id
),

daily_entries as (
    select
        user_id,
        date_trunc('day', journal_created_at)::date as entry_date
    from journal_entries
    group by
        user_id,
        date_trunc('day', journal_created_at)::date
),

streaks as (
    select
        user_id,
        entry_date,
        entry_date - (row_number() over (partition by user_id order by entry_date))::int as streak_group
    from daily_entries
),

current_streaks as (
    select
        user_id,
        count(*) as streak_length,
        min(entry_date) as streak_start,
        max(entry_date) as streak_end
    from streaks
    group by user_id, streak_group
),

active_streaks as (
    select
        user_id,
        streak_length,
        streak_end,
        row_number() over (partition by user_id order by streak_end desc) as rn
    from current_streaks
    where
        streak_end::date >= current_date - interval '1 day'
),

max_current_streak as (
    select
        user_id,
        streak_length as daily_streak
    from active_streaks
    where rn = 1
),

final as (
    select
        users.user_id,
        users.user_email,
        users.user_role,
        users.user_timezone,
        users.user_created_at,

        -- All-time metrics
        coalesce(user_metrics.total_journals, 0) as total_journals,
        coalesce(user_metrics.active_days, 0) as active_days,

        user_metrics.avg_mood_score,
        user_metrics.min_mood_score,
        user_metrics.max_mood_score,
        user_metrics.mood_score_stddev,

        coalesce(user_metrics.positive_entries, 0) as positive_entries,
        coalesce(user_metrics.negative_entries, 0) as negative_entries,
        coalesce(user_metrics.neutral_entries, 0) as neutral_entries,
        user_metrics.avg_sentiment_score,

        user_metrics.avg_journal_length,

        user_metrics.first_journal_at,
        user_metrics.last_journal_at,
        user_metrics.last_modified_at,

        -- Last 30 days metrics
        coalesce(user_metrics_30d.total_journals_30d, 0) as total_journals_30d,
        user_metrics_30d.avg_mood_score_30d,
        user_metrics_30d.min_mood_score_30d,
        user_metrics_30d.max_mood_score_30d,

        -- Streak metrics
        coalesce(max_current_streak.daily_streak, 0) as daily_streak,

        -- Calculated fields
        round(
            coalesce(user_metrics.positive_entries, 0)::numeric /
            nullif(coalesce(user_metrics.total_journals, 0), 0) * 100,
            2
        ) as positive_percentage,

        case
            when user_metrics.last_journal_at is not null
            then current_date - date_trunc('day', user_metrics.last_journal_at)::date
            else null
        end as days_since_last_journal,

        case
            when user_metrics.first_journal_at is not null
                and user_metrics.last_journal_at is not null
            then date_trunc('day', user_metrics.last_journal_at)::date - date_trunc('day', user_metrics.first_journal_at)::date + 1
            else null
        end as days_between_first_and_last_journal,

        round(
            coalesce(user_metrics.total_journals, 0)::numeric /
            nullif(coalesce(user_metrics.active_days, 0), 0),
            2
        ) as journals_per_active_day

    from users
    left join user_metrics
        on users.user_id = user_metrics.user_id
    left join user_metrics_30d
        on users.user_id = user_metrics_30d.user_id
    left join max_current_streak
        on users.user_id = max_current_streak.user_id
)

select * from final
