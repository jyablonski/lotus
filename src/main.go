package main

import (
	"database/sql"
	"log"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/jyablonski/lotus/src/db"

	_ "github.com/lib/pq" // Import the PostgreSQL driver
)

func handlers(queries *db.Queries) *http.ServeMux {
	mux := http.NewServeMux()

	mux.HandleFunc("/healthcheck", healthCheckHandler)

	// Initialize user handler with queries instance
	userHandler := NewUserHandler(queries)
	mux.Handle("/user", userHandler) // Use Handle instead of HandleFunc

	return mux
}

func startHTTPServer(queries *db.Queries) {
	server := &http.Server{
		Addr:           ":8080",
		Handler:        handlers(queries),
		ReadTimeout:    2 * time.Second,
		WriteTimeout:   2 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	slog.Info("Starting HTTP server", "addr", server.Addr)

	if err := server.ListenAndServe(); err != nil {
		slog.Error("Failed to start HTTP server", "error", err)
		os.Exit(1)
	}
}

func main() {
	// Load DB connection string from env
	connStr := os.Getenv("DB_CONN")
	if connStr == "" {
		log.Fatal("DB_CONN environment variable is required")
	}

	// Open a connection to the database
	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer dbConn.Close()

	// Initialize sqlc queries
	queries := db.New(dbConn)

	// Start HTTP server
	go startHTTPServer(queries)

	// Block the main function to keep the server running
	select {}
}
