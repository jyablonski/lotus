package main

import (
	"context"
	"crypto/subtle"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"database/sql"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"golang.org/x/sync/errgroup"
	"golang.org/x/time/rate"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"github.com/jyablonski/lotus/internal/db"
	grpcSrv "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/jobs"

	_ "github.com/lib/pq"
)

func allowCORS(origin string, h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		h.ServeHTTP(w, r)
	})
}

// authMiddleware validates the Authorization: Bearer <key> header on every
// request except OPTIONS (handled by CORS middleware) and /metrics (Prometheus scrape).
func authMiddleware(apiKey string, logger *slog.Logger, h http.Handler) http.Handler {
	expected := []byte("Bearer " + apiKey)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodOptions || r.URL.Path == "/metrics" {
			h.ServeHTTP(w, r)
			return
		}
		got := []byte(r.Header.Get("Authorization"))
		if subtle.ConstantTimeCompare(got, expected) != 1 {
			recv := r.Header.Get("Authorization")
			if len(recv) > 10 {
				recv = recv[:10] + "…"
			}
			logger.Warn("authMiddleware: rejected request",
				"method", r.Method,
				"path", r.URL.Path,
				"received_prefix", recv,
				"expected_len", len(expected),
				"received_len", len(got),
			)
			http.Error(w, `{"code":16,"message":"unauthorized"}`, http.StatusUnauthorized)
			return
		}
		h.ServeHTTP(w, r)
	})
}

// rateLimitMiddleware enforces a per-IP token-bucket rate limit.
// rps is the sustained request rate; burst is the maximum burst size.
// Stale limiters (no activity for 10 minutes) are pruned every 5 minutes.
// The pruning goroutine stops when ctx is cancelled (i.e. on graceful shutdown).
func rateLimitMiddleware(ctx context.Context, rps float64, burst int, h http.Handler) http.Handler {
	type entry struct {
		limiter  *rate.Limiter
		lastSeen time.Time
	}

	var mu sync.Mutex
	limiters := make(map[string]*entry)

	// Prune stale entries in the background.
	go func() {
		ticker := time.NewTicker(5 * time.Minute)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				mu.Lock()
				for ip, e := range limiters {
					if time.Since(e.lastSeen) > 10*time.Minute {
						delete(limiters, ip)
					}
				}
				mu.Unlock()
			}
		}
	}()

	getLimiter := func(ip string) *rate.Limiter {
		mu.Lock()
		defer mu.Unlock()
		e, ok := limiters[ip]
		if !ok {
			e = &entry{limiter: rate.NewLimiter(rate.Limit(rps), burst)}
			limiters[ip] = e
		}
		e.lastSeen = time.Now()
		return e.limiter
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := r.RemoteAddr
		if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
			ip = forwarded
		}
		if !getLimiter(ip).Allow() {
			w.Header().Set("Retry-After", "1")
			http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
			return
		}
		h.ServeHTTP(w, r)
	})
}

func initLogger() *slog.Logger {
	handler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	})
	logger := slog.New(handler)
	slog.SetDefault(logger)
	return logger
}

func main() {
	logger := initLogger()
	logger.Info("Starting Lotus Backend Service")

	// ── OpenTelemetry ──────────────────────────────────────────────────
	otelCtx := context.Background()
	shutdownTracer, err := initTracer(otelCtx)
	if err != nil {
		logger.Warn("Failed to initialize tracer; continuing without tracing", "error", err)
	} else {
		defer shutdownTracer(otelCtx) //nolint:errcheck
	}
	shutdownMeter, err := initMeter()
	if err != nil {
		logger.Warn("Failed to initialize meter; continuing without metrics", "error", err)
	} else {
		defer shutdownMeter(otelCtx) //nolint:errcheck
	}

	// ── Required environment ───────────────────────────────────────────
	connStr := os.Getenv("DB_CONN")
	if connStr == "" {
		logger.Error("DB_CONN environment variable is required")
		os.Exit(1)
	}

	backendAPIKey := os.Getenv("BACKEND_API_KEY")
	if backendAPIKey == "" {
		logger.Error("BACKEND_API_KEY environment variable is required")
		os.Exit(1)
	}

	analyzerAPIKey := os.Getenv("ANALYZER_API_KEY")
	if analyzerAPIKey == "" {
		logger.Error("ANALYZER_API_KEY environment variable is required")
		os.Exit(1)
	}

	analyzerBaseURL := os.Getenv("ANALYZER_BASE_URL")
	if analyzerBaseURL == "" {
		analyzerBaseURL = "http://localhost:8083"
		logger.Info("Using default analyzer URL", "url", analyzerBaseURL)
	} else {
		logger.Info("Using analyzer URL from environment", "url", analyzerBaseURL)
	}

	corsOrigin := os.Getenv("CORS_ALLOWED_ORIGIN")
	if corsOrigin == "" {
		corsOrigin = "http://localhost:3000"
	}

	// ── Database (database/sql + lib/pq) ──────────────────────────────
	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		logger.Error("Failed to open database connection", "error", err)
		os.Exit(1)
	}
	defer dbConn.Close()

	if err := dbConn.Ping(); err != nil {
		logger.Error("Failed to ping database", "error", err)
		os.Exit(1)
	}

	dbConn.SetMaxOpenConns(25)
	dbConn.SetMaxIdleConns(5)
	dbConn.SetConnMaxLifetime(5 * time.Minute)
	dbConn.SetConnMaxIdleTime(1 * time.Minute)

	queries := db.New(dbConn)

	// ── pgxpool (used by River) ────────────────────────────────────────
	pgxPool, err := pgxpool.New(context.Background(), connStr)
	if err != nil {
		logger.Error("Failed to create pgxpool", "error", err)
		os.Exit(1)
	}
	defer pgxPool.Close()

	// ── River migrations ───────────────────────────────────────────────
	if err := jobs.RunMigrations(context.Background(), pgxPool, logger); err != nil {
		logger.Error("Failed to run River migrations", "error", err)
		os.Exit(1)
	}

	// ── Shared HTTP client for outbound calls ──────────────────────────
	// otelhttp.NewTransport injects W3C TraceContext headers so calls to the
	// analyzer appear as child spans in the same Jaeger trace.
	httpClient := &http.Client{
		Timeout:   10 * time.Second,
		Transport: otelhttp.NewTransport(http.DefaultTransport),
	}

	// ── River client ───────────────────────────────────────────────────
	riverClient, err := jobs.NewClient(pgxPool, queries, httpClient, analyzerBaseURL, analyzerAPIKey, logger)
	if err != nil {
		logger.Error("Failed to create River client", "error", err)
		os.Exit(1)
	}

	// ── Injector interceptor ───────────────────────────────────────────
	// Populates every incoming gRPC request context with all dependencies.
	injector := func(
		ctx context.Context,
		req interface{},
		_ *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		ctx = inject.WithDB(ctx, queries)
		ctx = inject.WithLogger(ctx, logger)
		ctx = inject.WithHTTPClient(ctx, httpClient)
		ctx = inject.WithAnalyzerURL(ctx, analyzerBaseURL)
		ctx = inject.WithPgxPool(ctx, pgxPool)
		ctx = inject.WithRiverClient(ctx, riverClient)
		return handler(ctx, req)
	}

	// ── gRPC server ────────────────────────────────────────────────────
	grpcServer := grpc.NewServer(
		grpc.StatsHandler(otelgrpc.NewServerHandler()),
		grpc.ChainUnaryInterceptor(injector, grpcSrv.LoggingInterceptor(logger)),
	)
	grpcSrv.RegisterServices(grpcServer)

	// ── gRPC-Gateway (HTTP) ────────────────────────────────────────────
	gwMux := runtime.NewServeMux()
	dialOpts := []grpc.DialOption{
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithStatsHandler(otelgrpc.NewClientHandler()),
	}

	if err := grpcSrv.RegisterGateway(context.Background(), gwMux, "localhost:50051", dialOpts); err != nil {
		logger.Error("Failed to register gRPC-Gateway handlers", "error", err)
		os.Exit(1)
	}

	rootMux := http.NewServeMux()
	registerDocsHandlers(rootMux, logger)
	rootMux.Handle("/metrics", promhttp.Handler())
	rootMux.Handle("/", gwMux)

	// ── Graceful shutdown context ──────────────────────────────────────
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	httpServer := &http.Server{
		Addr:    ":8080",
		Handler: rateLimitMiddleware(ctx, 20, 40, allowCORS(corsOrigin, authMiddleware(backendAPIKey, logger, otelhttp.NewHandler(rootMux, "http")))),
	}

	g, gCtx := errgroup.WithContext(ctx)

	// Start River client
	g.Go(func() error {
		logger.Info("Starting River job queue")
		if err := riverClient.Start(gCtx); err != nil {
			return err
		}
		return nil
	})

	// Start gRPC server
	g.Go(func() error {
		lis, err := net.Listen("tcp", ":50051")
		if err != nil {
			return err
		}
		logger.Info("gRPC server listening", "address", ":50051")
		return grpcServer.Serve(lis)
	})

	// Start HTTP gateway
	g.Go(func() error {
		logger.Info("gRPC-Gateway listening", "address", ":8080", "cors_origin", corsOrigin)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			return err
		}
		return nil
	})

	// Shutdown goroutine: waits for cancellation, then stops servers.
	g.Go(func() error {
		<-gCtx.Done()
		logger.Info("Shutting down servers …")

		grpcServer.GracefulStop()

		riverStopCtx, riverCancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer riverCancel()
		if err := riverClient.Stop(riverStopCtx); err != nil {
			logger.Warn("River client did not stop cleanly", "error", err)
		}

		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		return httpServer.Shutdown(shutdownCtx)
	})

	if err := g.Wait(); err != nil {
		logger.Error("Server exited with error", "error", err)
		os.Exit(1)
	}

	logger.Info("Server shut down gracefully")
}
