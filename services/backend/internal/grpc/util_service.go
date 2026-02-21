package grpc

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"

	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/util"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

var (
	ErrGenerateRandomString = errors.New("failed to generate random string")
)

type UtilServer struct {
	pb.UnimplementedUtilServiceServer
}

func (s *UtilServer) GenerateRandomString(ctx context.Context, req *pb.GenerateRandomStringRequest) (*pb.GenerateRandomStringResponse, error) {
	// 16 random bytes -> 32 hex characters
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		logger := inject.LoggerFrom(ctx)
		logger.Error("Failed to generate random bytes", "error", err)
		return nil, status.Error(codes.Internal, ErrGenerateRandomString.Error())
	}

	randomStr := hex.EncodeToString(b)

	logger := inject.LoggerFrom(ctx)
	logger.Info("Generated random string", "length", len(randomStr))

	return &pb.GenerateRandomStringResponse{
		RandomString: randomStr,
	}, nil
}
