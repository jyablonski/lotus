package grpc

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/inject"
	"github.com/jyablonski/lotus/internal/invoicepdf"
	pb "github.com/jyablonski/lotus/internal/pb/proto/invoice"
	"github.com/lib/pq"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// InvoiceServer implements admin-only invoice APIs (persist + PDF).
type InvoiceServer struct {
	pb.UnimplementedInvoiceServiceServer
}

func (s *InvoiceServer) CreateInvoice(ctx context.Context, req *pb.CreateInvoiceRequest) (*pb.CreateInvoiceResponse, error) {
	if err := validateInvoicePayload(req.GetInvoice(), true); err != nil {
		return nil, status.Error(codes.InvalidArgument, err.Error())
	}

	userID, err := uuid.Parse(strings.TrimSpace(req.GetUserId()))
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid user_id")
	}

	dbq := inject.DBFrom(ctx)
	if err := requireAdmin(ctx, dbq, userID); err != nil {
		return nil, err
	}

	sqlDB := inject.SQLDBFrom(ctx)
	tx, err := sqlDB.BeginTx(ctx, nil)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "begin transaction: %v", err)
	}
	defer func() { _ = tx.Rollback() }()

	q := db.New(tx)

	senderID, err := getOrInsertSender(ctx, q, req.GetInvoice().GetSender())
	if err != nil {
		return nil, err
	}
	clientID, err := getOrInsertClient(ctx, q, req.GetInvoice().GetClient())
	if err != nil {
		return nil, err
	}
	paymentID, err := getOrInsertPayment(ctx, q, req.GetInvoice().GetPayment())
	if err != nil {
		return nil, err
	}

	inv := req.GetInvoice().GetInvoice()
	date, err := time.Parse("2006-01-02", strings.TrimSpace(inv.GetDate()))
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid invoice date (use YYYY-MM-DD)")
	}
	due, err := time.Parse("2006-01-02", strings.TrimSpace(inv.GetDueDate()))
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid due date (use YYYY-MM-DD)")
	}

	invoiceID, err := q.InsertInvoice(ctx, db.InsertInvoiceParams{
		InvoiceNumber: strings.TrimSpace(inv.GetNumber()),
		Date:          date,
		DueDate:       due,
		Terms:         strings.TrimSpace(inv.GetTerms()),
		SenderID:      senderID,
		ClientID:      clientID,
		PaymentInfoID: paymentID,
	})
	if err != nil {
		var pqErr *pq.Error
		if errors.As(err, &pqErr) && pqErr.Code == "23505" {
			return nil, status.Error(codes.AlreadyExists, "invoice number already exists")
		}
		return nil, status.Errorf(codes.Internal, "insert invoice: %v", err)
	}

	for _, line := range req.GetInvoice().GetLineItems() {
		err := q.InsertInvoiceLineItem(ctx, db.InsertInvoiceLineItemParams{
			InvoiceID:   invoiceID,
			Description: strings.TrimSpace(line.GetDescription()),
			Hours:       formatDecimal(line.GetHours()),
			Rate:        formatDecimal(line.GetRate()),
			Amount:      formatDecimal(line.GetAmount()),
		})
		if err != nil {
			return nil, status.Errorf(codes.Internal, "insert line item: %v", err)
		}
	}

	if err := tx.Commit(); err != nil {
		return nil, status.Errorf(codes.Internal, "commit transaction: %v", err)
	}

	return &pb.CreateInvoiceResponse{InvoiceId: invoiceID.String()}, nil
}

func (s *InvoiceServer) RenderInvoicePdf(ctx context.Context, req *pb.RenderInvoicePdfRequest) (*pb.RenderInvoicePdfResponse, error) {
	if err := validateInvoicePayload(req.GetInvoice(), false); err != nil {
		return nil, status.Error(codes.InvalidArgument, err.Error())
	}

	userID, err := uuid.Parse(strings.TrimSpace(req.GetUserId()))
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid user_id")
	}

	dbq := inject.DBFrom(ctx)
	if err := requireAdmin(ctx, dbq, userID); err != nil {
		return nil, err
	}

	pdfBytes, err := invoicepdf.Render(req.GetInvoice())
	if err != nil {
		return nil, status.Errorf(codes.Internal, "render pdf: %v", err)
	}

	num := strings.TrimSpace(req.GetInvoice().GetInvoice().GetNumber())
	filename := "invoice-draft.pdf"
	if num != "" {
		filename = fmt.Sprintf("invoice-%s.pdf", num)
	}

	return &pb.RenderInvoicePdfResponse{
		PdfBytes: pdfBytes,
		Filename: filename,
	}, nil
}

func (s *InvoiceServer) GetInvoiceReferenceData(
	ctx context.Context,
	req *pb.GetInvoiceReferenceDataRequest,
) (*pb.GetInvoiceReferenceDataResponse, error) {
	userID, err := uuid.Parse(strings.TrimSpace(req.GetUserId()))
	if err != nil {
		return nil, status.Error(codes.InvalidArgument, "invalid user_id")
	}

	dbq := inject.DBFrom(ctx)
	if err := requireAdmin(ctx, dbq, userID); err != nil {
		return nil, err
	}

	senders, err := dbq.ListInvoiceSenders(ctx)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "list senders: %v", err)
	}
	clients, err := dbq.ListInvoiceClients(ctx)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "list clients: %v", err)
	}
	payments, err := dbq.ListInvoicePaymentInfo(ctx)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "list payment info: %v", err)
	}

	resp := &pb.GetInvoiceReferenceDataResponse{}
	for _, r := range senders {
		resp.Senders = append(resp.Senders, &pb.InvoiceSenderRecord{
			Id:           r.ID.String(),
			Name:         r.Name,
			AddressLine1: r.AddressLine1,
			AddressLine2: r.AddressLine2,
			Email:        r.Email,
		})
	}
	for _, r := range clients {
		resp.Clients = append(resp.Clients, &pb.InvoiceClientRecord{
			Id:           r.ID.String(),
			Name:         r.Name,
			AddressLine1: r.AddressLine1,
			AddressLine2: r.AddressLine2,
			Attention:    r.Attention,
		})
	}
	for _, r := range payments {
		resp.PaymentProfiles = append(resp.PaymentProfiles, &pb.InvoicePaymentRecord{
			Id:               r.ID.String(),
			CheckPayableTo:   r.CheckPayableTo,
			AchAccountNumber: r.AchAccountNumber,
			AchRoutingNumber: r.AchRoutingNumber,
		})
	}
	return resp, nil
}

func requireAdmin(ctx context.Context, dbq db.Querier, userID uuid.UUID) error {
	u, err := dbq.GetUserById(ctx, userID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return status.Error(codes.NotFound, "user not found")
		}
		return status.Errorf(codes.Internal, "get user: %v", err)
	}
	if !strings.EqualFold(strings.TrimSpace(u.Role), "Admin") {
		return status.Error(codes.PermissionDenied, "admin access required")
	}
	return nil
}

func validateInvoicePayload(payload *pb.InvoicePayload, requireInvoiceNumber bool) error {
	if payload == nil {
		return fmt.Errorf("invoice payload is required")
	}
	if payload.Sender == nil || strings.TrimSpace(payload.Sender.Name) == "" {
		return fmt.Errorf("sender name is required")
	}
	if payload.Client == nil || strings.TrimSpace(payload.Client.Name) == "" {
		return fmt.Errorf("client name is required")
	}
	if payload.Payment == nil {
		return fmt.Errorf("payment section is required")
	}
	if payload.Invoice == nil {
		return fmt.Errorf("invoice details are required")
	}
	if requireInvoiceNumber && strings.TrimSpace(payload.Invoice.Number) == "" {
		return fmt.Errorf("invoice number is required")
	}
	if len(payload.LineItems) == 0 {
		return fmt.Errorf("at least one line item is required")
	}
	terms := strings.TrimSpace(payload.Invoice.Terms)
	switch terms {
	case "Net 15", "Net 30", "Net 45", "Net 60", "Due on Receipt":
	default:
		return fmt.Errorf("invalid terms value")
	}
	return nil
}

func getOrInsertSender(ctx context.Context, q *db.Queries, s *pb.InvoiceSender) (uuid.UUID, error) {
	id, err := q.GetInvoiceSenderByNameEmail(ctx, db.GetInvoiceSenderByNameEmailParams{
		Name:  strings.TrimSpace(s.GetName()),
		Email: strings.TrimSpace(s.GetEmail()),
	})
	if err == nil {
		return id, nil
	}
	if !errors.Is(err, sql.ErrNoRows) {
		return uuid.Nil, status.Errorf(codes.Internal, "lookup sender: %v", err)
	}
	return q.InsertInvoiceSender(ctx, db.InsertInvoiceSenderParams{
		Name:         strings.TrimSpace(s.GetName()),
		AddressLine1: strings.TrimSpace(s.GetAddressLine1()),
		AddressLine2: strings.TrimSpace(s.GetAddressLine2()),
		Email:        strings.TrimSpace(s.GetEmail()),
	})
}

func getOrInsertClient(ctx context.Context, q *db.Queries, c *pb.InvoiceClient) (uuid.UUID, error) {
	id, err := q.GetInvoiceClientByName(ctx, strings.TrimSpace(c.GetName()))
	if err == nil {
		return id, nil
	}
	if !errors.Is(err, sql.ErrNoRows) {
		return uuid.Nil, status.Errorf(codes.Internal, "lookup client: %v", err)
	}
	return q.InsertInvoiceClient(ctx, db.InsertInvoiceClientParams{
		Name:         strings.TrimSpace(c.GetName()),
		AddressLine1: strings.TrimSpace(c.GetAddressLine1()),
		AddressLine2: strings.TrimSpace(c.GetAddressLine2()),
		Attention:    strings.TrimSpace(c.GetAttention()),
	})
}

func getOrInsertPayment(ctx context.Context, q *db.Queries, p *pb.InvoicePayment) (uuid.UUID, error) {
	id, err := q.GetInvoicePaymentByCheckPayable(ctx, strings.TrimSpace(p.GetCheckPayableTo()))
	if err == nil {
		return id, nil
	}
	if !errors.Is(err, sql.ErrNoRows) {
		return uuid.Nil, status.Errorf(codes.Internal, "lookup payment info: %v", err)
	}
	return q.InsertInvoicePayment(ctx, db.InsertInvoicePaymentParams{
		CheckPayableTo:   strings.TrimSpace(p.GetCheckPayableTo()),
		AchAccountNumber: strings.TrimSpace(p.GetAchAccountNumber()),
		AchRoutingNumber: strings.TrimSpace(p.GetAchRoutingNumber()),
	})
}

func formatDecimal(x float64) string {
	return strconv.FormatFloat(x, 'f', 2, 64)
}
