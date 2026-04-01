package grpc_test

import (
	"context"
	"testing"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	internalgrpc "github.com/jyablonski/lotus/internal/grpc"
	"github.com/jyablonski/lotus/internal/mocks"
	pb "github.com/jyablonski/lotus/internal/pb/proto/invoice"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func sampleInvoicePayload() *pb.InvoicePayload {
	return &pb.InvoicePayload{
		Sender: &pb.InvoiceSender{
			Name:         "Sender Co",
			AddressLine1: "1 Main St",
			AddressLine2: "City, ST 12345",
			Email:        "s@example.com",
		},
		Client: &pb.InvoiceClient{
			Name:         "Client LLC",
			AddressLine1: "2 Oak Ave",
			AddressLine2: "Town, ST 99999",
			Attention:    "Jane",
		},
		Payment: &pb.InvoicePayment{
			CheckPayableTo:   "Sender Co",
			AchAccountNumber: "123456789",
			AchRoutingNumber: "987654321",
		},
		Invoice: &pb.InvoiceHeader{
			Number:  "INV-001",
			Date:    "2026-04-01",
			DueDate: "2026-05-01",
			Terms:   "Net 30",
		},
		LineItems: []*pb.InvoiceLineItem{
			{
				Description: "Work performed",
				Hours:       10,
				Rate:        100,
				Amount:      1000,
			},
		},
	}
}

func TestInvoiceServer_RenderInvoicePdf(t *testing.T) {
	t.Run("non_admin", func(t *testing.T) {
		uid := uuid.New()
		mock := &mocks.QuerierMock{
			GetUserByIdFunc: func(ctx context.Context, id uuid.UUID) (db.SourceUser, error) {
				return db.SourceUser{ID: id, Role: "Consumer"}, nil
			},
		}
		ctx := testCtx(mock)

		s := &internalgrpc.InvoiceServer{}
		_, err := s.RenderInvoicePdf(ctx, &pb.RenderInvoicePdfRequest{
			UserId:  uid.String(),
			Invoice: sampleInvoicePayload(),
		})
		require.Error(t, err)
		assert.Equal(t, codes.PermissionDenied, status.Code(err))
	})

	t.Run("success", func(t *testing.T) {
		uid := uuid.New()
		mock := &mocks.QuerierMock{
			GetUserByIdFunc: func(ctx context.Context, id uuid.UUID) (db.SourceUser, error) {
				return db.SourceUser{ID: id, Role: "Admin"}, nil
			},
		}
		ctx := testCtx(mock)

		s := &internalgrpc.InvoiceServer{}
		resp, err := s.RenderInvoicePdf(ctx, &pb.RenderInvoicePdfRequest{
			UserId:  uid.String(),
			Invoice: sampleInvoicePayload(),
		})
		require.NoError(t, err)
		require.NotNil(t, resp)
		assert.Greater(t, len(resp.PdfBytes), 100)
		assert.Contains(t, resp.Filename, "invoice-")
	})

	t.Run("invalid_terms", func(t *testing.T) {
		p := sampleInvoicePayload()
		p.Invoice.Terms = "invalid"
		s := &internalgrpc.InvoiceServer{}
		_, err := s.RenderInvoicePdf(context.Background(), &pb.RenderInvoicePdfRequest{
			UserId:  uuid.New().String(),
			Invoice: p,
		})
		require.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})
}

func TestInvoiceServer_CreateInvoice(t *testing.T) {
	t.Run("invalid_user_id", func(t *testing.T) {
		s := &internalgrpc.InvoiceServer{}
		_, err := s.CreateInvoice(context.Background(), &pb.CreateInvoiceRequest{
			UserId:  "not-a-uuid",
			Invoice: sampleInvoicePayload(),
		})
		require.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})
}

func TestInvoiceServer_GetInvoiceReferenceData(t *testing.T) {
	t.Run("invalid_user_id", func(t *testing.T) {
		s := &internalgrpc.InvoiceServer{}
		_, err := s.GetInvoiceReferenceData(context.Background(), &pb.GetInvoiceReferenceDataRequest{
			UserId: "bad",
		})
		require.Error(t, err)
		assert.Equal(t, codes.InvalidArgument, status.Code(err))
	})
}
