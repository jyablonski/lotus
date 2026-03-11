package utils

import (
	"context"
	"fmt"
	"math/rand"
	"time"
)

// RetryWithBackoff calls fn up to maxAttempts times, using exponential backoff
// with ±20% jitter between retries. It stops early if ctx is cancelled.
// Returns nil on the first successful call, or the last error if all attempts fail.
func RetryWithBackoff(ctx context.Context, maxAttempts int, fn func() error) error {
	var lastErr error
	baseDelay := time.Second

	for attempt := 1; attempt <= maxAttempts; attempt++ {
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("context cancelled before attempt %d: %w", attempt, err)
		}

		lastErr = fn()
		if lastErr == nil {
			return nil
		}

		if attempt == maxAttempts {
			break
		}

		// Exponential backoff: 1s, 2s, 4s, ... with ±20% jitter
		delay := baseDelay * (1 << (attempt - 1))
		jitter := time.Duration(float64(delay) * (0.8 + 0.4*rand.Float64()))
		select {
		case <-ctx.Done():
			return fmt.Errorf("context cancelled during backoff: %w", ctx.Err())
		case <-time.After(jitter):
		}
	}

	return fmt.Errorf("all %d attempts failed: %w", maxAttempts, lastErr)
}
