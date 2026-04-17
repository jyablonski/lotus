package grpc

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
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

	// Example of reading and writing runtime_config. Reads the current value and
	// logs the last run timestamp if set, then writes an updated timestamp below.
	config, err := dbq.GetRuntimeConfigByKey(ctx, runtimeConfigKey)
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		logger.Error("Failed to read runtime config", "key", runtimeConfigKey, "error", err)
		return nil, status.Error(codes.Internal, "failed to read runtime config")
	}

	if errors.Is(err, pgx.ErrNoRows) {
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

	b := make([]byte, 16)
	_, err = rand.Read(b)
	if err != nil {
		logger.Error("Failed to generate random bytes", "error", err)
		return nil, status.Error(codes.Internal, ErrGenerateRandomString.Error())
	}

	randomStr := hex.EncodeToString(b)
	logger.Info("Generated random string", "length", len(randomStr))

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
