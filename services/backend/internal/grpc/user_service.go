package grpc

import (
	"context"
	"database/sql"
	"errors"
	"log/slog"
	"time"

	"github.com/google/uuid"
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
		Password: sql.NullString{String: hashedPassword, Valid: true},
		Salt:     sql.NullString{Valid: false}, // bcrypt embeds its own salt
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

	// For OAuth, no password is required; we store the email and OAuth provider.
	// Using sql.NullString for nullable OAuth provider field
	oauthProvider := sql.NullString{String: req.OauthProvider, Valid: true}

	user, err := dbq.CreateUserOauth(ctx, db.CreateUserOauthParams{
		Email:         req.Email,
		OauthProvider: oauthProvider, // e.g., "github"
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
		if err == sql.ErrNoRows {
			return nil, status.Error(codes.NotFound, ErrUserNotFound.Error())
		}
		return nil, status.Errorf(codes.Internal, "%s: %v", ErrGetUserFailed.Error(), err)
	}

	return &pb.GetUserResponse{
		UserId:    u.ID.String(),
		Email:     u.Email,
		Role:      u.Role,
		Timezone:  u.Timezone,
		CreatedAt: u.CreatedAt.Format("2006-01-02T15:04:05Z07:00"),
		UpdatedAt: u.ModifiedAt.Format("2006-01-02T15:04:05Z07:00"),
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
		ID:       userID,
		Timezone: tz,
	})
	if err != nil {
		logger.Error("Failed to update user timezone", "user_id", req.GetUserId(), "timezone", tz, "error", err)
		return nil, status.Error(codes.Internal, ErrUpdateTimezone.Error())
	}

	logger.Info("User timezone updated", "user_id", u.ID.String(), "timezone", u.Timezone)

	return &pb.UpdateUserTimezoneResponse{
		UserId:    u.ID.String(),
		Timezone:  u.Timezone,
		UpdatedAt: u.ModifiedAt.Format(time.RFC3339),
	}, nil
}
