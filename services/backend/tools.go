//go:build tools
// +build tools

// Package tools tracks tool dependencies for the backend service.
// This file ensures that `go mod tidy` keeps tool dependencies in go.mod.
// See https://github.com/golang/go/wiki/Modules#how-can-i-track-tool-dependencies-for-a-module
package tools

import (
	_ "github.com/matryer/moq"
)
