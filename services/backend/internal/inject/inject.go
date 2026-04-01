// Package inject provides context-based dependency injection helpers.
//
// Each dependency has a WithX function that returns a new context carrying
// the value, and an XFrom function that extracts it. LoggerFrom falls back
// to slog.Default() when no logger is set; DBFrom, HTTPClientFrom,
// PgxPoolFrom, RiverClientFrom, and SQLDBFrom panic if their value is absent
// (indicating a programming error — the injector interceptor should always set them).
package inject

import (
	"context"
	"database/sql"
	"log/slog"
	"net/http"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/redis/go-redis/v9"
	"github.com/riverqueue/river"
)

// HTTPDoer is the interface for making HTTP requests. The existing
// mocks.HTTPClientMock satisfies this via Go structural typing.
type HTTPDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

// unexported key types prevent collisions with other packages.
type ctxKey int

const (
	dbKey ctxKey = iota
	sqlDBKey
	loggerKey
	httpClientKey
	analyzerURLKey
	analyzerAPIKeyKey
	pgxPoolKey
	redisClientKey
	riverClientKey
)

// --- DB (db.Querier) ---

func WithDB(ctx context.Context, q db.Querier) context.Context {
	return context.WithValue(ctx, dbKey, q)
}

func DBFrom(ctx context.Context) db.Querier {
	q, ok := ctx.Value(dbKey).(db.Querier)
	if !ok || q == nil {
		panic("inject: db.Querier not found in context (missing injector interceptor?)")
	}
	return q
}

// --- *sql.DB (same pool as DBFrom; for transactional workflows) ---
//
// DBFrom exposes the default sqlc Querier bound to the connection pool. Most
// handlers only need that. Some flows require a multi-statement ACID
// transaction (BeginTx → db.New(tx) → Commit/Rollback); those need the
// underlying *sql.DB to start the transaction. Use SQLDBFrom for that —
// e.g. admin invoice creation, where partial writes on failure would be
// unacceptable.
//
// WithSQLDB must be set alongside WithDB on every request (see main); SQLDBFrom
// panics if absent, same as DBFrom.

func WithSQLDB(ctx context.Context, db *sql.DB) context.Context {
	return context.WithValue(ctx, sqlDBKey, db)
}

func SQLDBFrom(ctx context.Context) *sql.DB {
	d, ok := ctx.Value(sqlDBKey).(*sql.DB)
	if !ok || d == nil {
		panic("inject: *sql.DB not found in context (missing injector interceptor?)")
	}
	return d
}

// --- Logger ---

func WithLogger(ctx context.Context, l *slog.Logger) context.Context {
	return context.WithValue(ctx, loggerKey, l)
}

func LoggerFrom(ctx context.Context) *slog.Logger {
	if l, ok := ctx.Value(loggerKey).(*slog.Logger); ok && l != nil {
		return l
	}
	return slog.Default()
}

// --- HTTP Client ---

func WithHTTPClient(ctx context.Context, c HTTPDoer) context.Context {
	return context.WithValue(ctx, httpClientKey, c)
}

func HTTPClientFrom(ctx context.Context) HTTPDoer {
	c, ok := ctx.Value(httpClientKey).(HTTPDoer)
	if !ok || c == nil {
		panic("inject: HTTPDoer not found in context (missing injector interceptor?)")
	}
	return c
}

// --- Analyzer URL ---

func WithAnalyzerURL(ctx context.Context, url string) context.Context {
	return context.WithValue(ctx, analyzerURLKey, url)
}

func AnalyzerURLFrom(ctx context.Context) string {
	if s, ok := ctx.Value(analyzerURLKey).(string); ok {
		return s
	}
	return ""
}

// --- Analyzer API Key ---

func WithAnalyzerAPIKey(ctx context.Context, key string) context.Context {
	return context.WithValue(ctx, analyzerAPIKeyKey, key)
}

func AnalyzerAPIKeyFrom(ctx context.Context) string {
	if s, ok := ctx.Value(analyzerAPIKeyKey).(string); ok {
		return s
	}
	return ""
}

// --- pgxpool.Pool ---

func WithPgxPool(ctx context.Context, p *pgxpool.Pool) context.Context {
	return context.WithValue(ctx, pgxPoolKey, p)
}

func PgxPoolFrom(ctx context.Context) *pgxpool.Pool {
	p, ok := ctx.Value(pgxPoolKey).(*pgxpool.Pool)
	if !ok || p == nil {
		panic("inject: *pgxpool.Pool not found in context (missing injector interceptor?)")
	}
	return p
}

// --- Redis client ---

func WithRedisClient(ctx context.Context, c *redis.Client) context.Context {
	return context.WithValue(ctx, redisClientKey, c)
}

func RedisClientFrom(ctx context.Context) *redis.Client {
	c, ok := ctx.Value(redisClientKey).(*redis.Client)
	if !ok || c == nil {
		panic("inject: *redis.Client not found in context (missing injector interceptor?)")
	}
	return c
}

// --- River client ---

func WithRiverClient(ctx context.Context, c *river.Client[pgx.Tx]) context.Context {
	return context.WithValue(ctx, riverClientKey, c)
}

func RiverClientFrom(ctx context.Context) *river.Client[pgx.Tx] {
	c, ok := ctx.Value(riverClientKey).(*river.Client[pgx.Tx])
	if !ok || c == nil {
		panic("inject: *river.Client not found in context (missing injector interceptor?)")
	}
	return c
}
