package grpc

import "net/http"

// HTTPClient is an interface for making HTTP requests.
// This allows for easy mocking in tests.
//
//go:generate moq -out mocks/http_client_mock.go -pkg mocks . HTTPClient
type HTTPClient interface {
	Do(req *http.Request) (*http.Response, error)
}
