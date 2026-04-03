package grpc

import "errors"

var (
	ErrInvalidUserID    = errors.New("invalid user ID")
	ErrJournalForbidden = errors.New("journal access denied")
	ErrEmptyJournalText = errors.New("journal text is required")
)
