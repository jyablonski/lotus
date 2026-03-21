{{
    config(
        materialized='table'
    )
}}

with topics as (
    select * from {{ ref('fct_journal_topics') }}
),

journal_entries as (
    select journal_id, user_id from {{ ref('fct_journal_entries') }}
),

users as (
    select * from {{ ref('dim_users') }}
),

-- join topics to users via journal entries
user_topics as (
    select
        journal_entries.user_id,
        topics.topic_id,
        topics.journal_id,
        topics.topic_name,
        topics.subtopic_name,
        topics.topic_confidence,
        topics.topic_model_version,
        topics.topic_created_at
    from topics
    inner join journal_entries
        on topics.journal_id = journal_entries.journal_id
),

-- all-time topic metrics per user
user_topic_metrics as (
    select
        user_id,
        count(*) as total_topic_assignments,
        count(distinct journal_id) as journals_with_topics,
        count(distinct topic_name) as distinct_topics,
        count(distinct subtopic_name) as distinct_subtopics,
        avg(topic_confidence) as avg_topic_confidence,
        min(topic_created_at) as first_topic_at,
        max(topic_created_at) as last_topic_at
    from user_topics
    group by user_id
),

-- 30d topic metrics
user_topic_metrics_30d as (
    select
        user_id,
        count(*) as total_topic_assignments_30d,
        count(distinct topic_name) as distinct_topics_30d,
        avg(topic_confidence) as avg_topic_confidence_30d
    from user_topics
    where date_trunc('day', topic_created_at)::date >= current_date - interval '29 days'
    group by user_id
),

-- dominant topic per user (most frequent)
topic_ranks as (
    select
        user_id,
        topic_name,
        count(*) as topic_count,
        avg(topic_confidence) as avg_confidence,
        row_number() over (partition by user_id order by count(*) desc, avg(topic_confidence) desc) as rn
    from user_topics
    group by user_id, topic_name
),

dominant_topic as (
    select
        user_id,
        topic_name as dominant_topic,
        topic_count as dominant_topic_count,
        round(avg_confidence::numeric, 4) as dominant_topic_avg_confidence
    from topic_ranks
    where rn = 1
),

-- top subtopic per user
subtopic_ranks as (
    select
        user_id,
        subtopic_name,
        count(*) as subtopic_count,
        row_number() over (partition by user_id order by count(*) desc) as rn
    from user_topics
    where subtopic_name is not null
    group by user_id, subtopic_name
),

dominant_subtopic as (
    select
        user_id,
        subtopic_name as dominant_subtopic
    from subtopic_ranks
    where rn = 1
),

final as (
    select
        users.user_id,
        users.user_email,

        -- all-time metrics
        coalesce(m.total_topic_assignments, 0) as total_topic_assignments,
        coalesce(m.journals_with_topics, 0) as journals_with_topics,
        coalesce(m.distinct_topics, 0) as distinct_topics,
        coalesce(m.distinct_subtopics, 0) as distinct_subtopics,
        round(m.avg_topic_confidence::numeric, 4) as avg_topic_confidence,

        -- dominant topic
        dominant_topic.dominant_topic,
        coalesce(dominant_topic.dominant_topic_count, 0) as dominant_topic_count,
        dominant_topic.dominant_topic_avg_confidence,
        dominant_subtopic.dominant_subtopic,

        -- 30d metrics
        coalesce(m30.total_topic_assignments_30d, 0) as total_topic_assignments_30d,
        coalesce(m30.distinct_topics_30d, 0) as distinct_topics_30d,
        round(m30.avg_topic_confidence_30d::numeric, 4) as avg_topic_confidence_30d,

        -- timestamps
        m.first_topic_at,
        m.last_topic_at

    from users
    left join user_topic_metrics m on users.user_id = m.user_id
    left join user_topic_metrics_30d m30 on users.user_id = m30.user_id
    left join dominant_topic on users.user_id = dominant_topic.user_id
    left join dominant_subtopic on users.user_id = dominant_subtopic.user_id
)

select * from final
