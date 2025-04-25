package grpc

import (
	"context"
	"fmt"

	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/user_pb"
	"github.com/jyablonski/lotus/internal/utils"
)

type server struct {
	pb.UnimplementedUserServiceServer
	db *db.Queries
}

func (s *server) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
	salt, err := utils.GenerateSalt(24) // base64 encoding of 24 bytes = ~32 characters
	if err != nil {
		return nil, err
	}

	hashed_password := utils.HashPassword(req.Password, salt)

	user, err := s.db.CreateUser(ctx, db.CreateUserParams{
		Username: req.Username,
		Password: hashed_password,
		Email:    req.Email,
		Salt:     salt,
	})
	if err != nil {
		return nil, err
	}

	return &pb.CreateUserResponse{
		UserId: fmt.Sprintf("%d", user.ID),
	}, nil
}
