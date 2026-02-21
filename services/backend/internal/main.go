package main

import (
	"context"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"golang.org/x/sync/errgroup"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"github.com/jyablonski/lotus/internal/db"
	grpcSrv "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"

	"database/sql"

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

	// ── Required environment ───────────────────────────────────────────
	connStr := os.Getenv("DB_CONN")
	if connStr == "" {
		logger.Error("DB_CONN environment variable is required")
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

	// ── Database ───────────────────────────────────────────────────────
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

	queries := db.New(dbConn)

	// ── Shared HTTP client for outbound calls ──────────────────────────
	httpClient := &http.Client{Timeout: 10 * time.Second}

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
		return handler(ctx, req)
	}

	// ── gRPC server ────────────────────────────────────────────────────
	grpcServer := grpc.NewServer(
		grpc.ChainUnaryInterceptor(injector, grpcSrv.LoggingInterceptor(logger)),
	)
	grpcSrv.RegisterServices(grpcServer)

	// ── gRPC-Gateway (HTTP) ────────────────────────────────────────────
	gwMux := runtime.NewServeMux()
	dialOpts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}

	if err := grpcSrv.RegisterGateway(context.Background(), gwMux, "localhost:50051", dialOpts); err != nil {
		logger.Error("Failed to register gRPC-Gateway handlers", "error", err)
		os.Exit(1)
	}

	httpServer := &http.Server{
		Addr:    ":8080",
		Handler: allowCORS(corsOrigin, gwMux),
	}

	// ── Graceful shutdown context ──────────────────────────────────────
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	g, gCtx := errgroup.WithContext(ctx)

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
