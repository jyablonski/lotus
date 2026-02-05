package grpc_test

import (
	"context"
	"database/sql"
	"errors"
	"io"
	"log/slog"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// newTestLogger creates a logger that discards output for testing
func newTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

func TestUserServer_CreateUser_Success(t *testing.T) {
	// Arrange
	expectedUserID := uuid.New()
	expectedEmail := "test@example.com"

	mockQuerier := &mocks.QuerierMock{
		CreateUserFunc: func(ctx context.Context, arg db.CreateUserParams) (db.SourceUser, error) {
			// Verify the email is passed correctly
			assert.Equal(t, expectedEmail, arg.Email)
			// Verify password and salt are set
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

	server := internalgrpc.UserService(mockQuerier, newTestLogger())

	req := &pb.CreateUserRequest{
		Email:    expectedEmail,
		Password: "securepassword123",
	}

	// Act
	resp, err := server.CreateUser(context.Background(), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, expectedUserID.String(), resp.UserId)

	// Verify the mock was called exactly once
	assert.Len(t, mockQuerier.CreateUserCalls(), 1)
}

func TestUserServer_CreateUser_DBError(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		CreateUserFunc: func(ctx context.Context, arg db.CreateUserParams) (db.SourceUser, error) {
			return db.SourceUser{}, errors.New("database connection failed")
		},
	}

	server := internalgrpc.UserService(mockQuerier, newTestLogger())

	req := &pb.CreateUserRequest{
		Email:    "test@example.com",
		Password: "securepassword123",
	}

	// Act
	resp, err := server.CreateUser(context.Background(), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "could not create user")
}

func TestUserServer_GetUser_Success(t *testing.T) {
	// Arrange
	expectedUserID := uuid.New()
	expectedEmail := "test@example.com"
	expectedRole := "admin"
	expectedTimezone := "America/New_York"
	expectedCreatedAt := time.Now().Add(-24 * time.Hour)
	expectedModifiedAt := time.Now()

	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			assert.Equal(t, expectedEmail, email)
			return db.SourceUser{
				ID:         expectedUserID,
				Email:      expectedEmail,
				Role:       expectedRole,
				Timezone:   expectedTimezone,
				CreatedAt:  expectedCreatedAt,
				ModifiedAt: expectedModifiedAt,
			}, nil
		},
	}

	server := internalgrpc.UserService(mockQuerier, newTestLogger())

	req := &pb.GetUserRequest{
		Email: expectedEmail,
	}

	// Act
	resp, err := server.GetUser(context.Background(), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, expectedUserID.String(), resp.UserId)
	assert.Equal(t, expectedEmail, resp.Email)
	assert.Equal(t, expectedRole, resp.Role)
	assert.Equal(t, expectedTimezone, resp.Timezone)

	// Verify the mock was called
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 1)
}

func TestUserServer_GetUser_NotFound(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{
		GetUserByEmailFunc: func(ctx context.Context, email string) (db.SourceUser, error) {
			return db.SourceUser{}, sql.ErrNoRows
		},
	}

	server := internalgrpc.UserService(mockQuerier, newTestLogger())

	req := &pb.GetUserRequest{
		Email: "nonexistent@example.com",
	}

	// Act
	resp, err := server.GetUser(context.Background(), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "user not found")
}

func TestUserServer_GetUser_EmptyEmail(t *testing.T) {
	// Arrange
	mockQuerier := &mocks.QuerierMock{}

	server := internalgrpc.UserService(mockQuerier, newTestLogger())

	req := &pb.GetUserRequest{
		Email: "",
	}

	// Act
	resp, err := server.GetUser(context.Background(), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "email is required")

	// Verify the mock was NOT called (validation should fail first)
	assert.Len(t, mockQuerier.GetUserByEmailCalls(), 0)
}

func TestUserServer_CreateUserOauth_Success(t *testing.T) {
	// Arrange
	expectedUserID := uuid.New()
	expectedEmail := "oauth@example.com"
	expectedProvider := "github"

	mockQuerier := &mocks.QuerierMock{
		CreateUserOauthFunc: func(ctx context.Context, arg db.CreateUserOauthParams) (db.SourceUser, error) {
			assert.Equal(t, expectedEmail, arg.Email)
			assert.True(t, arg.OauthProvider.Valid)
			assert.Equal(t, expectedProvider, arg.OauthProvider.String)

			return db.SourceUser{
				ID:            expectedUserID,
				Email:         expectedEmail,
				OauthProvider: sql.NullString{String: expectedProvider, Valid: true},
				Role:          "user",
				Timezone:      "UTC",
				CreatedAt:     time.Now(),
				ModifiedAt:    time.Now(),
			}, nil
		},
	}

	server := internalgrpc.UserService(mockQuerier, newTestLogger())

	req := &pb.CreateUserOauthRequest{
		Email:         expectedEmail,
		OauthProvider: expectedProvider,
	}

	// Act
	resp, err := server.CreateUserOauth(context.Background(), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, expectedUserID.String(), resp.UserId)

	// Verify the mock was called exactly once
	assert.Len(t, mockQuerier.CreateUserOauthCalls(), 1)
}
