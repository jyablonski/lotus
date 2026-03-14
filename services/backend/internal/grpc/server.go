package grpc

import (
	"context"
	"log/slog"
	"time"

	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	pb_analytics "github.com/jyablonski/lotus/internal/pb/proto/analytics"
	pb_featureflag "github.com/jyablonski/lotus/internal/pb/proto/featureflag"
	pb_game "github.com/jyablonski/lotus/internal/pb/proto/game"
	pb_journal "github.com/jyablonski/lotus/internal/pb/proto/journal"
	pb_user "github.com/jyablonski/lotus/internal/pb/proto/user"
	pb_util "github.com/jyablonski/lotus/internal/pb/proto/util"
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

// RegisterServices registers all gRPC service implementations on the given
// server. Services are empty structs that pull dependencies from context
// via the inject package (populated by the injector interceptor in main).
func RegisterServices(s *grpc.Server) {
	pb_user.RegisterUserServiceServer(s, &UserServer{})
	pb_journal.RegisterJournalServiceServer(s, &JournalServer{})
	pb_analytics.RegisterAnalyticsServiceServer(s, &AnalyticsServer{})
	pb_util.RegisterUtilServiceServer(s, &UtilServer{})
	pb_featureflag.RegisterFeatureFlagServiceServer(s, &FeatureFlagServer{})
	pb_game.RegisterGameServiceServer(s, &GameServer{})
}

// RegisterGateway registers all gRPC-Gateway HTTP handlers on the given mux.
// This keeps all service registration in one package so that main.go doesn't
// need to import every protobuf package individually.
func RegisterGateway(ctx context.Context, mux *runtime.ServeMux, endpoint string, opts []grpc.DialOption) error {
	for _, reg := range []func(context.Context, *runtime.ServeMux, string, []grpc.DialOption) error{
		pb_user.RegisterUserServiceHandlerFromEndpoint,
		pb_journal.RegisterJournalServiceHandlerFromEndpoint,
		pb_analytics.RegisterAnalyticsServiceHandlerFromEndpoint,
		pb_util.RegisterUtilServiceHandlerFromEndpoint,
		pb_featureflag.RegisterFeatureFlagServiceHandlerFromEndpoint,
		pb_game.RegisterGameServiceHandlerFromEndpoint,
	} {
		if err := reg(ctx, mux, endpoint, opts); err != nil {
			return err
		}
	}
	return nil
}
