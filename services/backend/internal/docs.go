package main

import (
	"embed"
	"encoding/json"
	"fmt"
	"io/fs"
	"log/slog"
	"net/http"
	"strings"
)

//go:embed pb/proto
var swaggerFS embed.FS

// mergedSwaggerSpec walks all *_service.swagger.json files embedded from the
// generated protobuf output and merges their paths and definitions into a
// single Swagger 2.0 document served at /swagger.json.
func mergedSwaggerSpec() ([]byte, error) {
	type swaggerDoc struct {
		Swagger     string                 `json:"swagger"`
		Info        map[string]interface{} `json:"info"`
		Tags        []interface{}          `json:"tags"`
		Paths       map[string]interface{} `json:"paths"`
		Definitions map[string]interface{} `json:"definitions"`
	}

	merged := swaggerDoc{
		Swagger:     "2.0",
		Info:        map[string]interface{}{"title": "Lotus API", "version": "1.0.0"},
		Paths:       make(map[string]interface{}),
		Definitions: make(map[string]interface{}),
	}

	err := fs.WalkDir(swaggerFS, "pb/proto", func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil || d.IsDir() {
			return walkErr
		}
		if !strings.HasSuffix(path, "_service.swagger.json") {
			return nil
		}
		data, err := swaggerFS.ReadFile(path)
		if err != nil {
			return fmt.Errorf("read %s: %w", path, err)
		}
		var doc swaggerDoc
		if err := json.Unmarshal(data, &doc); err != nil {
			return fmt.Errorf("parse %s: %w", path, err)
		}
		merged.Tags = append(merged.Tags, doc.Tags...)
		for k, v := range doc.Paths {
			merged.Paths[k] = v
		}
		for k, v := range doc.Definitions {
			merged.Definitions[k] = v
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return json.MarshalIndent(merged, "", "  ")
}

const swaggerUIHTML = `<!DOCTYPE html>
<html>
<head>
  <title>Lotus API Docs</title>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
<script>
  SwaggerUIBundle({
    url: "/swagger.json",
    dom_id: "#swagger-ui",
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
    layout: "StandaloneLayout",
  });
</script>
</body>
</html>`

// registerDocsHandlers adds /swagger.json and /docs routes to mux.
// The merged spec is computed once at startup from embedded swagger files.
func registerDocsHandlers(mux *http.ServeMux, logger *slog.Logger) {
	spec, err := mergedSwaggerSpec()
	if err != nil {
		logger.Error("Failed to build merged Swagger spec", "error", err)
		return
	}

	mux.HandleFunc("/swagger.json", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write(spec)
	})

	mux.HandleFunc("/docs", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = fmt.Fprint(w, swaggerUIHTML)
	})
}
