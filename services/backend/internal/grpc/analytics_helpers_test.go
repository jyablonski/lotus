package grpc

import (
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNumericToFloat64(t *testing.T) {
	var valid pgtype.Numeric
	require.NoError(t, valid.Scan("7.5"))
	assert.Equal(t, 7.5, numericToFloat64(valid))

	var invalid pgtype.Numeric
	assert.Equal(t, 0.0, numericToFloat64(invalid))
}

func TestDerefString(t *testing.T) {
	s := "hello"
	assert.Equal(t, "hello", derefString(&s))
	assert.Equal(t, "", derefString(nil))
}

func TestPgTimestampToString(t *testing.T) {
	ts := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
	assert.Equal(t, "2024-01-15T10:30:00Z", pgTimestampToString(pgtype.Timestamp{Time: ts, Valid: true}))
	assert.Equal(t, "", pgTimestampToString(pgtype.Timestamp{}))
}
