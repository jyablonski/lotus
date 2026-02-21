// Package inject provides context-based dependency injection helpers.
//
// Each dependency has a WithX function that returns a new context carrying
// the value, and an XFrom function that extracts it. LoggerFrom falls back
// to slog.Default() when no logger is set; DBFrom and HTTPClientFrom panic
// if their value is absent (indicating a programming error — the injector
// interceptor should always set them).
package inject

import (
	"context"
	"log/slog"
	"net/http"

	"github.com/jyablonski/lotus/internal/db"
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
