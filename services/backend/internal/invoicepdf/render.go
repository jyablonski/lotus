// Package invoicepdf renders invoice PDFs matching the admin invoice form layout.
package invoicepdf

import (
	"bytes"
	"errors"
	"fmt"
	"math"
	"strconv"
	"strings"
	"time"

	"github.com/go-pdf/fpdf"
	pb "github.com/jyablonski/lotus/internal/pb/proto/invoice"
)

// Render builds a single-page letter-size PDF from the invoice payload.
func Render(payload *pb.InvoicePayload) ([]byte, error) {
	if payload == nil || payload.Invoice == nil {
		return nil, errors.New("invoice payload is required")
	}
	if payload.Sender == nil || payload.Client == nil || payload.Payment == nil {
		return nil, errors.New("sender, client, and payment sections are required")
	}

	pdf := fpdf.New("P", "pt", "Letter", "")
	pdf.SetMargins(50, 50, 50)
	// Default bottom break margin is ~56.7pt; SetMargins does not update it. Without this,
	// pageBreakTrigger stays ~735 while we draw the footer at y=742, so fpdf inserts a
	// new page before "Thank you" and the line lands at the top of page 2.
	pdf.SetAutoPageBreak(true, 50)
	pdf.AddPage()

	width, height := pdf.GetPageSize()
	rightX := width - 50
	const lightGray = 204
	contentW := width - 100

	// Line items table: Description | Hours | Rate | Amount (amounts right-aligned).
	const (
		colDesc   = 60.0
		colDescW  = 250.0
		colHours  = 315.0
		colHoursW = 40.0
		colRate   = 360.0
		colRateW  = 100.0
		colAmt    = 465.0
		colAmtW   = 97.0
	)

	dark := func() { pdf.SetTextColor(51, 51, 51) }
	medium := func() { pdf.SetTextColor(102, 102, 102) }
	lightText := func() { pdf.SetTextColor(lightGray, lightGray, lightGray) }

	// Header
	pdf.SetFont("Helvetica", "B", 28)
	dark()
	pdf.SetXY(50, 50)
	pdf.Cell(0, 0, "INVOICE")

	pdf.SetFont("Helvetica", "", 10)
	medium()
	inv := payload.Invoice
	hdrY := 40.0
	for _, line := range []string{
		fmt.Sprintf("Invoice #: %s", inv.Number),
		fmt.Sprintf("Date: %s", formatUSDate(inv.Date)),
		fmt.Sprintf("Due Date: %s", formatUSDate(inv.DueDate)),
		fmt.Sprintf("Terms: %s", inv.Terms),
	} {
		pdf.SetXY(50, hdrY)
		pdf.CellFormat(contentW, 12, line, "", 0, "R", false, 0, "")
		hdrY += 15
	}

	pdf.SetDrawColor(lightGray, lightGray, lightGray)
	pdf.SetLineWidth(1)
	pdf.Line(50, 105, width-50, 105)

	// FROM / TO
	pdf.SetFont("Helvetica", "B", 9)
	medium()
	pdf.SetXY(50, 120)
	pdf.Cell(0, 0, "FROM")

	s := payload.Sender
	pdf.SetFont("Helvetica", "", 10)
	dark()
	y := 135.0
	for _, line := range []string{s.Name, s.AddressLine1, s.AddressLine2, s.Email} {
		pdf.SetXY(50, y)
		pdf.Cell(0, 0, line)
		y += 13
	}

	pdf.SetFont("Helvetica", "B", 9)
	medium()
	pdf.SetXY(300, 120)
	pdf.Cell(0, 0, "TO")

	c := payload.Client
	pdf.SetFont("Helvetica", "", 10)
	dark()
	y = 135
	for _, line := range []string{c.Name, c.AddressLine1, c.AddressLine2} {
		pdf.SetXY(300, y)
		pdf.Cell(0, 0, line)
		y += 13
	}
	if strings.TrimSpace(c.Attention) != "" {
		pdf.SetXY(300, y)
		pdf.Cell(0, 0, fmt.Sprintf("Attn: %s", c.Attention))
		y += 13
	}

	tableTop := 240.0
	pdf.SetFillColor(245, 245, 245)
	pdf.Rect(50, tableTop-5, width-100, 25, "F")

	pdf.SetFont("Helvetica", "B", 10)
	dark()
	pdf.SetXY(colDesc, tableTop+5)
	pdf.Cell(0, 0, "Description")
	pdf.SetXY(colHours, tableTop+5)
	pdf.CellFormat(colHoursW, 0, "Hours", "", 0, "R", false, 0, "")
	pdf.SetXY(colRate, tableTop+5)
	pdf.CellFormat(colRateW, 0, "Rate", "", 0, "R", false, 0, "")
	pdf.SetXY(colAmt, tableTop+5)
	pdf.CellFormat(colAmtW, 0, "Amount", "", 0, "R", false, 0, "")

	pdf.SetFont("Helvetica", "", 10)
	descY := tableTop + 35.0
	var total float64
	const lineH = 15.0
	for _, item := range payload.LineItems {
		lines := splitLines(item.Description)
		if len(lines) == 0 {
			lines = []string{""}
		}
		for i, ln := range lines {
			pdf.SetXY(colDesc, descY+float64(i)*lineH)
			pdf.CellFormat(colDescW, 0, ln, "", 0, "L", false, 0, "")
		}
		amt := item.Amount
		total += amt
		// Vertically center hours / rate / amount with the description block.
		midY := descY + float64(len(lines)-1)*lineH/2
		pdf.SetXY(colHours, midY)
		pdf.CellFormat(colHoursW, 0, formatHours(item.Hours), "", 0, "R", false, 0, "")
		pdf.SetXY(colRate, midY)
		pdf.CellFormat(colRateW, 0, formatRate(item.Rate), "", 0, "R", false, 0, "")
		pdf.SetXY(colAmt, midY)
		pdf.CellFormat(colAmtW, 0, formatMoney(amt), "", 0, "R", false, 0, "")
		descY += float64(len(lines))*lineH + 12
	}

	totalY := descY + 8
	pdf.SetDrawColor(lightGray, lightGray, lightGray)
	pdf.Line(colHours, totalY, rightX, totalY)

	pdf.SetFont("Helvetica", "B", 12)
	dark()
	pdf.SetXY(colHours, totalY+12)
	pdf.Cell(0, 0, "Total Due:")
	pdf.SetXY(colAmt, totalY+12)
	pdf.CellFormat(colAmtW, 0, formatMoney(total), "", 0, "R", false, 0, "")

	payY := totalY + 48
	pdf.SetFont("Helvetica", "B", 10)
	pdf.SetXY(50, payY)
	pdf.Cell(0, 0, "Payment Information")
	pdf.Line(50, payY+10, width-50, payY+10)

	p := payload.Payment
	pdf.SetFont("Helvetica", "", 10)
	dark()
	pdf.SetXY(50, payY+20)
	pdf.Cell(0, 0, "Please make payment via one of the following methods:")

	pdf.SetFont("Helvetica", "B", 10)
	pdf.SetXY(50, payY+42)
	pdf.Cell(0, 0, "ACH Transfer:")
	pdf.SetFont("Helvetica", "", 10)
	pdf.SetXY(70, payY+55)
	pdf.Cell(0, 0, fmt.Sprintf("Account Number: %s", p.AchAccountNumber))
	pdf.SetXY(70, payY+68)
	pdf.Cell(0, 0, fmt.Sprintf("Routing Number: %s", p.AchRoutingNumber))

	pdf.SetFont("Helvetica", "B", 10)
	pdf.SetXY(50, payY+88)
	pdf.Cell(0, 0, "Check:")
	pdf.SetFont("Helvetica", "", 10)
	pdf.SetXY(70, payY+101)
	pdf.Cell(0, 0, fmt.Sprintf("Payable to %s", p.CheckPayableTo))

	pdf.SetFont("Helvetica", "", 9)
	lightText()
	pdf.SetXY(0, height-50)
	pdf.CellFormat(width, 0, "Thank you for your business", "", 0, "C", false, 0, "")

	var buf bytes.Buffer
	if err := pdf.Output(&buf); err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

func formatUSDate(iso string) string {
	t, err := time.Parse("2006-01-02", strings.TrimSpace(iso))
	if err != nil {
		return iso
	}
	return t.Format("January 2, 2006")
}

func formatMoney(x float64) string {
	neg := x < 0
	if neg {
		x = -x
	}
	cents := int64(math.Round(x*100 + 1e-9))
	whole := cents / 100
	frac := cents % 100
	s := addThousands(strconv.FormatInt(whole, 10))
	sign := ""
	if neg {
		sign = "-"
	}
	return fmt.Sprintf("%s$%s.%02d", sign, s, frac)
}

func formatHours(h float64) string {
	if math.Abs(h-math.Round(h)) < 1e-6 {
		return fmt.Sprintf("%.0f", h)
	}
	s := fmt.Sprintf("%.1f", h)
	s = strings.TrimRight(s, "0")
	return strings.TrimRight(s, ".")
}

func formatRate(rate float64) string {
	return fmt.Sprintf("%s/hr", formatMoney(rate))
}

func addThousands(intDigits string) string {
	n := len(intDigits)
	if n <= 3 {
		return intDigits
	}
	prefix := n % 3
	if prefix == 0 {
		prefix = 3
	}
	var b strings.Builder
	b.WriteString(intDigits[:prefix])
	for i := prefix; i < n; i += 3 {
		b.WriteByte(',')
		b.WriteString(intDigits[i : i+3])
	}
	return b.String()
}

func splitLines(s string) []string {
	raw := strings.Split(s, "\n")
	var out []string
	for _, line := range raw {
		if strings.TrimSpace(line) != "" {
			out = append(out, line)
		}
	}
	return out
}
