package grpc_test

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/featureflag"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newWaffleFlag(name string, everyone, superusers, staff, authenticated bool) db.SourceWaffleFlag {
	now := time.Now()
	ts := pgtype.Timestamptz{Time: now, Valid: true}
	return db.SourceWaffleFlag{
		ID:            1,
		Name:          name,
		Everyone:      everyone,
		Superusers:    superusers,
		Staff:         staff,
		Authenticated: authenticated,
		Created:       ts,
		Modified:      ts,
	}
}

func TestFeatureFlagServer_GetFeatureFlags_Success(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("frontend_maintenance", true, true, false, false),
				newWaffleFlag("frontend_admin", false, true, false, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Admin",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.Flags, 2)

	// frontend_maintenance: everyone=true -> active for all
	assert.Equal(t, "frontend_maintenance", resp.Flags[0].Name)
	assert.True(t, resp.Flags[0].IsActive)

	// frontend_admin: everyone=null, superusers=true, user_role=Admin -> active
	assert.Equal(t, "frontend_admin", resp.Flags[1].Name)
	assert.True(t, resp.Flags[1].IsActive)

	assert.Len(t, mockQuerier.GetActiveFeatureFlagsCalls(), 1)
}

func TestFeatureFlagServer_GetFeatureFlags_EveryoneFalseFallsThrough(t *testing.T) {
	// When everyone=false, role-based checks still apply.
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("admin_flag", false, true, true, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	// Admin should see it active via superusers/staff check
	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Admin",
	})
	require.NoError(t, err)
	require.Len(t, resp.Flags, 1)
	assert.True(t, resp.Flags[0].IsActive)

	// Consumer should see it inactive — no role match
	resp, err = server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Consumer",
	})
	require.NoError(t, err)
	require.Len(t, resp.Flags, 1)
	assert.False(t, resp.Flags[0].IsActive)
}

func TestFeatureFlagServer_GetFeatureFlags_SuperusersOnlyForAdmin(t *testing.T) {
	// superusers=true should only activate for Admin role.
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("admin_only", false, true, false, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	// Admin user should see it active
	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Admin",
	})
	require.NoError(t, err)
	assert.True(t, resp.Flags[0].IsActive)

	// Consumer user should see it inactive
	resp, err = server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Consumer",
	})
	require.NoError(t, err)
	assert.False(t, resp.Flags[0].IsActive)
}

func TestFeatureFlagServer_GetFeatureFlags_StaffFlagForAdmin(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("staff_only", false, false, true, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Admin",
	})
	require.NoError(t, err)
	assert.True(t, resp.Flags[0].IsActive)

	resp, err = server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Consumer",
	})
	require.NoError(t, err)
	assert.False(t, resp.Flags[0].IsActive)
}

func TestFeatureFlagServer_GetFeatureFlags_AuthenticatedForAll(t *testing.T) {
	// authenticated=true should activate for any role.
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("auth_flag", false, false, false, true),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Consumer",
	})
	require.NoError(t, err)
	assert.True(t, resp.Flags[0].IsActive)
}

func TestFeatureFlagServer_GetFeatureFlags_NoFlags(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Consumer",
	})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Empty(t, resp.Flags)
}

func TestFeatureFlagServer_GetFeatureFlags_DBError(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return nil, errors.New("database connection failed")
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Admin",
	})

	require.Error(t, err)
	require.Nil(t, resp)
	assert.Contains(t, err.Error(), "failed to get feature flags")
}

func TestFeatureFlagServer_GetFeatureFlags_EmptyRole(t *testing.T) {
	// When no role is provided, admin-only flags should be inactive.
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("admin_only", false, true, false, false),
				newWaffleFlag("everyone_on", true, false, false, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "",
	})

	require.NoError(t, err)
	require.Len(t, resp.Flags, 2)
	assert.False(t, resp.Flags[0].IsActive) // admin_only: not active for empty role
	assert.True(t, resp.Flags[1].IsActive)  // everyone_on: active for all
}

func TestFeatureFlagServer_GetFeatureFlags_CaseInsensitiveRole(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("admin_flag", false, true, false, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "admin",
	})

	require.NoError(t, err)
	assert.True(t, resp.Flags[0].IsActive)
}

func TestFeatureFlagServer_GetFeatureFlags_AllInactiveForConsumer(t *testing.T) {
	// All flags that rely on superusers/staff should be inactive for a Consumer.
	mockQuerier := &mocks.QuerierMock{
		GetActiveFeatureFlagsFunc: func(ctx context.Context) ([]db.SourceWaffleFlag, error) {
			return []db.SourceWaffleFlag{
				newWaffleFlag("su_only", false, true, false, false),
				newWaffleFlag("staff_only", false, false, true, false),
			}, nil
		},
	}

	server := &internalgrpc.FeatureFlagServer{}

	resp, err := server.GetFeatureFlags(testCtx(mockQuerier), &pb.GetFeatureFlagsRequest{
		UserRole: "Consumer",
	})

	require.NoError(t, err)
	for _, f := range resp.Flags {
		assert.False(t, f.IsActive, "flag %s should be inactive for Consumer", f.Name)
	}
}
