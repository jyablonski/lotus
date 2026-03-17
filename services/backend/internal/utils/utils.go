package utils

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"fmt"
)

func GenerateSalt(n int) (string, error) {
	bytes := make([]byte, n)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return base64.StdEncoding.EncodeToString(bytes), nil
}

func HashPassword(password, salt string) string {
	hash := sha256.Sum256([]byte(password + salt))
	return fmt.Sprintf("%x", hash)
}

// MaskSecret returns s with all but the first and last n characters replaced
// by asterisks. Safe to use in logs when s may be an API key or token.
// If s is too short to mask meaningfully, it returns a fixed placeholder.
func MaskSecret(s string, n int) string {
	runes := []rune(s)
	if n < 1 || len(runes) <= n*2 {
		return "***"
	}
	masked := make([]rune, len(runes))
	copy(masked[:n], runes[:n])
	for i := n; i < len(runes)-n; i++ {
		masked[i] = '*'
	}
	copy(masked[len(runes)-n:], runes[len(runes)-n:])
	return string(masked)
}
