package grpc

import (
	"log"
	"net"

	"github.com/jyablonski/lotus/internal/db"
	pb_journal "github.com/jyablonski/lotus/internal/pb/proto/journal"
	pb_user "github.com/jyablonski/lotus/internal/pb/proto/user"
	"google.golang.org/grpc"
)

func StartGRPCServer(queries *db.Queries) error {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		return err
	}

	grpcServer := grpc.NewServer()

	pb_user.RegisterUserServiceServer(grpcServer, &UserServer{DB: queries})          // Register UserService
	pb_journal.RegisterJournalServiceServer(grpcServer, &JournalServer{DB: queries}) // Register JournalService

	log.Println("Starting gRPC server on :50051")
	return grpcServer.Serve(lis)
}
