package grpc_test

import (
	"context"
	"testing"

	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/util"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestUtilServer_GenerateRandomString_Success(t *testing.T) {
	server := &internalgrpc.UtilServer{}

	resp, err := server.GenerateRandomString(context.Background(), &pb.GenerateRandomStringRequest{})

	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Len(t, resp.RandomString, 32)
}

func TestUtilServer_GenerateRandomString_IsHex(t *testing.T) {
	server := &internalgrpc.UtilServer{}

	resp, err := server.GenerateRandomString(context.Background(), &pb.GenerateRandomStringRequest{})

	require.NoError(t, err)
	require.NotNil(t, resp)

	// Verify the string only contains valid hex characters
	for _, c := range resp.RandomString {
		assert.True(t, (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'), "expected hex character, got %c", c)
	}
}

func TestUtilServer_GenerateRandomString_Unique(t *testing.T) {
	server := &internalgrpc.UtilServer{}

	resp1, err := server.GenerateRandomString(context.Background(), &pb.GenerateRandomStringRequest{})
	require.NoError(t, err)

	resp2, err := server.GenerateRandomString(context.Background(), &pb.GenerateRandomStringRequest{})
	require.NoError(t, err)

	// Two calls should produce different strings (extremely unlikely to collide)
	assert.NotEqual(t, resp1.RandomString, resp2.RandomString)
}
