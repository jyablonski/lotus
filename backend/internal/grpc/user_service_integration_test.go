package grpc_test

import (
	"context"
	"database/sql"
	"io"
	"log/slog"
	"testing"

	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/stretchr/testify/require"
)

func setupTestDB(t *testing.T) (*sql.DB, *db.Queries) {
	connStr := "postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable&search_path=source"
	dbConn, err := sql.Open("postgres", connStr)
	require.NoError(t, err)
	return dbConn, db.New(dbConn)
}

func newTestUserServer(t *testing.T) *grpcServer.UserServer {
	dbConn, queries := setupTestDB(t)

	// Clean up before test
	_, err := dbConn.Exec("DELETE FROM users")
	require.NoError(t, err)

	t.Cleanup(func() {
		dbConn.Close()
	})

	logger := slog.New(slog.NewTextHandler(io.Discard, nil))
	return grpcServer.UserService(queries, logger)
}

func TestCreateUser(t *testing.T) {
	svc := newTestUserServer(t)

	email := "test_user@example.com"
	req := &pb.CreateUserRequest{
		Email:    email,
		Password: "strongpassword123!",
	}

	ctx := context.Background()
	resp, err := svc.CreateUser(ctx, req)
	require.NoError(t, err)
	require.NotEmpty(t, resp.UserId)

	// Validate in DB
	user, err := svc.DB.GetUserByEmail(ctx, email)
	require.NoError(t, err)
	require.Equal(t, email, user.Email)
	require.True(t, user.Password.Valid)
	require.True(t, user.Salt.Valid)
}

func TestCreateUserOauth(t *testing.T) {
	svc := newTestUserServer(t)

	email := "oauth_user@example.com"
	req := &pb.CreateUserOauthRequest{
		Email:         email,
		OauthProvider: "github",
	}

	ctx := context.Background()
	resp, err := svc.CreateUserOauth(ctx, req)
	require.NoError(t, err)
	require.NotEmpty(t, resp.UserId)

	user, err := svc.DB.GetUserByEmail(ctx, email)
	require.NoError(t, err)
	require.Equal(t, email, user.Email)
	require.True(t, user.OauthProvider.Valid)
	require.Equal(t, "github", user.OauthProvider.String)
	require.False(t, user.Password.Valid)
	require.False(t, user.Salt.Valid)
}

func TestGetUser(t *testing.T) {
	svc := newTestUserServer(t)

	email := "get_user@example.com"
	createReq := &pb.CreateUserRequest{
		Email:    email,
		Password: "getme123",
	}
	ctx := context.Background()
	createResp, err := svc.CreateUser(ctx, createReq)
	require.NoError(t, err)

	getReq := &pb.GetUserRequest{
		Email: email,
	}
	getResp, err := svc.GetUser(ctx, getReq)
	require.NoError(t, err)
	require.Equal(t, createResp.UserId, getResp.UserId)
	require.Equal(t, email, getResp.Email)
}

func TestGetUser_NotFound(t *testing.T) {
	svc := newTestUserServer(t)

	getReq := &pb.GetUserRequest{
		Email: "nonexistent@example.com",
	}
	_, err := svc.GetUser(context.Background(), getReq)
	require.Error(t, err)
	require.Contains(t, err.Error(), "user not found")
}

func TestGetUser_InvalidEmail(t *testing.T) {
	svc := newTestUserServer(t)

	getReq := &pb.GetUserRequest{} // no email
	_, err := svc.GetUser(context.Background(), getReq)
	require.Error(t, err)
	require.Contains(t, err.Error(), "email is required")
}
