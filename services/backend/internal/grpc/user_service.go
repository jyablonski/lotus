package grpc

import (
	"context"
	"errors"
	"log/slog"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/user"
	"github.com/jyablonski/lotus/internal/utils"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

var (
	ErrEmailRequired   = errors.New("email is required")
	ErrUserNotFound    = errors.New("user not found")
	ErrCreateUser      = errors.New("could not create user")
	ErrHashPassword    = errors.New("failed to hash password")
	ErrGetUserFailed   = errors.New("failed to get user")
	ErrInvalidTimezone = errors.New("invalid timezone")
	ErrUpdateTimezone  = errors.New("failed to update timezone")
	ErrUpdateCommunity = errors.New("failed to update community settings")
)

type UserServer struct {
	pb.UnimplementedUserServiceServer
}

// CreateUser handles username/password-based user creation.
func (s *UserServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
	logger := inject.LoggerFrom(ctx)
	dbq := inject.DBFrom(ctx)

	// Hash the password using bcrypt (salt is embedded in the hash).
	hashedPassword, err := utils.HashPassword(req.Password)
	if err != nil {
		logger.Error("Failed to hash password", "error", err)
		return nil, status.Error(codes.Internal, ErrHashPassword.Error())
	}

	user, err := dbq.CreateUser(ctx, db.CreateUserParams{
		Email:    req.Email,
		Password: &hashedPassword,
		Salt:     nil,
	})
	if err != nil {
		logger.Error("Failed to create user", "email", req.Email, "error", err)
		return nil, status.Error(codes.Internal, ErrCreateUser.Error())
	}

	logger.Info("User created successfully", "user_id", user.ID.String(), "email", req.Email)

	return &pb.CreateUserResponse{
		UserId: user.ID.String(),
	}, nil
}

// CreateUserOauth handles OAuth-based user creation.
func (s *UserServer) CreateUserOauth(ctx context.Context, req *pb.CreateUserOauthRequest) (*pb.CreateUserResponse, error) {
	logger := inject.LoggerFrom(ctx)
	dbq := inject.DBFrom(ctx)

	// create a structured log w/ `time: xxx`, `level`, `msg`, and `user_info`:`
	// "user_info":{"email":"user_oauth2@email.com","oauth_provider":"github"}}
	logger.Info("CreateUser request received",
		slog.Group("user_info",
			slog.String("email", req.Email),
			slog.String("oauth_provider", "github"),
		),
	)

	oauthProvider := req.OauthProvider

	user, err := dbq.CreateUserOauth(ctx, db.CreateUserOauthParams{
		Email:         req.Email,
		OauthProvider: &oauthProvider,
	})
	if err != nil {
		logger.Error("Failed to create OAuth user", "email", req.Email, "error", err)
		return nil, status.Error(codes.Internal, ErrCreateUser.Error())
	}

	return &pb.CreateUserResponse{
		UserId: user.ID.String(),
	}, nil
}

func (s *UserServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
	email := req.GetEmail()
	if email == "" {
		return nil, status.Error(codes.InvalidArgument, ErrEmailRequired.Error())
	}

	// Extract deps after input validation
	dbq := inject.DBFrom(ctx)

	u, err := dbq.GetUserByEmail(ctx, email)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, status.Error(codes.NotFound, ErrUserNotFound.Error())
		}
		return nil, status.Errorf(codes.Internal, "%s: %v", ErrGetUserFailed.Error(), err)
	}

	createdAt := ""
	if u.CreatedAt.Valid {
		createdAt = u.CreatedAt.Time.Format("2006-01-02T15:04:05Z07:00")
	}
	updatedAt := ""
	if u.ModifiedAt.Valid {
		updatedAt = u.ModifiedAt.Time.Format("2006-01-02T15:04:05Z07:00")
	}

	return &pb.GetUserResponse{
		UserId:                 u.ID.String(),
		Email:                  u.Email,
		Role:                   u.Role,
		Timezone:               u.Timezone,
		CreatedAt:              createdAt,
		UpdatedAt:              updatedAt,
		CommunityInsightsOptIn: u.CommunityInsightsOptIn,
		CommunityLocationOptIn: u.CommunityLocationOptIn,
		CommunityCountryCode:   stringOrEmpty(u.CommunityCountryCode),
		CommunityRegionCode:    stringOrEmpty(u.CommunityRegionCode),
	}, nil
}

func (s *UserServer) UpdateUserTimezone(ctx context.Context, req *pb.UpdateUserTimezoneRequest) (*pb.UpdateUserTimezoneResponse, error) {
	logger := inject.LoggerFrom(ctx)

	// Validate user ID
	userID, err := uuid.Parse(req.GetUserId())
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, ErrInvalidUserID.Error())
	}

	// Validate timezone is a valid IANA timezone name
	tz := req.GetTimezone()
	if _, err := time.LoadLocation(tz); err != nil {
		return nil, status.Error(codes.InvalidArgument, ErrInvalidTimezone.Error())
	}

	dbq := inject.DBFrom(ctx)

	u, err := dbq.UpdateUserTimezone(ctx, db.UpdateUserTimezoneParams{
		ID:       pgtype.UUID{Bytes: userID, Valid: true},
		Timezone: tz,
	})
	if err != nil {
		logger.Error("Failed to update user timezone", "user_id", req.GetUserId(), "timezone", tz, "error", err)
		return nil, status.Error(codes.Internal, ErrUpdateTimezone.Error())
	}

	logger.Info("User timezone updated", "user_id", u.ID.String(), "timezone", u.Timezone)

	updatedAt := ""
	if u.ModifiedAt.Valid {
		updatedAt = u.ModifiedAt.Time.Format(time.RFC3339)
	}

	return &pb.UpdateUserTimezoneResponse{
		UserId:    u.ID.String(),
		Timezone:  u.Timezone,
		UpdatedAt: updatedAt,
	}, nil
}

func (s *UserServer) UpdateCommunitySettings(ctx context.Context, req *pb.UpdateCommunitySettingsRequest) (*pb.UpdateCommunitySettingsResponse, error) {
	logger := inject.LoggerFrom(ctx)

	userID, err := uuid.Parse(req.GetUserId())
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, ErrInvalidUserID.Error())
	}

	dbq := inject.DBFrom(ctx)

	u, err := dbq.UpdateCommunitySettingsByUserId(ctx, db.UpdateCommunitySettingsByUserIdParams{
		ID:                     pgtype.UUID{Bytes: userID, Valid: true},
		CommunityInsightsOptIn: req.GetCommunityInsightsOptIn(),
		CommunityLocationOptIn: req.GetCommunityLocationOptIn(),
		CommunityCountryCode:   normalizeOptionalString(req.GetCommunityCountryCode()),
		CommunityRegionCode:    normalizeOptionalString(req.GetCommunityRegionCode()),
	})
	if err != nil {
		logger.Error("Failed to update community settings", "user_id", req.GetUserId(), "error", err)
		return nil, status.Error(codes.Internal, ErrUpdateCommunity.Error())
	}

	updatedAt := ""
	if u.ModifiedAt.Valid {
		updatedAt = u.ModifiedAt.Time.Format(time.RFC3339)
	}

	return &pb.UpdateCommunitySettingsResponse{
		UserId:                 u.ID.String(),
		CommunityInsightsOptIn: u.CommunityInsightsOptIn,
		CommunityLocationOptIn: u.CommunityLocationOptIn,
		CommunityCountryCode:   stringOrEmpty(u.CommunityCountryCode),
		CommunityRegionCode:    stringOrEmpty(u.CommunityRegionCode),
		UpdatedAt:              updatedAt,
	}, nil
}

func normalizeOptionalString(value string) *string {
	if value == "" {
		return nil
	}
	return &value
}

func stringOrEmpty(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}
