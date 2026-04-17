package grpc_test

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/util"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newRuntimeConfigMock(lastRunTimestamp string) *mocks.QuerierMock {
	configValue, _ := json.Marshal(map[string]interface{}{
		"ENABLED":            false,
		"LAST_RUN_TIMESTAMP": lastRunTimestamp,
	})

	now := time.Now()
	ts := pgtype.Timestamp{Time: now, Valid: true}
	return &mocks.QuerierMock{
		GetRuntimeConfigByKeyFunc: func(ctx context.Context, key string) (db.SourceRuntimeConfig, error) {
			return db.SourceRuntimeConfig{
				ID:          1,
				Key:         "go_config_example",
				Value:       configValue,
				Service:     "backend",
				Description: "Runtime config managed by GenerateRandomString",
				CreatedAt:   ts,
				ModifiedAt:  ts,
			}, nil
		},
		UpsertRuntimeConfigValueFunc: func(ctx context.Context, arg db.UpsertRuntimeConfigValueParams) (db.SourceRuntimeConfig, error) {
			return db.SourceRuntimeConfig{
				ID:          1,
				Key:         arg.Key,
				Value:       arg.Value,
				Service:     arg.Service,
				Description: arg.Description,
				CreatedAt:   ts,
				ModifiedAt:  ts,
			}, nil
		},
	}
}

func TestUtilServer_GenerateRandomString_Success(t *testing.T) {
	mockQuerier := newRuntimeConfigMock("2026-02-26T10:10:10Z")
	server := &internalgrpc.UtilServer{}

	resp, err := server.GenerateRandomString(testCtx(mockQuerier), &pb.GenerateRandomStringRequest{})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.RandomString, 32)

	assert.Len(t, mockQuerier.GetRuntimeConfigByKeyCalls(), 1)
	assert.Equal(t, "go_config_example", mockQuerier.GetRuntimeConfigByKeyCalls()[0].Key)
	assert.Len(t, mockQuerier.UpsertRuntimeConfigValueCalls(), 1)
	assert.Equal(t, "go_config_example", mockQuerier.UpsertRuntimeConfigValueCalls()[0].Arg.Key)
	assert.Equal(t, "backend", mockQuerier.UpsertRuntimeConfigValueCalls()[0].Arg.Service)
}

func TestUtilServer_GenerateRandomString_IsHex(t *testing.T) {
	mockQuerier := newRuntimeConfigMock("2026-02-26T10:10:10Z")
	server := &internalgrpc.UtilServer{}

	resp, err := server.GenerateRandomString(testCtx(mockQuerier), &pb.GenerateRandomStringRequest{})

	require.NoError(t, err)
	require.NotNil(t, resp)

	for _, c := range resp.RandomString {
		assert.True(t, (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'), "expected hex character, got %c", c)
	}
}

func TestUtilServer_GenerateRandomString_Unique(t *testing.T) {
	mockQuerier := newRuntimeConfigMock("2026-02-26T10:10:10Z")
	server := &internalgrpc.UtilServer{}
	ctx := testCtx(mockQuerier)

	resp1, err := server.GenerateRandomString(ctx, &pb.GenerateRandomStringRequest{})
	require.NoError(t, err)

	resp2, err := server.GenerateRandomString(ctx, &pb.GenerateRandomStringRequest{})
	require.NoError(t, err)

	assert.NotEqual(t, resp1.RandomString, resp2.RandomString)
}

func TestUtilServer_GenerateRandomString_NoExistingConfig(t *testing.T) {
	mockQuerier := &mocks.QuerierMock{
		GetRuntimeConfigByKeyFunc: func(ctx context.Context, key string) (db.SourceRuntimeConfig, error) {
			return db.SourceRuntimeConfig{}, pgx.ErrNoRows
		},
		UpsertRuntimeConfigValueFunc: func(ctx context.Context, arg db.UpsertRuntimeConfigValueParams) (db.SourceRuntimeConfig, error) {
			now := time.Now()
			ts := pgtype.Timestamp{Time: now, Valid: true}
			return db.SourceRuntimeConfig{
				ID:          1,
				Key:         arg.Key,
				Value:       arg.Value,
				Service:     arg.Service,
				Description: arg.Description,
				CreatedAt:   ts,
				ModifiedAt:  ts,
			}, nil
		},
	}

	server := &internalgrpc.UtilServer{}

	resp, err := server.GenerateRandomString(testCtx(mockQuerier), &pb.GenerateRandomStringRequest{})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.RandomString, 32)
	assert.Len(t, mockQuerier.UpsertRuntimeConfigValueCalls(), 1)
}

func TestUtilServer_GenerateRandomString_WritesUpdatedTimestamp(t *testing.T) {
	mockQuerier := newRuntimeConfigMock("2026-01-01T00:00:00Z")
	server := &internalgrpc.UtilServer{}

	before := time.Now().UTC().Truncate(time.Second)
	resp, err := server.GenerateRandomString(testCtx(mockQuerier), &pb.GenerateRandomStringRequest{})
	after := time.Now().UTC().Add(time.Second).Truncate(time.Second)

	require.NoError(t, err)
	require.NotNil(t, resp)

	upsertCall := mockQuerier.UpsertRuntimeConfigValueCalls()[0]
	var written map[string]interface{}
	err = json.Unmarshal(upsertCall.Arg.Value, &written)
	require.NoError(t, err)

	ts, err := time.Parse(time.RFC3339, written["LAST_RUN_TIMESTAMP"].(string))
	require.NoError(t, err)
	assert.True(t, !ts.Before(before) && !ts.After(after), "timestamp should be between test start and end")
	assert.Equal(t, true, written["ENABLED"])
}
