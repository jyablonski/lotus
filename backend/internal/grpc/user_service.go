package grpc

import (
	"context"
	"fmt"

	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/user_pb/proto/user"
	"github.com/jyablonski/lotus/internal/utils"
)

type Server struct {
	pb.UnimplementedUserServiceServer
	DB *db.Queries
}

func (s *Server) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
	salt, err := utils.GenerateSalt(24) // base64 encoding of 24 bytes = ~32 characters
	if err != nil {
		return nil, err
	}

	hashed_password := utils.HashPassword(req.Password, salt)

	user, err := s.DB.CreateUser(ctx, db.CreateUserParams{
		Email:    req.Email,
		Password: hashed_password,
		Salt:     salt,
	})
	if err != nil {
		return nil, err
	}

	return &pb.CreateUserResponse{
		UserId: fmt.Sprintf("%s", user.ID),
	}, nil
}
