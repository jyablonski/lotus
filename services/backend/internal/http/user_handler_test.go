package http_test

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalhttp "github.com/jyablonski/lotus/internal/http"
	"github.com/jyablonski/lotus/internal/mocks"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestUserHandler_GetUser_Success(t *testing.T) {
	// Arrange
	expectedUserID := uuid.New()
	expectedEmail := "test@example.com"

	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			assert.Equal(t, expectedEmail, email)
			return db.SourceUser{
				ID:         expectedUserID,
				Email:      expectedEmail,
				Role:       "user",
				Timezone:   "UTC",
				CreatedAt:  time.Now(),
				ModifiedAt: time.Now(),
			}, nil
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)
	req := httptest.NewRequest(http.MethodGet, "/users?email="+expectedEmail, nil)
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusOK, w.Code)
	assert.Equal(t, "application/json", w.Header().Get("Content-Type"))

	var user db.SourceUser
	err := json.NewDecoder(w.Body).Decode(&user)
	require.NoError(t, err)
	assert.Equal(t, expectedUserID, user.ID)
	assert.Equal(t, expectedEmail, user.Email)

	// Verify mock was called
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 1)
}

func TestUserHandler_GetUser_MissingEmail(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	handler := internalhttp.NewUserHandler(mockQuerier)
	req := httptest.NewRequest(http.MethodGet, "/users", nil)
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusBadRequest, w.Code)
	assert.Contains(t, w.Body.String(), "Missing email query parameter")

	// Verify mock was NOT called
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 0)
}

func TestUserHandler_GetUser_NotFound(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			return db.SourceUser{}, sql.ErrNoRows
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)
	req := httptest.NewRequest(http.MethodGet, "/users?email=notfound@example.com", nil)
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusNotFound, w.Code)
	assert.Contains(t, w.Body.String(), "User not found")
}

func TestUserHandler_GetUser_DBError(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			return db.SourceUser{}, errors.New("database connection failed")
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)
	req := httptest.NewRequest(http.MethodGet, "/users?email=test@example.com", nil)
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, w.Body.String(), "Failed to retrieve user")
}

func TestUserHandler_CreateUser_Success(t *testing.T) {
	// Arrange
	expectedUserID := uuid.New()
	expectedEmail := "newuser@example.com"

	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			// Return ErrNoRows to indicate email is available
			return db.SourceUser{}, sql.ErrNoRows
		},
		CreateUserFunc: func(ctx context.Context, arg db.CreateUserParams) (db.SourceUser, error) {
			assert.Equal(t, expectedEmail, arg.Email)
			assert.True(t, arg.Password.Valid)
			assert.True(t, arg.Salt.Valid)

			return db.SourceUser{
				ID:         expectedUserID,
				Email:      expectedEmail,
				Role:       "user",
				Timezone:   "UTC",
				CreatedAt:  time.Now(),
				ModifiedAt: time.Now(),
			}, nil
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)

	body := map[string]any{
		"email":    expectedEmail,
		"password": sql.NullString{String: "securepassword123", Valid: true},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusCreated, w.Code)
	assert.Equal(t, "application/json", w.Header().Get("Content-Type"))

	var user db.SourceUser
	err := json.NewDecoder(w.Body).Decode(&user)
	require.NoError(t, err)
	assert.Equal(t, expectedUserID, user.ID)
	assert.Equal(t, expectedEmail, user.Email)

	// Verify mocks were called
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 1)
	assert.Len(t, mockQuerier.CreateUserCalls(), 1)
}

func TestUserHandler_CreateUser_InvalidEmail(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	handler := internalhttp.NewUserHandler(mockQuerier)

	body := map[string]any{
		"email":    "invalid-email",
		"password": sql.NullString{String: "password123", Valid: true},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusBadRequest, w.Code)
	assert.Contains(t, w.Body.String(), "Invalid email format")

	// Verify GetUserByEmail was NOT called
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 0)
}

func TestUserHandler_CreateUser_EmailAlreadyExists(t *testing.T) {
	// Arrange
	existingEmail := "existing@example.com"

	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			// Return a user to indicate email already exists
			return db.SourceUser{
				ID:    uuid.New(),
				Email: existingEmail,
			}, nil
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)

	body := map[string]any{
		"email":    existingEmail,
		"password": sql.NullString{String: "password123", Valid: true},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusConflict, w.Code)
	assert.Contains(t, w.Body.String(), "Email already taken")

	// Verify CreateUser was NOT called
	assert.Len(t, mockQuerier.CreateUserCalls(), 0)
}

func TestUserHandler_CreateUser_EmptyPassword(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			return db.SourceUser{}, sql.ErrNoRows
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)

	body := map[string]any{
		"email":    "test@example.com",
		"password": sql.NullString{String: "", Valid: false},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusBadRequest, w.Code)
	assert.Contains(t, w.Body.String(), "Password cannot be empty")

	// Verify CreateUser was NOT called
	assert.Len(t, mockQuerier.CreateUserCalls(), 0)
}

func TestUserHandler_CreateUser_DBError(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			return db.SourceUser{}, sql.ErrNoRows
		},
		CreateUserFunc: func(ctx context.Context, arg db.CreateUserParams) (db.SourceUser, error) {
			return db.SourceUser{}, errors.New("database connection failed")
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)

	body := map[string]any{
		"email":    "test@example.com",
		"password": sql.NullString{String: "password123", Valid: true},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, w.Body.String(), "Failed to create user")
}

func TestUserHandler_MethodNotAllowed(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	handler := internalhttp.NewUserHandler(mockQuerier)

	// Test various unsupported methods
	methods := []string{http.MethodPut, http.MethodDelete, http.MethodPatch}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			req := httptest.NewRequest(method, "/users", nil)
			w := httptest.NewRecorder()

			// Act
			handler.ServeHTTP(w, req)

			// Assert
			assert.Equal(t, http.StatusMethodNotAllowed, w.Code)
			assert.Contains(t, w.Body.String(), "Method not allowed")
		})
	}
}

func TestUserHandler_CreateUser_InvalidRequestBody(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	handler := internalhttp.NewUserHandler(mockQuerier)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader([]byte("invalid json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusBadRequest, w.Code)
	assert.Contains(t, w.Body.String(), "Invalid request body")

	// Verify no DB calls were made
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 0)
	assert.Len(t, mockQuerier.CreateUserCalls(), 0)
}

func TestUserHandler_CreateUser_CheckEmailDBError(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			return db.SourceUser{}, errors.New("database connection failed")
		},
	}

	handler := internalhttp.NewUserHandler(mockQuerier)

	body := map[string]any{
		"email":    "test@example.com",
		"password": sql.NullString{String: "password123", Valid: true},
	}
	bodyBytes, _ := json.Marshal(body)

	req := httptest.NewRequest(http.MethodPost, "/users", bytes.NewReader(bodyBytes))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	// Act
	handler.ServeHTTP(w, req)

	// Assert
	assert.Equal(t, http.StatusInternalServerError, w.Code)
	assert.Contains(t, w.Body.String(), "Error checking email availability")

	// Verify CreateUser was NOT called
	assert.Len(t, mockQuerier.CreateUserCalls(), 0)
}
