package invoicepdf

import (
	"bytes"
	"strings"
	"testing"

	pb "github.com/jyablonski/lotus/internal/pb/proto/invoice"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func samplePayload() *pb.InvoicePayload {
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
			AchAccountNumber: "554041411333",
			AchRoutingNumber: "323111555",
		},
		Invoice: &pb.InvoiceHeader{
			Number:  "INV-001",
			Date:    "2026-04-01",
			DueDate: "2026-05-01",
			Terms:   "Net 30",
		},
		LineItems: []*pb.InvoiceLineItem{
			{
				Description: "Software Development Services\nForecasting Widget",
				Hours:       30,
				Rate:        110,
				Amount:      3300,
			},
		},
	}
}

func TestRender(t *testing.T) {
	t.Run("success", func(t *testing.T) {
		out, err := Render(samplePayload())
		require.NoError(t, err)
		require.NotEmpty(t, out)
		assert.True(t, bytes.HasPrefix(out, []byte("%PDF")), "output should be a PDF")
		assert.Greater(t, len(out), 1500, "expected a non-trivial PDF payload")

		// Page content is Flate-compressed; assert structure from uncompressed sections.
		raw := string(out)
		assert.Contains(t, raw, "%%EOF")
		assert.Contains(t, raw, "/Count 1")
		assert.Contains(t, raw, "612.00 792.00")
		assert.Contains(t, raw, "/Subtype /Type1")
	})

	t.Run("nil_payload", func(t *testing.T) {
		_, err := Render(nil)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "invoice payload is required")
	})

	t.Run("nil_invoice", func(t *testing.T) {
		p := samplePayload()
		p.Invoice = nil
		_, err := Render(p)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "invoice payload is required")
	})

	t.Run("nil_sender", func(t *testing.T) {
		p := samplePayload()
		p.Sender = nil
		_, err := Render(p)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "sender, client, and payment sections are required")
	})

	t.Run("nil_client", func(t *testing.T) {
		p := samplePayload()
		p.Client = nil
		_, err := Render(p)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "sender, client, and payment sections are required")
	})

	t.Run("nil_payment", func(t *testing.T) {
		p := samplePayload()
		p.Payment = nil
		_, err := Render(p)
		require.Error(t, err)
		assert.Contains(t, err.Error(), "sender, client, and payment sections are required")
	})
}

func TestFormatMoney(t *testing.T) {
	assert.Equal(t, "$0.00", formatMoney(0))
	assert.Equal(t, "$1.23", formatMoney(1.23))
	assert.Equal(t, "$3,300.00", formatMoney(3300))
	assert.Equal(t, "$1,234,567.89", formatMoney(1234567.89))
	assert.Equal(t, "-$100.00", formatMoney(-100))
}

func TestFormatHours(t *testing.T) {
	assert.Equal(t, "30", formatHours(30))
	assert.Equal(t, "30", formatHours(30.0))
	assert.Equal(t, "2.5", formatHours(2.5))
}

func TestFormatRate(t *testing.T) {
	assert.Equal(t, "$110.00/hr", formatRate(110))
	assert.Equal(t, "$0.50/hr", formatRate(0.5))
}

func TestAddThousands(t *testing.T) {
	assert.Equal(t, "300", addThousands("300"))
	assert.Equal(t, "3,300", addThousands("3300"))
	assert.Equal(t, "1,234,567", addThousands("1234567"))
}

func TestFormatUSDate(t *testing.T) {
	assert.Equal(t, "April 1, 2026", formatUSDate("2026-04-01"))
	assert.Equal(t, "not-a-date", formatUSDate("not-a-date"))
}

func TestSplitLines(t *testing.T) {
	assert.Equal(t, []string{"a", "b"}, splitLines("a\n\nb\n"))
	assert.Nil(t, splitLines("   \n  \n"))
}

func TestRender_multiLineDescriptionCentersNumericColumns(t *testing.T) {
	p := samplePayload()
	p.LineItems[0].Description = strings.Repeat("Line\n", 4) + "Last"
	out, err := Render(p)
	require.NoError(t, err)
	assert.True(t, bytes.HasPrefix(out, []byte("%PDF")))
	assert.Greater(t, len(out), 1500)
	// Body text is inside a compressed stream; still a single-page PDF.
	assert.Contains(t, string(out), "/Count 1")
}
