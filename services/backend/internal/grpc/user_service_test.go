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
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// newTestLogger creates a logger that discards output for testing
func newTestLogger() *slog.Logger {
	return slog.New(slog.NewTextHandler(io.Discard, nil))
}

// testCtx returns a context populated with the given DB mock and a discard logger.
func testCtx(mock db.Querier) context.Context {
	ctx := context.Background()
	ctx = inject.WithDB(ctx, mock)
	ctx = inject.WithLogger(ctx, newTestLogger())
	return ctx
}

func TestUserServer_CreateUser_Success(t *testing.T) {
	// Arrange
	expectedUserID := uuid.New()
	expectedEmail := "test@example.com"

	mockQuerier := &mocks.QuerierMock{
		CreateUserFunc: func(ctx context.Context, arg db.CreateUserParams) (db.SourceUser, error) {
			// Verify the email is passed correctly
			assert.Equal(t, expectedEmail, arg.Email)
			// Verify password is set (bcrypt hash) and salt is not used
			assert.True(t, arg.Password.Valid)
			assert.False(t, arg.Salt.Valid) // bcrypt embeds its own salt

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

	server := &internalgrpc.UserServer{}

	req := &pb.CreateUserRequest{
		Email:    expectedEmail,
		Password: "securepassword123",
	}

	// Act
	resp, err := server.CreateUser(testCtx(mockQuerier), req)

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

	server := &internalgrpc.UserServer{}

	req := &pb.CreateUserRequest{
		Email:    "test@example.com",
		Password: "securepassword123",
	}

	// Act
	resp, err := server.CreateUser(testCtx(mockQuerier), req)

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

	server := &internalgrpc.UserServer{}

	req := &pb.GetUserRequest{
		Email: expectedEmail,
	}

	// Act
	resp, err := server.GetUser(testCtx(mockQuerier), req)

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

	server := &internalgrpc.UserServer{}

	req := &pb.GetUserRequest{
		Email: "nonexistent@example.com",
	}

	// Act
	resp, err := server.GetUser(testCtx(mockQuerier), req)

	// Assert
	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "user not found")
}

func TestUserServer_GetUser_EmptyEmail(t *testing.T) {
	// Arrange — no DB mock needed; validation fails before DB access.
	mockQuerier := &mocks.QuerierMock{}

	server := &internalgrpc.UserServer{}

	req := &pb.GetUserRequest{
		Email: "",
	}

	// Act — context still needs DB because GetUser extracts it after validation,
	// but with the new code DB is only extracted after the empty-email check,
	// so a bare context is sufficient.
	resp, err := server.GetUser(testCtx(mockQuerier), req)

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

	server := &internalgrpc.UserServer{}

	req := &pb.CreateUserOauthRequest{
		Email:         expectedEmail,
		OauthProvider: expectedProvider,
	}

	// Act
	resp, err := server.CreateUserOauth(testCtx(mockQuerier), req)

	// Assert
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, expectedUserID.String(), resp.UserId)

	// Verify the mock was called exactly once
	assert.Len(t, mockQuerier.CreateUserOauthCalls(), 1)
}

func TestUserServer_UpdateUserTimezone_Success(t *testing.T) {
	expectedUserID := uuid.New()
	expectedTimezone := "America/Los_Angeles"

	mockQuerier := &mocks.QuerierMock{
		UpdateUserTimezoneFunc: func(ctx context.Context, arg db.UpdateUserTimezoneParams) (db.SourceUser, error) {
			assert.Equal(t, expectedUserID, arg.ID)
			assert.Equal(t, expectedTimezone, arg.Timezone)
			return db.SourceUser{
				ID:         expectedUserID,
				Timezone:   expectedTimezone,
				ModifiedAt: time.Now(),
			}, nil
		},
	}

	server := &internalgrpc.UserServer{}
	req := &pb.UpdateUserTimezoneRequest{
		UserId:   expectedUserID.String(),
		Timezone: expectedTimezone,
	}

	resp, err := server.UpdateUserTimezone(testCtx(mockQuerier), req)

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Equal(t, expectedUserID.String(), resp.UserId)
	assert.Equal(t, expectedTimezone, resp.Timezone)
	assert.Len(t, mockQuerier.UpdateUserTimezoneCalls(), 1)
}

func TestUserServer_UpdateUserTimezone_InvalidTimezone(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{}
	server := &internalgrpc.UserServer{}

	req := &pb.UpdateUserTimezoneRequest{
		UserId:   uuid.New().String(),
		Timezone: "Not/A/Timezone",
	}

	resp, err := server.UpdateUserTimezone(testCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "invalid timezone")
	assert.Len(t, mockQuerier.UpdateUserTimezoneCalls(), 0)
}

func TestUserServer_UpdateUserTimezone_InvalidUserID(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{}
	server := &internalgrpc.UserServer{}

	req := &pb.UpdateUserTimezoneRequest{
		UserId:   "not-a-uuid",
		Timezone: "America/New_York",
	}

	resp, err := server.UpdateUserTimezone(testCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "invalid user ID")
	assert.Len(t, mockQuerier.UpdateUserTimezoneCalls(), 0)
}

func TestUserServer_UpdateUserTimezone_DBError(t *testing.T) {
	expectedUserID := uuid.New()

	mockQuerier := &mocks.QuerierMock{
		UpdateUserTimezoneFunc: func(ctx context.Context, arg db.UpdateUserTimezoneParams) (db.SourceUser, error) {
			return db.SourceUser{}, errors.New("database error")
		},
	}

	server := &internalgrpc.UserServer{}
	req := &pb.UpdateUserTimezoneRequest{
		UserId:   expectedUserID.String(),
		Timezone: "America/Chicago",
	}

	resp, err := server.UpdateUserTimezone(testCtx(mockQuerier), req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to update timezone")
	assert.Len(t, mockQuerier.UpdateUserTimezoneCalls(), 1)
}
