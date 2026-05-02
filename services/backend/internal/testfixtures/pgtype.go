package testfixtures

import (
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
)

func UUIDFromGoogle(t *testing.T, id uuid.UUID) pgtype.UUID {
	t.Helper()

	var pgID pgtype.UUID
	if err := pgID.Scan(id.String()); err != nil {
		t.Fatalf("testfixtures: scan uuid: %v", err)
	}
	return pgID
}

func Date(year int, month time.Month, day int) pgtype.Date {
	return pgtype.Date{
		Time:  time.Date(year, month, day, 0, 0, 0, 0, time.UTC),
		Valid: true,
	}
}

func Numeric(t *testing.T, value string) pgtype.Numeric {
	t.Helper()

	var numeric pgtype.Numeric
	if err := numeric.Scan(value); err != nil {
		t.Fatalf("testfixtures: scan numeric %q: %v", value, err)
	}
	return numeric
}

func StringPtr(value string) *string {
	return &value
}

func Int32Ptr(value int32) *int32 {
	return &value
}
