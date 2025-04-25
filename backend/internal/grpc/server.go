package grpc

import (
	"log"
	"net"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/user_pb"
	"google.golang.org/grpc"
)

func StartGRPCServer(queries *db.Queries) error {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		return err
	}

	grpcServer := grpc.NewServer()
	user_pb.RegisterUserServiceServer(grpcServer, &server{db: queries})

	log.Println("Starting gRPC server on :50051")
	return grpcServer.Serve(lis)
}
