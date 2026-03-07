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
// It mirrors django-waffle's Flag.is_active_for_user() logic:
//   - everyone=true  -> active for all users
//   - everyone=false -> explicitly inactive for all users
//   - everyone=null  -> check superusers, staff, authenticated fields
func isFlagActive(flag db.SourceWaffleFlag, userRole string) bool {
	// If "everyone" is explicitly set, it takes precedence.
	if flag.Everyone.Valid {
		return flag.Everyone.Bool
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

	logger.Info("Feature flags evaluated", "count", len(result), "user_role", userRole)

	return &pb.GetFeatureFlagsResponse{
		Flags: result,
	}, nil
}
