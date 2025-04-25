package http

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthCheckHandler(t *testing.T) {
	tests := []struct {
		method         string
		expectedStatus int
		expectedBody   string
	}{
		{"GET", http.StatusOK, `{"status":"ok"`},                      // Should return 200 OK
		{"POST", http.StatusMethodNotAllowed, "Method not allowed\n"}, // Should return 405
	}

	for _, tt := range tests {
		req, err := http.NewRequest(tt.method, "/", nil)
		if err != nil {
			t.Fatalf("Could not create %s request: %v", tt.method, err)
		}

		rr := httptest.NewRecorder()
		healthCheckHandler(rr, req)

		// Check status code
		if status := rr.Code; status != tt.expectedStatus {
			t.Errorf("%s request: handler returned wrong status code: got %v want %v", tt.method, status, tt.expectedStatus)
		}

		// Check response body
		if rr.Body.String()[:len(tt.expectedBody)] != tt.expectedBody {
			t.Errorf("%s request: handler returned unexpected body: got %v want %v", tt.method, rr.Body.String(), tt.expectedBody)
		}
	}
}
