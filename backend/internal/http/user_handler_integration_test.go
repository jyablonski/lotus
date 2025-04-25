package http

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/jyablonski/lotus/internal/db"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
)

var testDB *sql.DB
var testQueries *db.Queries

func setupTestDB(t *testing.T) {
	// Setup database connection for testing
	connStr := "postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable&search_path=source"
	var err error
	testDB, err = sql.Open("postgres", connStr)
	if err != nil {
		t.Fatalf("Failed to connect to database: %v", err)
	}

	// Initialize queries object
	testQueries = db.New(testDB)
}

func teardownTestDB(t *testing.T) {
	// Clean up test data
	_, err := testDB.Exec("DELETE FROM users")
	if err != nil {
		t.Fatalf("Failed to clean up test database: %v", err)
	}

	// Close database connection
	testDB.Close()
}

func TestCreateUser(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Create user handler
	handler := NewUserHandler(testQueries)

	// Prepare request body
	input := db.CreateUserParams{
		Username: "testuser",
		Email:    "testuser@example.com",
		Password: "password123", // Should ideally be hashed
	}

	body, err := json.Marshal(input)
	if err != nil {
		t.Fatalf("Failed to marshal request body: %v", err)
	}

	// Create a POST request
	req := httptest.NewRequest(http.MethodPost, "/user", bytes.NewReader(body))
	rec := httptest.NewRecorder()

	// Serve the HTTP request
	handler.ServeHTTP(rec, req)

	// Assert the response status
	assert.Equal(t, http.StatusCreated, rec.Code)

	// Parse response body
	var user db.SourceUser
	err = json.NewDecoder(rec.Body).Decode(&user)
	if err != nil {
		t.Fatalf("Failed to decode response body: %v", err)
	}

	// Assert user creation
	assert.Equal(t, input.Username, user.Username)
	assert.Equal(t, input.Email, user.Email)
}

func TestGetUser(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Insert a user directly into the test DB
	input := db.CreateUserParams{
		Username: "existinguser",
		Email:    "existinguser@example.com",
		Password: "password123", // Should ideally be hashed
	}

	_, err := testQueries.CreateUser(context.Background(), input)
	if err != nil {
		t.Fatalf("Failed to create test user: %v", err)
	}

	// Create user handler
	handler := NewUserHandler(testQueries)

	// Create a GET request to fetch the user
	req := httptest.NewRequest(http.MethodGet, "/user?username=existinguser", nil)
	rec := httptest.NewRecorder()

	// Serve the HTTP request
	handler.ServeHTTP(rec, req)

	// Assert the response status
	assert.Equal(t, http.StatusOK, rec.Code)

	// Parse response body
	var user db.SourceUser
	err = json.NewDecoder(rec.Body).Decode(&user)
	if err != nil {
		t.Fatalf("Failed to decode response body: %v", err)
	}

	// Assert that the correct user was returned
	assert.Equal(t, input.Username, user.Username)
	assert.Equal(t, input.Email, user.Email)
}

func TestCreateUser_UsernameExists(t *testing.T) {
	setupTestDB(t)
	defer teardownTestDB(t)

	// Insert a user directly into the test DB
	input := db.CreateUserParams{
		Username: "existinguser",
		Email:    "existinguser@example.com",
		Password: "password123", // Should ideally be hashed
	}

	_, err := testQueries.CreateUser(context.Background(), input)
	if err != nil {
		t.Fatalf("Failed to create test user: %v", err)
	}

	// Create user handler
	handler := NewUserHandler(testQueries)

	// Prepare request body for another user with the same username
	newInput := db.CreateUserParams{
		Username: "existinguser", // same username as the existing user
		Email:    "newuser@example.com",
		Password: "newpassword123",
	}

	body, err := json.Marshal(newInput)
	if err != nil {
		t.Fatalf("Failed to marshal request body: %v", err)
	}

	// Create a POST request
	req := httptest.NewRequest(http.MethodPost, "/user", bytes.NewReader(body))
	rec := httptest.NewRecorder()

	// Serve the HTTP request
	handler.ServeHTTP(rec, req)

	// Assert the response status is Conflict (409)
	assert.Equal(t, http.StatusConflict, rec.Code)

	// Assert the response message
	assert.Contains(t, rec.Body.String(), "Username already taken")
}
