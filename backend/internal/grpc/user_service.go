package grpc

import (
	"context"
	"database/sql"

	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/jyablonski/lotus/internal/utils"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
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
		UserId: user.ID.String(),
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
		UserId: user.ID.String(),
	}, nil
}

func (s *UserServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
	email := req.GetEmail()
	if email == "" {
		return nil, status.Error(codes.InvalidArgument, "email is required")
	}

	u, err := s.DB.GetUserByEmail(ctx, email)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, status.Error(codes.NotFound, "user not found")
		}
		return nil, status.Errorf(codes.Internal, "failed to get user: %v", err)
	}

	return &pb.GetUserResponse{
		UserId:    u.ID.String(),
		Email:     u.Email,
		Role:      u.Role,
		CreatedAt: u.CreatedAt.Format("2006-01-02T15:04:05Z07:00"),
		UpdatedAt: u.ModifiedAt.Format("2006-01-02T15:04:05Z07:00"),
	}, nil
}
