package grpc_test

import (
	"context"
	"database/sql"
	"testing"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/inject"
	pb "github.com/jyablonski/lotus/internal/pb/proto/invoice"
	"github.com/jyablonski/lotus/internal/testinfra"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func newInvoiceIntegrationCtx(t *testing.T) (context.Context, *sql.DB) {
	t.Helper()
	dbConn, err := sql.Open("postgres", testDBConnStr)
	require.NoError(t, err)
	t.Cleanup(func() { _ = dbConn.Close() })

	queries := db.New(dbConn)
	logger := testinfra.DiscardLogger()
	ctx := inject.WithDB(context.Background(), queries)
	ctx = inject.WithSQLDB(ctx, dbConn)
	ctx = inject.WithLogger(ctx, logger)
	ctx = inject.WithRedisClient(ctx, testRedisClient)
	return ctx, dbConn
}

func TestIntegration_InvoiceServer_CreateInvoice(t *testing.T) {
	t.Run("success", func(t *testing.T) {
		ctx, dbConn := newInvoiceIntegrationCtx(t)

		userID := createTestUser(t, db.New(dbConn))
		_, err := dbConn.ExecContext(context.Background(),
			`UPDATE source.users SET role = $1 WHERE id = $2`,
			"Admin", userID)
		require.NoError(t, err)

		num := "test-inv-" + uuid.New().String()[:8]
		payload := sampleInvoicePayload()
		payload.Invoice.Number = num

		svc := &internalgrpc.InvoiceServer{}
		resp, err := svc.CreateInvoice(ctx, &pb.CreateInvoiceRequest{
			UserId:  userID.String(),
			Invoice: payload,
		})
		require.NoError(t, err)
		require.NotNil(t, resp)
		invID, err := uuid.Parse(resp.InvoiceId)
		require.NoError(t, err)
		assert.NotEqual(t, uuid.Nil, invID)

		var count int
		err = dbConn.QueryRowContext(context.Background(),
			`SELECT COUNT(*) FROM source.invoice_line_items WHERE invoice_id = $1`,
			invID).Scan(&count)
		require.NoError(t, err)
		assert.Equal(t, 1, count)

		// CreateInvoice commits its own transaction internally, so we cannot wrap this
		// call in a test transaction and rollback. Tear down persisted rows instead.
		t.Cleanup(func() {
			_, _ = dbConn.ExecContext(context.Background(),
				`DELETE FROM source.invoices WHERE id = $1`, invID)
		})
	})
}
