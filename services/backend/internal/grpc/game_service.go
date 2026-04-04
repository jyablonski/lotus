package grpc

import (
	"context"
	"errors"
	"fmt"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/game"
)

var (
	ErrGameBalanceNotFound = errors.New("game balance not found")
	ErrInvalidBalance      = errors.New("invalid balance: must be >= 0")
)

type GameServer struct {
	pb.UnimplementedGameServiceServer
}

// GetGameBalance returns the current game balance for a user.
// If no row exists yet (first visit), it returns the default balance of 100.
func (s *GameServer) GetGameBalance(ctx context.Context, req *pb.GetGameBalanceRequest) (*pb.GetGameBalanceResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	dbq := inject.DBFrom(ctx)

	pgUserID := pgtype.UUID{Bytes: userID, Valid: true}

	row, err := dbq.GetUserGameBalance(ctx, pgUserID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			// First visit — seed the default balance via upsert so it persists.
			const defaultBalance = 100
			row, err = dbq.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
				UserID:  pgUserID,
				Balance: defaultBalance,
			})
			if err != nil {
				return nil, fmt.Errorf("failed to seed game balance: %w", err)
			}
		} else {
			return nil, fmt.Errorf("failed to get game balance: %w", err)
		}
	}

	return &pb.GetGameBalanceResponse{
		UserId:  uuid.UUID(row.UserID.Bytes).String(),
		Balance: row.Balance,
	}, nil
}

// RecordBets inserts one row into user_game_bets for each BetEntry in the request.
// All inserts happen in a single transaction so they either all succeed or all fail.
func (s *GameServer) RecordBets(ctx context.Context, req *pb.RecordBetsRequest) (*pb.RecordBetsResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	pgxPool := inject.PgxPoolFrom(ctx)

	tx, err := pgxPool.Begin(ctx)
	if err != nil {
		return nil, fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback(ctx) //nolint:errcheck // rollback is a no-op after commit

	txq := db.New(tx)
	pgUserID := pgtype.UUID{Bytes: userID, Valid: true}
	for _, entry := range req.Bets {
		_, err := txq.InsertUserGameBet(ctx, db.InsertUserGameBetParams{
			UserID:     pgUserID,
			Zone:       entry.Zone,
			Amount:     entry.Amount,
			RollResult: entry.RollResult,
			Payout:     entry.Payout,
		})
		if err != nil {
			return nil, fmt.Errorf("failed to record bet: %w", err)
		}
	}

	if err := tx.Commit(ctx); err != nil {
		return nil, fmt.Errorf("commit transaction: %w", err)
	}

	return &pb.RecordBetsResponse{Success: true}, nil
}

// GetBetHistory returns paginated bet history for a user.
func (s *GameServer) GetBetHistory(ctx context.Context, req *pb.GetBetHistoryRequest) (*pb.GetBetHistoryResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	limit := clampLimit(req.Limit, 20)

	dbq := inject.DBFrom(ctx)

	rows, err := dbq.GetUserGameBets(ctx, db.GetUserGameBetsParams{
		UserID: pgtype.UUID{Bytes: userID, Valid: true},
		Limit:  limit,
		Offset: req.Offset,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get bet history: %w", err)
	}

	bets := make([]*pb.BetRecord, 0, len(rows))
	for _, row := range rows {
		createdAt := ""
		if row.CreatedAt.Valid {
			createdAt = row.CreatedAt.Time.Format("2006-01-02T15:04:05Z")
		}
		bets = append(bets, &pb.BetRecord{
			Id:         int32(row.ID),
			Zone:       row.Zone,
			Amount:     row.Amount,
			RollResult: row.RollResult,
			Payout:     row.Payout,
			CreatedAt:  createdAt,
		})
	}

	return &pb.GetBetHistoryResponse{Bets: bets}, nil
}

// UpdateGameBalance sets the game balance for a user to the given value.
func (s *GameServer) UpdateGameBalance(ctx context.Context, req *pb.UpdateGameBalanceRequest) (*pb.UpdateGameBalanceResponse, error) {
	userID, err := uuid.Parse(req.UserId)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrInvalidUserID, err)
	}

	if req.Balance < 0 {
		return nil, ErrInvalidBalance
	}

	dbq := inject.DBFrom(ctx)

	row, err := dbq.UpsertUserGameBalance(ctx, db.UpsertUserGameBalanceParams{
		UserID:  pgtype.UUID{Bytes: userID, Valid: true},
		Balance: req.Balance,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to update game balance: %w", err)
	}

	return &pb.UpdateGameBalanceResponse{
		UserId:  row.UserID.String(),
		Balance: row.Balance,
	}, nil
}
