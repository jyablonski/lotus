// Package inject provides context-based dependency injection helpers.
//
// Each dependency has a WithX function that returns a new context carrying
// the value, and an XFrom function that extracts it. LoggerFrom falls back
// to slog.Default() when no logger is set; DBFrom, HTTPClientFrom,
// PgxPoolFrom, and RiverClientFrom panic if their value is absent
// (indicating a programming error — the injector interceptor should always set them).
package inject

import (
	"context"
	"log/slog"
	"net/http"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jyablonski/lotus/internal/db"
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
	loggerKey
	httpClientKey
	analyzerURLKey
	pgxPoolKey
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
