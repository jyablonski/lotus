package grpc

import (
	"database/sql"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestParseNumericToFloat64(t *testing.T) {
	cases := []struct {
		name     string
		input    string
		expected float64
	}{
		{"valid integer", "42", 42.0},
		{"valid float", "3.14159", 3.14159},
		{"negative number", "-5.5", -5.5},
		{"zero", "0", 0.0},
		{"invalid string", "not-a-number", 0.0},
		{"empty string", "", 0.0},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			assert.Equal(t, tc.expected, parseNumericToFloat64(tc.input))
		})
	}
}

func TestNullStringToString(t *testing.T) {
	cases := []struct {
		name     string
		input    sql.NullString
		expected string
	}{
		{"valid string", sql.NullString{String: "hello", Valid: true}, "hello"},
		{"empty valid string", sql.NullString{String: "", Valid: true}, ""},
		{"null string", sql.NullString{String: "", Valid: false}, ""},
		{"null string with value", sql.NullString{String: "ignored", Valid: false}, ""},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			assert.Equal(t, tc.expected, nullStringToString(tc.input))
		})
	}
}

func TestNullTimeToString(t *testing.T) {
	testTime := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)

	cases := []struct {
		name     string
		input    sql.NullTime
		expected string
	}{
		{"valid time", sql.NullTime{Time: testTime, Valid: true}, "2024-01-15T10:30:00Z"},
		{"null time", sql.NullTime{Time: time.Time{}, Valid: false}, ""},
		{"null time with value", sql.NullTime{Time: testTime, Valid: false}, ""},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			assert.Equal(t, tc.expected, nullTimeToString(tc.input))
		})
	}
}
