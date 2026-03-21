package grpc

import (
	"context"
	"errors"
	"strings"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/featureflag"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

var (
	ErrGetFeatureFlags = errors.New("failed to get feature flags")
)

type FeatureFlagServer struct {
	pb.UnimplementedFeatureFlagServiceServer
}

// isFlagActive evaluates a waffle flag for the given user role.
//   - everyone=true  -> active for all users (short-circuit)
//   - everyone=false -> check superusers, staff, authenticated
func isFlagActive(flag db.SourceWaffleFlag, userRole string) bool {
	if flag.Everyone {
		return true
	}

	isAdmin := strings.EqualFold(userRole, "Admin")

	// Check superusers flag -- in this app, "Admin" role maps to Django superuser.
	if flag.Superusers && isAdmin {
		return true
	}

	// Check staff flag -- "Admin" role also maps to Django staff.
	if flag.Staff && isAdmin {
		return true
	}

	// Check authenticated flag -- all frontend users are authenticated.
	if flag.Authenticated {
		return true
	}

	return false
}

func (s *FeatureFlagServer) GetFeatureFlags(ctx context.Context, req *pb.GetFeatureFlagsRequest) (*pb.GetFeatureFlagsResponse, error) {
	dbq := inject.DBFrom(ctx)
	logger := inject.LoggerFrom(ctx)

	flags, err := dbq.GetActiveFeatureFlags(ctx)
	if err != nil {
		logger.Error("Failed to get feature flags", "error", err)
		return nil, status.Errorf(codes.Internal, "%s: %v", ErrGetFeatureFlags.Error(), err)
	}

	userRole := req.GetUserRole()

	result := make([]*pb.FeatureFlag, 0, len(flags))
	for _, f := range flags {
		result = append(result, &pb.FeatureFlag{
			Name:     f.Name,
			IsActive: isFlagActive(f, userRole),
		})
	}

	return &pb.GetFeatureFlagsResponse{
		Flags: result,
	}, nil
}
