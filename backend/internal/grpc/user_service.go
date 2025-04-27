package grpc

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/jyablonski/lotus/internal/utils"
)

type UserServer struct {
	pb.UnimplementedUserServiceServer
	DB *db.Queries
}

func UserService(q *db.Queries) *UserServer {
	return &UserServer{
		DB: q,
	}
}

// CreateUser handles username/password-based user creation.
func (s *UserServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
	// Salt and password are only used for non-OAuth users.
	salt, err := utils.GenerateSalt(24) // base64 encoding of 24 bytes = ~32 characters
	if err != nil {
		return nil, err
	}

	hashed_password := utils.HashPassword(req.Password, salt)

	// Using sql.NullString for nullable fields
	password := sql.NullString{String: hashed_password, Valid: true}
	saltStr := sql.NullString{String: salt, Valid: true}

	user, err := s.DB.CreateUser(ctx, db.CreateUserParams{
		Email:    req.Email,
		Password: password,
		Salt:     saltStr,
	})
	if err != nil {
		return nil, err
	}

	return &pb.CreateUserResponse{
		UserId: fmt.Sprintf("%s", user.ID),
	}, nil
}

// CreateUserOauth handles OAuth-based user creation.
func (s *UserServer) CreateUserOauth(ctx context.Context, req *pb.CreateUserOauthRequest) (*pb.CreateUserResponse, error) {
	// For OAuth, no password is required; we store the email and OAuth provider.
	// Using sql.NullString for nullable OAuth provider field
	oauthProvider := sql.NullString{String: req.OauthProvider, Valid: true}

	user, err := s.DB.CreateUserOauth(ctx, db.CreateUserOauthParams{
		Email:         req.Email,
		OauthProvider: oauthProvider, // e.g., "github"
	})
	if err != nil {
		return nil, err
	}

	return &pb.CreateUserResponse{
		UserId: fmt.Sprintf("%s", user.ID),
	}, nil
}
