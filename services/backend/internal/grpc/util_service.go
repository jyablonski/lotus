package grpc

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"log/slog"

	pb "github.com/jyablonski/lotus/internal/pb/proto/util"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type UtilServer struct {
	pb.UnimplementedUtilServiceServer
	Logger *slog.Logger
}

func UtilService(logger *slog.Logger) *UtilServer {
	return &UtilServer{
		Logger: logger,
	}
}

func (s *UtilServer) GenerateRandomString(ctx context.Context, req *pb.GenerateRandomStringRequest) (*pb.GenerateRandomStringResponse, error) {
	// 16 random bytes -> 32 hex characters
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		s.Logger.Error("Failed to generate random bytes", "error", err)
		return nil, status.Errorf(codes.Internal, "failed to generate random string")
	}

	randomStr := hex.EncodeToString(b)

	s.Logger.Info("Generated random string", "length", len(randomStr))

	return &pb.GenerateRandomStringResponse{
		RandomString: randomStr,
	}, nil
}
