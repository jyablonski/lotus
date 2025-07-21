package http

import (
	"net/http"
	"time"
)

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)

	utc_timestamp := time.Now().UTC().Format(time.RFC3339)
	w.Write([]byte(`{"status":"ok","timestamp":"` + utc_timestamp + `"}`))
}
