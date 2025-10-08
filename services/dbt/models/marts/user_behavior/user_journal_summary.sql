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

final as (
    select
        users.user_id,
        users.user_email,
        users.user_role,
        users.user_timezone,
        users.user_created_at,

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

        -- Calculated fields
        round(
            coalesce(user_metrics.positive_entries, 0)::numeric /
            nullif(coalesce(user_metrics.total_journals, 0), 0) * 100,
            2
        ) as positive_percentage,

        case
            when user_metrics.first_journal_at is not null
                and user_metrics.last_journal_at is not null
            then date_part('day', user_metrics.last_journal_at - user_metrics.first_journal_at) + 1
            else null
        end as days_since_first_journal,

        round(
            coalesce(user_metrics.total_journals, 0)::numeric /
            nullif(coalesce(user_metrics.active_days, 0), 0),
            2
        ) as journals_per_active_day

    from users
    left join user_metrics
        on users.user_id = user_metrics.user_id
)

select * from final
