package grpc

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"time"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/util"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

const runtimeConfigKey = "go_config_example"

var (
	ErrGenerateRandomString = errors.New("failed to generate random string")
)

type UtilServer struct {
	pb.UnimplementedUtilServiceServer
}

// runtimeConfigValue represents the JSON structure stored in the runtime_config value
// for the "go_config_example" key.
type runtimeConfigValue struct {
	Enabled          bool   `json:"ENABLED"`
	LastRunTimestamp string `json:"LAST_RUN_TIMESTAMP"`
}

func (s *UtilServer) GenerateRandomString(ctx context.Context, req *pb.GenerateRandomStringRequest) (*pb.GenerateRandomStringResponse, error) {
	logger := inject.LoggerFrom(ctx)
	dbq := inject.DBFrom(ctx)

	// This is just an example of how to read and write from the runtime_config table
	// Read the current runtime config for the "ml" key and log the last run timestamp
	config, err := dbq.GetRuntimeConfigByKey(ctx, runtimeConfigKey)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		logger.Error("Failed to read runtime config", "key", runtimeConfigKey, "error", err)
		return nil, status.Error(codes.Internal, "failed to read runtime config")
	}

	if errors.Is(err, sql.ErrNoRows) {
		logger.Info("No runtime config found, first run", "key", runtimeConfigKey)
	} else {
		var configVal runtimeConfigValue
		if err := json.Unmarshal(config.Value, &configVal); err != nil {
			logger.Error("Failed to unmarshal runtime config value", "key", runtimeConfigKey, "error", err)
		} else {
			logger.Info("Runtime config loaded",
				"key", runtimeConfigKey,
				"last_run_timestamp", configVal.LastRunTimestamp,
				"enabled", configVal.Enabled,
			)
		}
	}

	// Generate random string (16 random bytes -> 32 hex characters)
	b := make([]byte, 16)
	_, err = rand.Read(b)
	if err != nil {
		logger.Error("Failed to generate random bytes", "error", err)
		return nil, status.Error(codes.Internal, ErrGenerateRandomString.Error())
	}

	randomStr := hex.EncodeToString(b)
	logger.Info("Generated random string", "length", len(randomStr))

	// Write updated LAST_RUN_TIMESTAMP back to the runtime config
	now := time.Now().UTC().Format(time.RFC3339)
	updatedVal := runtimeConfigValue{
		Enabled:          true,
		LastRunTimestamp: now,
	}

	updatedJSON, err := json.Marshal(updatedVal)
	if err != nil {
		logger.Error("Failed to marshal updated runtime config value", "error", err)
		return nil, status.Error(codes.Internal, "failed to update runtime config")
	}

	_, err = dbq.UpsertRuntimeConfigValue(ctx, db.UpsertRuntimeConfigValueParams{
		Key:         runtimeConfigKey,
		Value:       updatedJSON,
		Service:     "backend",
		Description: "Runtime config managed by GenerateRandomString",
	})
	if err != nil {
		logger.Error("Failed to write runtime config", "key", runtimeConfigKey, "error", err)
		return nil, status.Error(codes.Internal, "failed to update runtime config")
	}

	logger.Info("Updated runtime config", "key", runtimeConfigKey, "last_run_timestamp", now)

	return &pb.GenerateRandomStringResponse{
		RandomString: randomStr,
	}, nil
}
