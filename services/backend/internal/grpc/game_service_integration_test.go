package grpc_test

import (
	"context"
	"testing"

	"github.com/jyablonski/lotus/internal/db"
	grpcServer "github.com/jyablonski/lotus/internal/grpc"
	pb "github.com/jyablonski/lotus/internal/pb/proto/game"
	"github.com/stretchr/testify/require"
)

func TestIntegration_GetGameBalance(t *testing.T) {
	t.Run("first_visit_seeds_default", func(t *testing.T) {
		ctx, queries := newTestCtx(t)
		userID := createTestUser(t, queries)
		svc := &grpcServer.GameServer{}

		resp, err := svc.GetGameBalance(ctx, &pb.GetGameBalanceRequest{UserId: userID.String()})
		require.NoError(t, err)
		require.NotNil(t, resp)
		require.Equal(t, userID.String(), resp.UserId)
		require.Equal(t, int32(100), resp.Balance)

		row, err := queries.GetUserGameBalance(ctx, userID)
		require.NoError(t, err)
		require.Equal(t, int32(100), row.Balance)
	})

	t.Run("existing_balance", func(t *testing.T) {
		ctx, queries := newTestCtx(t)
		userID := createTestUser(t, queries)
		svc := &grpcServer.GameServer{}

		_, err := queries.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
			UserID:  userID,
			Balance: 250,
		})
		require.NoError(t, err)

		resp, err := svc.GetGameBalance(ctx, &pb.GetGameBalanceRequest{UserId: userID.String()})
		require.NoError(t, err)
		require.Equal(t, int32(250), resp.Balance)
	})

	t.Run("invalid_user_id", func(t *testing.T) {
		svc := &grpcServer.GameServer{}

		resp, err := svc.GetGameBalance(context.Background(), &pb.GetGameBalanceRequest{UserId: "not-a-uuid"})
		require.Error(t, err)
		require.Nil(t, resp)
	})
}

func TestIntegration_UpdateGameBalance(t *testing.T) {
	t.Run("set_balance", func(t *testing.T) {
		ctx, queries := newTestCtx(t)
		userID := createTestUser(t, queries)
		svc := &grpcServer.GameServer{}

		resp, err := svc.UpdateGameBalance(ctx, &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: 300})
		require.NoError(t, err)
		require.Equal(t, userID.String(), resp.UserId)
		require.Equal(t, int32(300), resp.Balance)

		row, err := queries.GetUserGameBalance(ctx, userID)
		require.NoError(t, err)
		require.Equal(t, int32(300), row.Balance)
	})

	t.Run("overwrite", func(t *testing.T) {
		ctx, queries := newTestCtx(t)
		userID := createTestUser(t, queries)
		svc := &grpcServer.GameServer{}

		_, err := queries.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
			UserID:  userID,
			Balance: 100,
		})
		require.NoError(t, err)

		resp, err := svc.UpdateGameBalance(ctx, &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: 75})
		require.NoError(t, err)
		require.Equal(t, int32(75), resp.Balance)

		row, err := queries.GetUserGameBalance(ctx, userID)
		require.NoError(t, err)
		require.Equal(t, int32(75), row.Balance)
	})

	t.Run("negative_rejected", func(t *testing.T) {
		ctx, queries := newTestCtx(t)
		userID := createTestUser(t, queries)
		svc := &grpcServer.GameServer{}

		resp, err := svc.UpdateGameBalance(ctx, &pb.UpdateGameBalanceRequest{UserId: userID.String(), Balance: -10})
		require.Error(t, err)
		require.Nil(t, resp)
	})
}

func TestIntegration_RecordBets_AndGetBetHistory(t *testing.T) {
	ctx, queries := newTestCtx(t)
	userID := createTestUser(t, queries)
	svc := &grpcServer.GameServer{}

	_, err := queries.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
		UserID:  userID,
		Balance: 100,
	})
	require.NoError(t, err)

	recordResp, err := svc.RecordBets(ctx, &pb.RecordBetsRequest{
		UserId: userID.String(),
		Bets: []*pb.BetEntry{
			{Zone: "red", Amount: 10, RollResult: 7, Payout: 20},
			{Zone: "black", Amount: 5, RollResult: 14, Payout: 0},
		},
	})
	require.NoError(t, err)
	require.True(t, recordResp.Success)

	historyResp, err := svc.GetBetHistory(ctx, &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 10, Offset: 0})
	require.NoError(t, err)
	require.Len(t, historyResp.Bets, 2)
	// Both bets were inserted in the same transaction so created_at is identical;
	// only assert that both records exist with the right fields.
	zones := map[string]int32{
		historyResp.Bets[0].Zone: historyResp.Bets[0].Amount,
		historyResp.Bets[1].Zone: historyResp.Bets[1].Amount,
	}
	require.Equal(t, int32(10), zones["red"])
	require.Equal(t, int32(5), zones["black"])
}

func TestIntegration_GetBetHistory(t *testing.T) {
	t.Run("pagination", func(t *testing.T) {
		ctx, queries := newTestCtx(t)
		userID := createTestUser(t, queries)
		svc := &grpcServer.GameServer{}

		_, err := queries.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
			UserID:  userID,
			Balance: 1000,
		})
		require.NoError(t, err)

		for i := 0; i < 5; i++ {
			_, err := queries.InsertUserGameBet(ctx, db.InsertUserGameBetParams{
				UserID:     userID,
				Zone:       "red",
				Amount:     int32(10 + i),
				RollResult: 7,
				Payout:     int32(20 + i),
			})
			require.NoError(t, err)
		}

		resp1, err := svc.GetBetHistory(ctx, &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 2, Offset: 0})
		require.NoError(t, err)
		require.Len(t, resp1.Bets, 2)

		resp2, err := svc.GetBetHistory(ctx, &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 2, Offset: 2})
		require.NoError(t, err)
		require.Len(t, resp2.Bets, 2)

		respAll, err := svc.GetBetHistory(ctx, &pb.GetBetHistoryRequest{UserId: userID.String(), Limit: 10, Offset: 0})
		require.NoError(t, err)
		require.Len(t, respAll.Bets, 5)
	})
}

// Ensure GetGameBalance and GetBetHistory reject invalid UUIDs without touching the DB.
func TestIntegration_InvalidUserID(t *testing.T) {
	svc := &grpcServer.GameServer{}

	t.Run("GetGameBalance", func(t *testing.T) {
		_, err := svc.GetGameBalance(context.Background(), &pb.GetGameBalanceRequest{UserId: "not-a-uuid"})
		require.Error(t, err)
	})

	t.Run("GetBetHistory", func(t *testing.T) {
		_, err := svc.GetBetHistory(context.Background(), &pb.GetBetHistoryRequest{UserId: "not-a-uuid"})
		require.Error(t, err)
	})
}
