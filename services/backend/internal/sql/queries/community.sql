-- name: UpsertJournalCommunityProjection :one
INSERT INTO source.journal_community_projections (
    journal_id,
    user_id,
    eligible_for_community,
    entry_local_date,
    primary_mood,
    primary_sentiment,
    theme_names,
    country_code,
    region_code,
    analysis_version
) VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9,
    $10
)
ON CONFLICT (journal_id) DO UPDATE
SET
    user_id = EXCLUDED.user_id,
    eligible_for_community = EXCLUDED.eligible_for_community,
    entry_local_date = EXCLUDED.entry_local_date,
    primary_mood = EXCLUDED.primary_mood,
    primary_sentiment = EXCLUDED.primary_sentiment,
    theme_names = EXCLUDED.theme_names,
    country_code = EXCLUDED.country_code,
    region_code = EXCLUDED.region_code,
    analysis_version = EXCLUDED.analysis_version,
    updated_at = NOW()
RETURNING *;

-- name: DeleteCommunityThemeRollupsForBucket :exec
DELETE FROM source.community_theme_rollups
WHERE bucket_date = $1 AND time_grain = $2;

-- name: DeleteCommunityMoodRollupsForBucket :exec
DELETE FROM source.community_mood_rollups
WHERE bucket_date = $1 AND time_grain = $2;

-- name: DeleteCommunitySummariesForBucket :exec
DELETE FROM source.community_summaries
WHERE bucket_date = $1 AND time_grain = $2;

-- name: DeleteCommunityPromptSetsForBucket :exec
DELETE FROM source.community_prompt_sets
WHERE bucket_date = $1 AND time_grain = $2;

-- name: UpsertCommunityThemeRollup :one
INSERT INTO source.community_theme_rollups (
    bucket_date,
    time_grain,
    scope_type,
    scope_value,
    theme_name,
    entry_count,
    unique_user_count,
    rank,
    delta_vs_previous
) VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9
)
ON CONFLICT (bucket_date, time_grain, scope_type, scope_value, theme_name) DO UPDATE
SET
    entry_count = EXCLUDED.entry_count,
    unique_user_count = EXCLUDED.unique_user_count,
    rank = EXCLUDED.rank,
    delta_vs_previous = EXCLUDED.delta_vs_previous,
    updated_at = NOW()
RETURNING *;

-- name: UpsertCommunityMoodRollup :one
INSERT INTO source.community_mood_rollups (
    bucket_date,
    time_grain,
    scope_type,
    scope_value,
    mood_name,
    entry_count,
    unique_user_count,
    rank,
    delta_vs_previous
) VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
    $9
)
ON CONFLICT (bucket_date, time_grain, scope_type, scope_value, mood_name) DO UPDATE
SET
    entry_count = EXCLUDED.entry_count,
    unique_user_count = EXCLUDED.unique_user_count,
    rank = EXCLUDED.rank,
    delta_vs_previous = EXCLUDED.delta_vs_previous,
    updated_at = NOW()
RETURNING *;

-- name: UpsertCommunitySummary :one
INSERT INTO source.community_summaries (
    bucket_date,
    time_grain,
    scope_type,
    scope_value,
    summary_text,
    source_theme_names,
    source_mood_names,
    generation_method
) VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8
)
ON CONFLICT (bucket_date, time_grain, scope_type, scope_value) DO UPDATE
SET
    summary_text = EXCLUDED.summary_text,
    source_theme_names = EXCLUDED.source_theme_names,
    source_mood_names = EXCLUDED.source_mood_names,
    generation_method = EXCLUDED.generation_method,
    updated_at = NOW()
RETURNING *;

-- name: UpsertCommunityPromptSet :one
INSERT INTO source.community_prompt_sets (
    bucket_date,
    time_grain,
    scope_type,
    scope_value,
    prompt_set_json,
    source_theme_names,
    source_mood_names,
    generation_method
) VALUES (
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8
)
ON CONFLICT (bucket_date, time_grain, scope_type, scope_value) DO UPDATE
SET
    prompt_set_json = EXCLUDED.prompt_set_json,
    source_theme_names = EXCLUDED.source_theme_names,
    source_mood_names = EXCLUDED.source_mood_names,
    generation_method = EXCLUDED.generation_method,
    updated_at = NOW()
RETURNING *;

-- name: ListEligibleCommunityProjectionsByDateRange :many
SELECT *
FROM source.journal_community_projections
WHERE eligible_for_community = TRUE
  AND entry_local_date >= $1
  AND entry_local_date <= $2
ORDER BY entry_local_date, journal_id;

-- name: GetCommunityProjectionSourceByJournalId :one
SELECT
    j.id AS journal_id,
    j.user_id,
    j.created_at,
    j.mood_score,
    u.timezone,
    u.community_insights_opt_in,
    u.community_location_opt_in,
    u.community_country_code,
    u.community_region_code,
    sentiment.sentiment AS primary_sentiment,
    sentiment.ml_model_version AS sentiment_model_version,
    COALESCE(topics.topic_names, ARRAY[]::text[]) AS theme_names,
    topics.topic_model_version
FROM source.journals j
JOIN source.users u ON u.id = j.user_id
LEFT JOIN LATERAL (
    SELECT js.sentiment, js.ml_model_version
    FROM source.journal_sentiments js
    WHERE js.journal_id = j.id AND js.is_reliable = TRUE
    ORDER BY js.created_at DESC, js.id DESC
    LIMIT 1
) sentiment ON TRUE
LEFT JOIN LATERAL (
    SELECT
        ARRAY_AGG(jt.topic_name ORDER BY jt.confidence DESC, jt.topic_name ASC) AS topic_names,
        MAX(jt.ml_model_version) AS topic_model_version
    FROM source.journal_topics jt
    WHERE jt.journal_id = j.id
) topics ON TRUE
WHERE j.id = $1;

-- name: ListCommunityRepairJournalIds :many
SELECT DISTINCT j.id
FROM source.journals j
JOIN source.users u ON u.id = j.user_id
WHERE
    j.created_at >= $1
    OR j.modified_at >= $1
    OR u.modified_at >= $1
ORDER BY j.id;

-- name: GetJournalCommunityProjectionByJournalId :one
SELECT * FROM source.journal_community_projections
WHERE journal_id = $1;

-- name: GetThemeRollupsByBucketAndScope :many
SELECT * FROM source.community_theme_rollups
WHERE
    bucket_date = $1
    AND time_grain = $2
    AND scope_type = $3
    AND scope_value = $4
ORDER BY rank ASC, theme_name ASC;

-- name: GetMoodRollupsByBucketAndScope :many
SELECT * FROM source.community_mood_rollups
WHERE
    bucket_date = $1
    AND time_grain = $2
    AND scope_type = $3
    AND scope_value = $4
ORDER BY rank ASC, mood_name ASC;

-- name: GetCommunitySummaryByBucketAndScope :one
SELECT * FROM source.community_summaries
WHERE
    bucket_date = $1
    AND time_grain = $2
    AND scope_type = $3
    AND scope_value = $4;

-- name: GetCommunityPromptSetByBucketAndScope :one
SELECT * FROM source.community_prompt_sets
WHERE
    bucket_date = $1
    AND time_grain = $2
    AND scope_type = $3
    AND scope_value = $4;
