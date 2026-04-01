-- name: GetInvoiceSenderByNameEmail :one
SELECT id FROM source.invoice_senders
WHERE name = $1 AND email = $2
LIMIT 1;

-- name: InsertInvoiceSender :one
INSERT INTO source.invoice_senders (name, address_line1, address_line2, email)
VALUES ($1, $2, $3, $4)
RETURNING id;

-- name: GetInvoiceClientByName :one
SELECT id FROM source.invoice_clients
WHERE name = $1
LIMIT 1;

-- name: InsertInvoiceClient :one
INSERT INTO source.invoice_clients (name, address_line1, address_line2, attention)
VALUES ($1, $2, $3, $4)
RETURNING id;

-- name: GetInvoicePaymentByCheckPayable :one
SELECT id FROM source.invoice_payment_info
WHERE check_payable_to = $1
LIMIT 1;

-- name: InsertInvoicePayment :one
INSERT INTO source.invoice_payment_info (check_payable_to, ach_account_number, ach_routing_number)
VALUES ($1, $2, $3)
RETURNING id;

-- name: InsertInvoice :one
INSERT INTO source.invoices (
    invoice_number,
    date,
    due_date,
    terms,
    sender_id,
    client_id,
    payment_info_id
) VALUES ($1, $2, $3, $4, $5, $6, $7)
RETURNING id;

-- name: InsertInvoiceLineItem :exec
INSERT INTO source.invoice_line_items (invoice_id, description, hours, rate, amount)
VALUES ($1, $2, $3, $4, $5);

-- name: ListInvoiceSenders :many
SELECT * FROM source.invoice_senders
ORDER BY name ASC, id ASC;

-- name: ListInvoiceClients :many
SELECT * FROM source.invoice_clients
ORDER BY name ASC, id ASC;

-- name: ListInvoicePaymentInfo :many
SELECT * FROM source.invoice_payment_info
ORDER BY check_payable_to ASC, id ASC;
