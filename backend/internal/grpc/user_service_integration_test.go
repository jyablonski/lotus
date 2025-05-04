package grpc_test

import (
	"context"
	"database/sql"
	"testing"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/require"
)

// setup integration DB and return db handle and Queries instance
func setupTestDB(t *testing.T) (*sql.DB, *db.Queries) {
	connStr := "postgres://postgres:postgres@localhost:5432/postgres?sslmode=disable&search_path=source"
	dbConn, err := sql.Open("postgres", connStr)
	require.NoError(t, err)
	return dbConn, db.New(dbConn)
}

func TestCreateUser(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	// Optional: Clean up table for idempotent test
	_, err := dbConn.Exec("DELETE FROM users")
	require.NoError(t, err)

	// Set up gRPC service instance
	svc := &grpc.UserServer{ // We'll create this type below
		DB: queries,
	}

	ctx := context.Background()
	req := &pb.CreateUserRequest{
		Email:    "grpc_test@example.com",
		Password: "strongpass123",
	}

	// Call the gRPC method
	resp, err := svc.CreateUser(ctx, req)
	require.NoError(t, err)
	require.NotEmpty(t, resp.UserId)

	// Optional: Check if user really exists in DB
	user, err := queries.GetUserByEmail(ctx, req.Email)
	require.NoError(t, err)
	require.Equal(t, req.Email, user.Email)
}

func TestCreateUserOauth(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	// Optional: Clean up table for idempotent test
	_, err := dbConn.Exec("DELETE FROM users")
	require.NoError(t, err)

	// Set up gRPC service instance
	svc := &grpc.UserServer{ // We'll create this type below
		DB: queries,
	}

	ctx := context.Background()
	req := &pb.CreateUserOauthRequest{
		Email:         "grpc_test@example.com",
		OauthProvider: "github",
	}

	// Call the gRPC method
	resp, err := svc.CreateUserOauth(ctx, req)
	require.NoError(t, err)
	require.NotEmpty(t, resp.UserId)

	// Optional: Check if user really exists in DB
	user, err := queries.GetUserByEmail(ctx, req.Email)
	require.NoError(t, err)
	require.Equal(t, req.Email, user.Email)
}

func TestGetUser(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	// Clean up
	_, err := dbConn.Exec("DELETE FROM users")
	require.NoError(t, err)

	svc := &grpc.UserServer{
		DB: queries,
	}

	ctx := context.Background()

	// --- Create user
	createReq := &pb.CreateUserRequest{
		Email:    "getuser_test@example.com",
		Password: "securepass",
	}

	createResp, err := svc.CreateUser(ctx, createReq)
	require.NoError(t, err)
	require.NotEmpty(t, createResp.UserId)

	// --- Call GetUser using email now
	getReq := &pb.GetUserRequest{
		Email: createReq.Email,
	}

	getResp, err := svc.GetUser(ctx, getReq)
	require.NoError(t, err)
	require.Equal(t, createResp.UserId, getResp.UserId)
	require.Equal(t, createReq.Email, getResp.Email)
	require.NotEmpty(t, getResp.CreatedAt)
	require.NotEmpty(t, getResp.UpdatedAt)
}

func TestGetUser_InvalidEmail(t *testing.T) {
	svc := &grpc.UserServer{} // no DB needed for this case

	_, err := svc.GetUser(context.Background(), &pb.GetUserRequest{
		Email: "",
	})

	require.Error(t, err)
	require.Contains(t, err.Error(), "email is required")
}

func TestGetUser_NotFound(t *testing.T) {
	dbConn, queries := setupTestDB(t)
	defer dbConn.Close()

	svc := &grpc.UserServer{
		DB: queries,
	}

	// use a dummy email unlikely to exist
	nonexistentEmail := "nobody@nowhere.com"

	_, err := svc.GetUser(context.Background(), &pb.GetUserRequest{
		Email: nonexistentEmail,
	})

	require.Error(t, err)
	require.Contains(t, err.Error(), "user not found")
}
