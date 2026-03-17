package utils

import (
	"testing"
)

// TestGenerateSalt checks if the generated salt is of expected length and non-empty.
func TestGenerateSalt(t *testing.T) {
	salt, err := GenerateSalt(24)
	if err != nil {
		t.Fatalf("GenerateSalt returned error: %v", err)
	}

	if len(salt) == 0 {
		t.Error("Expected non-empty salt string")
	}

	// base64 encoding of 24 bytes = ~32 characters
	if len(salt) < 32 {
		t.Errorf("Expected salt length >= 32, got %d", len(salt))
	}
}

// TestHashPassword checks if the hash output is deterministic for the same inputs.
func TestHashPassword(t *testing.T) {
	password := "securePassword123"
	salt := "randomSaltValue"

	hash1 := HashPassword(password, salt)
	hash2 := HashPassword(password, salt)

	if hash1 != hash2 {
		t.Errorf("Expected consistent hashes, got %s and %s", hash1, hash2)
	}

	if len(hash1) != 64 {
		t.Errorf("Expected SHA256 hash length of 64, got %d", len(hash1))
	}
}

// TestHashPasswordDifferentInputs ensures that different salts produce different hashes.
func TestHashPasswordDifferentInputs(t *testing.T) {
	password := "securePassword123"

	hash1 := HashPassword(password, "saltOne")
	hash2 := HashPassword(password, "saltTwo")

	if hash1 == hash2 {
		t.Errorf("Expected different hashes for different salts, but got the same")
	}
}

func TestMaskSecret(t *testing.T) {
	tests := []struct {
		name  string
		input string
		n     int
		want  string
	}{
		{"normal key", "abcdefghij", 2, "ab******ij"},
		{"too short returns placeholder", "ab", 2, "***"},
		{"n zero returns placeholder", "abcdefgh", 0, "***"},
		{"unicode safe", "αβγδεζηθ", 2, "αβ****ηθ"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := MaskSecret(tc.input, tc.n)
			if got != tc.want {
				t.Errorf("MaskSecret(%q, %d) = %q, want %q", tc.input, tc.n, got, tc.want)
			}
		})
	}
}
