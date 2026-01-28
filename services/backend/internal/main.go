package main

import (
	"context"
	"database/sql"
	"log/slog"
	"net/http"
	"os"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"github.com/jyablonski/lotus/internal/db"
	grpcSrv "github.com/jyablonski/lotus/internal/grpc"
	httpSrv "github.com/jyablonski/lotus/internal/http"
	analytics_pb "github.com/jyablonski/lotus/internal/pb/proto/analytics"
	journal_pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	user_pb "github.com/jyablonski/lotus/internal/pb/proto/user"

	_ "github.com/lib/pq"
)

func allowCORS(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "http://localhost:3000")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		// If this is a preflight request, respond immediately
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		// Otherwise, pass along to the next handler
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

	connStr := os.Getenv("DB_CONN")
	if connStr == "" {
		logger.Error("DB_CONN environment variable is required")
	}

	// Get analyzer service URL from environment
	analyzerBaseURL := os.Getenv("ANALYZER_BASE_URL")
	if analyzerBaseURL == "" {
		analyzerBaseURL = "http://localhost:8083" // default fallback
		logger.Info("Using default analyzer URL", "url", analyzerBaseURL)
	} else {
		logger.Info("Using analyzer URL from environment", "url", analyzerBaseURL)
	}

	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		logger.Error("Failed to connect to database", "error", err)
	}
	defer dbConn.Close()

	queries := db.New(dbConn)

	// Start original HTTP server on :8081
	go func() {
		httpSrv.StartHTTPServer(queries, logger)
	}()

	// Start gRPC server on :50052 with analyzer URL
	go func() {
		if err := grpcSrv.StartGRPCServer(queries, logger, analyzerBaseURL); err != nil {
			logger.Error("Failed to start gRPC server", "error", err)
		}
	}()

	// Start gRPC-Gateway on :8080
	go func() {
		logger.Info("Starting gRPC-Gateway on :8080")

		ctx := context.Background()
		mux := runtime.NewServeMux()
		opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}

		err := user_pb.RegisterUserServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts)
		if err != nil {
			logger.Error("Failed to register UserService gRPC-Gateway", "error", err)
		}

		err = journal_pb.RegisterJournalServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts)
		if err != nil {
			logger.Error("Failed to register JournalService gRPC-Gateway", "error", err)
		}

		err = analytics_pb.RegisterAnalyticsServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts)
		if err != nil {
			logger.Error("Failed to register AnalyticsService gRPC-Gateway", "error", err)
		}

		if err := http.ListenAndServe(":8080", allowCORS(mux)); err != nil {
			logger.Error("Failed to serve gRPC-Gateway", "error", err)
		}
	}()

	// Block forever
	select {}
}
