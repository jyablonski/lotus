package main

import (
	"context"
	"database/sql"
	"log"
	"net/http"
	"os"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"github.com/jyablonski/lotus/internal/db"
	grpcSrv "github.com/jyablonski/lotus/internal/grpc"
	httpSrv "github.com/jyablonski/lotus/internal/http"
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

func main() {
	connStr := os.Getenv("DB_CONN")
	if connStr == "" {
		log.Fatal("DB_CONN environment variable is required")
	}

	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer dbConn.Close()

	queries := db.New(dbConn)

	// Start original HTTP server on :8081
	go func() {
		httpSrv.StartHTTPServer(queries)
	}()

	// Start gRPC server on :50052
	go func() {
		if err := grpcSrv.StartGRPCServer(queries); err != nil {
			log.Fatalf("Failed to start gRPC server: %v", err)
		}
	}()

	// Start gRPC-Gateway on :8080
	go func() {
		log.Println("Starting gRPC-Gateway on :8080")

		ctx := context.Background()
		mux := runtime.NewServeMux()
		opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}

		err := user_pb.RegisterUserServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts)
		if err != nil {
			log.Fatalf("Failed to register UserService gRPC-Gateway: %v", err)
		}

		err = journal_pb.RegisterJournalServiceHandlerFromEndpoint(ctx, mux, "localhost:50051", opts) // Register JournalService
		if err != nil {
			log.Fatalf("Failed to register JournalService gRPC-Gateway: %v", err)
		}

		if err := http.ListenAndServe(":8080", allowCORS(mux)); err != nil {
			log.Fatalf("Failed to serve gRPC-Gateway: %v", err)
		}
	}()

	// Block forever
	select {}
}
