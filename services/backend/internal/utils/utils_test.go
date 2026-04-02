package utils

import (
	"testing"
)

func TestHashPassword(t *testing.T) {
	password := "securePassword123"

	hash, err := HashPassword(password)
	if err != nil {
		t.Fatalf("HashPassword returned error: %v", err)
	}

	if len(hash) == 0 {
		t.Error("Expected non-empty hash string")
	}

	// bcrypt hashes are 60 characters
	if len(hash) != 60 {
		t.Errorf("Expected bcrypt hash length of 60, got %d", len(hash))
	}
}

func TestHashPasswordUniqueSalts(t *testing.T) {
	password := "securePassword123"

	hash1, err := HashPassword(password)
	if err != nil {
		t.Fatalf("HashPassword returned error: %v", err)
	}

	hash2, err := HashPassword(password)
	if err != nil {
		t.Fatalf("HashPassword returned error: %v", err)
	}

	// bcrypt generates a unique salt each time, so hashes should differ.
	if hash1 == hash2 {
		t.Error("Expected different hashes due to unique bcrypt salts")
	}
}

func TestCheckPassword(t *testing.T) {
	password := "securePassword123"

	hash, err := HashPassword(password)
	if err != nil {
		t.Fatalf("HashPassword returned error: %v", err)
	}

	if !CheckPassword(password, hash) {
		t.Error("CheckPassword should return true for correct password")
	}

	if CheckPassword("wrongPassword", hash) {
		t.Error("CheckPassword should return false for incorrect password")
	}
}
