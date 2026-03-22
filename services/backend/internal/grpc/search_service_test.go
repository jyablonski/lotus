package grpc_test

import (
	"testing"

	"github.com/google/uuid"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/journal"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestKeywordSearchJournals_InvalidUserID(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	req := &pb.KeywordSearchJournalsRequest{
		UserId: "invalid-uuid",
		Query:  "test",
	}
	resp, err := server.KeywordSearchJournals(journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient()), req)
	require.Error(t, err)
	require.Nil(t, resp)
	assert.ErrorIs(t, err, internalgrpc.ErrInvalidUserID)
}

func TestKeywordSearchJournals_EmptyQuery(t *testing.T) {
	server := &internalgrpc.JournalServer{}
	ctx := journalTestCtx(&mocks.QuerierMock{}, noopHTTPClient())
	ctx = withRiverDeps(ctx)

	req := &pb.KeywordSearchJournalsRequest{
		UserId: uuid.New().String(),
		Query:  "",
	}
	resp, err := server.KeywordSearchJournals(ctx, req)
	require.NoError(t, err)
	require.NotNil(t, resp)
	assert.Empty(t, resp.Results)
}
