package utils

import (
	"strings"
	"testing"
)

func TestIsValidAPIKey(t *testing.T) {
	tests := []struct {
		name   string
		key    string
		minLen int
		maxLen int
		want   bool
	}{
		{"valid key", "lotus-backend-dev-key", 8, 64, true},
		{"empty", "", 8, 64, false},
		{"too short", "abc", 8, 64, false},
		{"too long", strings.Repeat("a", 65), 8, 64, false},
		{"contains space", "bad key", 4, 64, false},
		{"contains newline", "bad\nkey", 4, 64, false},
		{"exact min length", "abcdefgh", 8, 64, true},
		{"exact max length", strings.Repeat("a", 64), 8, 64, true},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := IsValidAPIKey(tc.key, tc.minLen, tc.maxLen)
			if got != tc.want {
				t.Errorf("IsValidAPIKey(%q, %d, %d) = %v, want %v", tc.key, tc.minLen, tc.maxLen, got, tc.want)
			}
		})
	}
}

func TestClamp(t *testing.T) {
	tests := []struct {
		v, lo, hi, want int
	}{
		{5, 1, 10, 5},
		{0, 1, 10, 1},
		{15, 1, 10, 10},
		{1, 1, 10, 1},
		{10, 1, 10, 10},
	}
	for _, tc := range tests {
		got := Clamp(tc.v, tc.lo, tc.hi)
		if got != tc.want {
			t.Errorf("Clamp(%d, %d, %d) = %d, want %d", tc.v, tc.lo, tc.hi, got, tc.want)
		}
	}
}
