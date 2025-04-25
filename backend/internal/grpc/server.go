package grpc

import (
	"log"
	"net"

	"github.com/jyablonski/lotus/internal/db"
	pb "github.com/jyablonski/lotus/internal/user_pb/proto/user"
	"google.golang.org/grpc"
)

func StartGRPCServer(queries *db.Queries) error {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		return err
	}

	grpcServer := grpc.NewServer()
	pb.RegisterUserServiceServer(grpcServer, &Server{DB: queries})

	log.Println("Starting gRPC server on :50051")
	return grpcServer.Serve(lis)
}
