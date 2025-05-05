package grpc

import (
	"context"
	"log/slog"
	"net"
	"time"

	"github.com/jyablonski/lotus/internal/db"
	pb_journal "github.com/jyablonski/lotus/internal/pb/proto/journal"
	pb_user "github.com/jyablonski/lotus/internal/pb/proto/user"
	"google.golang.org/grpc"
	"google.golang.org/grpc/peer"
)

func LoggingInterceptor(logger *slog.Logger) grpc.UnaryServerInterceptor {
	return func(
		ctx context.Context,
		req interface{},
		info *grpc.UnaryServerInfo,
		handler grpc.UnaryHandler,
	) (interface{}, error) {
		start := time.Now()
		resp, err := handler(ctx, req)
		duration := time.Since(start)

		attrs := []any{
			"rpc.method", info.FullMethod,
			"rpc.duration_ms", duration.Milliseconds(),
		}

		if peer, ok := peer.FromContext(ctx); ok {
			attrs = append(attrs, "rpc.peer", peer.Addr.String())
		}

		if err != nil {
			attrs = append(attrs, "error", err)
			logger.Error("gRPC call failed", attrs...)
		} else {
			logger.Info("gRPC call succeeded", attrs...)
		}

		return resp, err
	}
}

func StartGRPCServer(queries *db.Queries, logger *slog.Logger) error {
	lis, err := net.Listen("tcp", ":50051")
	if err != nil {
		return err
	}

	// Register gRPC server with the logging interceptor
	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(LoggingInterceptor(logger)), // <- Add this line
	)

	// Register services with logger injected
	pb_user.RegisterUserServiceServer(grpcServer, &UserServer{
		DB:     queries,
		Logger: logger,
	})
	pb_journal.RegisterJournalServiceServer(grpcServer, &JournalServer{
		DB:     queries,
		Logger: logger,
	})

	logger.Info("Starting gRPC server on :50051")
	return grpcServer.Serve(lis)
}
