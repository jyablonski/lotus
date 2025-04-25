package http

import (
	"log"
	"net/http"
	"time"

	"github.com/jyablonski/lotus/internal/db"
)

func NewMux(queries *db.Queries) *http.ServeMux {
	mux := http.NewServeMux()

	mux.HandleFunc("/healthcheck", healthCheckHandler)

	// Correctly use the NewUserHandler constructor
	userHandler := NewUserHandler(queries)
	mux.Handle("/user", userHandler) // ServeHTTP method will be used automatically

	return mux
}

func StartHTTPServer(queries *db.Queries) {
	mux := NewMux(queries)

	server := &http.Server{
		Addr:           ":8080",
		Handler:        mux,
		ReadTimeout:    2 * time.Second,
		WriteTimeout:   2 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	log.Println("Starting HTTP server on :8080")
	if err := server.ListenAndServe(); err != nil {
		log.Fatal("HTTP server failed to start:", err)
	}
}
