{{
    config(
        materialized='incremental',
        unique_key='journal_id'
    )
}}

with journals as (
    select * from {{ ref('stg_journals') }}

    {% if is_incremental() %}
        where modified_at > coalesce((select max(journal_modified_at) from {{ this }}), '1970-01-01'::timestamp)
    {% endif %}
),

journal_details as (
    select * from {{ ref('stg_journal_details') }}

    {% if is_incremental() %}
        where modified_at > coalesce((select max(journal_modified_at) from {{ this }}), '1970-01-01'::timestamp)
    {% endif %}
),

sentiments as (
    select
        *,
        row_number() over (partition by journal_id order by created_at desc) as rn
    from {{ ref('stg_journal_sentiments') }}

    {% if is_incremental() %}
        where journal_id in (select journal_id from journals)
    {% endif %}
),

topic_counts as (
    select
        journal_id,
        count(*) as topic_count
    from {{ ref('stg_journal_topics') }}
    group by journal_id
),

joined as (
    select
        journals.journal_id,
        journals.user_id,
        journals.journal_text,
        journals.mood_score,
        journal_details.sentiment_score,
        journal_details.mood_label,
        journal_details.keywords,
        sentiments.sentiment,
        sentiments.sentiment_confidence,
        sentiments.confidence_level,
        sentiments.is_reliable as sentiment_is_reliable,
        sentiments.ml_model_version as sentiment_model_version,
        sentiments.sentiment_scores_json,
        coalesce(topic_counts.topic_count, 0) as topic_count,
        journals.created_at as journal_created_at,
        journals.modified_at as journal_modified_at
    from journals
    left join journal_details
        on journals.journal_id = journal_details.journal_id
    left join sentiments
        on
            journals.journal_id = sentiments.journal_id
            and sentiments.rn = 1
    left join topic_counts
        on journals.journal_id = topic_counts.journal_id
)

select * from joined
