package main

import (
	"database/sql"
	"log"
	"os"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/http"
	_ "github.com/lib/pq"
)

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

	// Start both HTTP and gRPC servers concurrently
	go http.StartHTTPServer(queries)

	if err := grpc.StartGRPCServer(queries); err != nil {
		log.Fatalf("Failed to start gRPC server: %v", err)
	}
}
