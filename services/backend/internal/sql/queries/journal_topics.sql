-- name: GetTopicsByJournalIds :many
SELECT journal_id, topic_name
FROM source.journal_topics
WHERE journal_id = ANY($1::int[])
ORDER BY journal_id, confidence DESC;
