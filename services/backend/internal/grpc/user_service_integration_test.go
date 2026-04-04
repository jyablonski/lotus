package grpc_test

import (
	"context"
	"testing"

	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/stretchr/testify/require"
)

func TestCreateUser(t *testing.T) {
	ctx, queries := newTestCtx(t)
	svc := &grpcServer.UserServer{}

	email := "test_user@example.com"
	resp, err := svc.CreateUser(ctx, &pb.CreateUserRequest{
		Email:    email,
		Password: "strongpassword123!",
	})
	require.NoError(t, err)
	require.NotEmpty(t, resp.UserId)

	user, err := queries.GetUserByEmail(ctx, email)
	require.NoError(t, err)
	require.Equal(t, email, user.Email)
	require.NotNil(t, user.Password)
	require.Nil(t, user.Salt) // bcrypt embeds its own salt
}

func TestCreateUserOauth(t *testing.T) {
	ctx, queries := newTestCtx(t)
	svc := &grpcServer.UserServer{}

	email := "oauth_user@example.com"
	resp, err := svc.CreateUserOauth(ctx, &pb.CreateUserOauthRequest{
		Email:         email,
		OauthProvider: "github",
	})
	require.NoError(t, err)
	require.NotEmpty(t, resp.UserId)

	user, err := queries.GetUserByEmail(ctx, email)
	require.NoError(t, err)
	require.Equal(t, email, user.Email)
	require.NotNil(t, user.OauthProvider)
	require.Equal(t, "github", *user.OauthProvider)
	require.Nil(t, user.Password)
	require.Nil(t, user.Salt)
}

func TestGetUser(t *testing.T) {
	ctx, _ := newTestCtx(t)
	svc := &grpcServer.UserServer{}

	email := "get_user@example.com"
	createResp, err := svc.CreateUser(ctx, &pb.CreateUserRequest{
		Email:    email,
		Password: "getme123",
	})
	require.NoError(t, err)

	getResp, err := svc.GetUser(ctx, &pb.GetUserRequest{Email: email})
	require.NoError(t, err)
	require.Equal(t, createResp.UserId, getResp.UserId)
	require.Equal(t, email, getResp.Email)
}

func TestGetUser_NotFound(t *testing.T) {
	ctx, _ := newTestCtx(t)
	svc := &grpcServer.UserServer{}

	_, err := svc.GetUser(ctx, &pb.GetUserRequest{Email: "nonexistent@example.com"})
	require.Error(t, err)
	require.Contains(t, err.Error(), "user not found")
}

func TestGetUser_InvalidEmail(t *testing.T) {
	svc := &grpcServer.UserServer{}

	_, err := svc.GetUser(context.Background(), &pb.GetUserRequest{})
	require.Error(t, err)
	require.Contains(t, err.Error(), "email is required")
}
