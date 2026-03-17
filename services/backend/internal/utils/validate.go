package utils

import (
	"strings"
	"unicode/utf8"
)

// IsValidAPIKey returns true when key is non-empty, contains no whitespace,
// and falls within the expected length range.
func IsValidAPIKey(key string, minLen, maxLen int) bool {
	if key == "" || strings.ContainsAny(key, " \t\n\r") {
		return false
	}
	n := utf8.RuneCountInString(key)
	return n >= minLen && n <= maxLen
}

// Clamp returns v clamped to [lo, hi].
func Clamp(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}
