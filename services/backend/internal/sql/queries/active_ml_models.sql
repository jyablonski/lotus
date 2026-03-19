-- name: GetActiveMLModel :one
SELECT is_enabled FROM active_ml_models WHERE ml_model = $1;
