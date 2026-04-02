package grpc_test

import (
	"context"
	"database/sql"
	"errors"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/game"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestGameServer_GetGameBalance(t *testing.T) {
	server := &internalgrpc.GameServer{}

	t.Run("success", func(t *testing.T) {
		userID := uuid.New()
		balance := int32(250)

		mockQuerier := &mocks.QuerierMock{
			GetUserGameBalanceFunc: func(ctx context.Context, uid uuid.UUID) (db.SourceUserGameBalance, error) {
				assert.Equal(t, userID, uid)
				return db.SourceUserGameBalance{
					ID:         1,
					UserID:     userID,
					Balance:    balance,
					CreatedAt:  time.Now(),
					ModifiedAt: time.Now(),
				}, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetGameBalanceRequest{UserId: userID.String()}
		resp, err := server.GetGameBalance(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Equal(t, userID.String(), resp.UserId)
		assert.Equal(t, balance, resp.Balance)
		assert.Len(t, mockQuerier.GetUserGameBalanceCalls(), 1)
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 0)
	})

	t.Run("first_visit_seeds_default", func(t *testing.T) {
		userID := uuid.New()

		mockQuerier := &mocks.QuerierMock{
			GetUserGameBalanceFunc: func(ctx context.Context, uid uuid.UUID) (db.SourceUserGameBalance, error) {
				return db.SourceUserGameBalance{}, sql.ErrNoRows
			},
			UpsertUserGameBalanceFunc: func(ctx context.Context, arg db.UpsertUserGameBalanceParams) (db.SourceUserGameBalance, error) {
				assert.Equal(t, userID, arg.UserID)
				assert.Equal(t, int32(100), arg.Balance)
				return db.SourceUserGameBalance{
					ID:         1,
					UserID:     userID,
					Balance:    100,
					CreatedAt:  time.Now(),
					ModifiedAt: time.Now(),
				}, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetGameBalanceRequest{UserId: userID.String()}
		resp, err := server.GetGameBalance(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Equal(t, userID.String(), resp.UserId)
		assert.Equal(t, int32(100), resp.Balance)
		assert.Len(t, mockQuerier.GetUserGameBalanceCalls(), 1)
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 1)
	})

	t.Run("invalid_user_id", func(t *testing.T) {
		mockQuerier := &mocks.QuerierMock{}
		ctx := testCtx(mockQuerier)
		req := &pb.GetGameBalanceRequest{UserId: "not-a-uuid"}

		resp, err := server.GetGameBalance(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.True(t, errors.Is(err, internalgrpc.ErrInvalidUserID))
		assert.Len(t, mockQuerier.GetUserGameBalanceCalls(), 0)
	})

	t.Run("db_error", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			GetUserGameBalanceFunc: func(ctx context.Context, uid uuid.UUID) (db.SourceUserGameBalance, error) {
				return db.SourceUserGameBalance{}, errors.New("connection refused")
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetGameBalanceRequest{UserId: userID.String()}
		resp, err := server.GetGameBalance(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.Contains(t, err.Error(), "failed to get game balance")
		assert.Len(t, mockQuerier.GetUserGameBalanceCalls(), 1)
	})

	t.Run("first_visit_upsert_error", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			GetUserGameBalanceFunc: func(ctx context.Context, uid uuid.UUID) (db.SourceUserGameBalance, error) {
				return db.SourceUserGameBalance{}, sql.ErrNoRows
			},
			UpsertUserGameBalanceFunc: func(ctx context.Context, arg db.UpsertUserGameBalanceParams) (db.SourceUserGameBalance, error) {
				return db.SourceUserGameBalance{}, errors.New("unique violation")
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetGameBalanceRequest{UserId: userID.String()}
		resp, err := server.GetGameBalance(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.Contains(t, err.Error(), "failed to seed game balance")
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 1)
	})
}

func TestGameServer_RecordBets_InvalidUserID(t *testing.T) {
	server := &internalgrpc.GameServer{}
	mockQuerier := &mocks.QuerierMock{}
	ctx := testCtx(mockQuerier)
	req := &pb.RecordBetsRequest{
		UserId: "bad-uuid",
		Bets:   []*pb.BetEntry{{Zone: "red", Amount: 1, RollResult: 7, Payout: 2}},
	}

	resp, err := server.RecordBets(ctx, req)

	require.Error(t, err)
	require.Nil(t, resp)
	assert.True(t, errors.Is(err, internalgrpc.ErrInvalidUserID))
}

func TestGameServer_GetBetHistory(t *testing.T) {
	server := &internalgrpc.GameServer{}

	t.Run("success", func(t *testing.T) {
		userID := uuid.New()
		now := time.Now()
		mockQuerier := &mocks.QuerierMock{
			GetUserGameBetsFunc: func(ctx context.Context, arg db.GetUserGameBetsParams) ([]db.SourceUserGameBet, error) {
				assert.Equal(t, userID, arg.UserID)
				assert.Equal(t, int32(20), arg.Limit)
				assert.Equal(t, int32(0), arg.Offset)
				return []db.SourceUserGameBet{
					{
						ID:         1,
						UserID:     userID,
						Zone:       "red",
						Amount:     10,
						RollResult: 7,
						Payout:     20,
						CreatedAt:  now,
					},
				}, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 20, Offset: 0}
		resp, err := server.GetBetHistory(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		require.Len(t, resp.Bets, 1)
		assert.Equal(t, int32(1), resp.Bets[0].Id)
		assert.Equal(t, "red", resp.Bets[0].Zone)
		assert.Equal(t, int32(10), resp.Bets[0].Amount)
		assert.Equal(t, int32(7), resp.Bets[0].RollResult)
		assert.Equal(t, int32(20), resp.Bets[0].Payout)
		assert.Equal(t, now.Format("2006-01-02T15:04:05Z"), resp.Bets[0].CreatedAt)
		assert.Len(t, mockQuerier.GetUserGameBetsCalls(), 1)
	})

	t.Run("invalid_user_id", func(t *testing.T) {
		mockQuerier := &mocks.QuerierMock{}
		ctx := testCtx(mockQuerier)
		req := &pb.GetBetHistoryRequest{UserId: "not-a-uuid", Limit: 10, Offset: 0}

		resp, err := server.GetBetHistory(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.True(t, errors.Is(err, internalgrpc.ErrInvalidUserID))
		assert.Len(t, mockQuerier.GetUserGameBetsCalls(), 0)
	})

	t.Run("limit_clamped_when_zero", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			GetUserGameBetsFunc: func(ctx context.Context, arg db.GetUserGameBetsParams) ([]db.SourceUserGameBet, error) {
				assert.Equal(t, int32(20), arg.Limit)
				return nil, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 0, Offset: 0}
		resp, err := server.GetBetHistory(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Len(t, mockQuerier.GetUserGameBetsCalls(), 1)
	})

	t.Run("limit_clamped_when_over_100", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			GetUserGameBetsFunc: func(ctx context.Context, arg db.GetUserGameBetsParams) ([]db.SourceUserGameBet, error) {
				assert.Equal(t, int32(20), arg.Limit)
				return nil, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 500, Offset: 0}
		resp, err := server.GetBetHistory(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Len(t, mockQuerier.GetUserGameBetsCalls(), 1)
	})

	t.Run("db_error", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			GetUserGameBetsFunc: func(ctx context.Context, arg db.GetUserGameBetsParams) ([]db.SourceUserGameBet, error) {
				return nil, errors.New("query failed")
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 10, Offset: 0}
		resp, err := server.GetBetHistory(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.Contains(t, err.Error(), "failed to get bet history")
		assert.Len(t, mockQuerier.GetUserGameBetsCalls(), 1)
	})
}

func TestGameServer_UpdateGameBalance(t *testing.T) {
	server := &internalgrpc.GameServer{}

	t.Run("success", func(t *testing.T) {
		userID := uuid.New()
		balance := int32(500)
		mockQuerier := &mocks.QuerierMock{
			UpsertUserGameBalanceFunc: func(ctx context.Context, arg db.UpsertUserGameBalanceParams) (db.SourceUserGameBalance, error) {
				assert.Equal(t, userID, arg.UserID)
				assert.Equal(t, balance, arg.Balance)
				return db.SourceUserGameBalance{
					ID:         1,
					UserID:     userID,
					Balance:    balance,
					CreatedAt:  time.Now(),
					ModifiedAt: time.Now(),
				}, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: balance}
		resp, err := server.UpdateGameBalance(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Equal(t, userID.String(), resp.UserId)
		assert.Equal(t, balance, resp.Balance)
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 1)
	})

	t.Run("invalid_user_id", func(t *testing.T) {
		mockQuerier := &mocks.QuerierMock{}
		ctx := testCtx(mockQuerier)
		req := &pb.UpdateGameBalanceRequest{UserId: "invalid", Balance: 100}

		resp, err := server.UpdateGameBalance(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.True(t, errors.Is(err, internalgrpc.ErrInvalidUserID))
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 0)
	})

	t.Run("negative_balance", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{}
		ctx := testCtx(mockQuerier)
		req := &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: -1}

		resp, err := server.UpdateGameBalance(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.True(t, errors.Is(err, internalgrpc.ErrInvalidBalance))
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 0)
	})

	t.Run("zero_allowed", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			UpsertUserGameBalanceFunc: func(ctx context.Context, arg db.UpsertUserGameBalanceParams) (db.SourceUserGameBalance, error) {
				assert.Equal(t, int32(0), arg.Balance)
				return db.SourceUserGameBalance{
					ID:         1,
					UserID:     userID,
					Balance:    0,
					CreatedAt:  time.Now(),
					ModifiedAt: time.Now(),
				}, nil
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: 0}
		resp, err := server.UpdateGameBalance(ctx, req)

		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Equal(t, int32(0), resp.Balance)
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 1)
	})

	t.Run("db_error", func(t *testing.T) {
		userID := uuid.New()
		mockQuerier := &mocks.QuerierMock{
			UpsertUserGameBalanceFunc: func(ctx context.Context, arg db.UpsertUserGameBalanceParams) (db.SourceUserGameBalance, error) {
				return db.SourceUserGameBalance{}, errors.New("upsert failed")
			},
		}

		ctx := testCtx(mockQuerier)
		req := &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: 100}
		resp, err := server.UpdateGameBalance(ctx, req)

		require.Error(t, err)
		require.Nil(t, resp)
		assert.Contains(t, err.Error(), "failed to update game balance")
		assert.Len(t, mockQuerier.UpsertUserGameBalanceCalls(), 1)
	})
}
