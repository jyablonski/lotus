package main

import (
	"context"
	"fmt"
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	otelprom "go.opentelemetry.io/otel/exporters/prometheus"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
)

const serviceName = "lotus-backend"

func newResource() *resource.Resource {
	return resource.NewWithAttributes(
		semconv.SchemaURL,
		semconv.ServiceName(serviceName),
		semconv.ServiceVersion("1.0.0"),
	)
}

// initTracer configures the global OTel trace provider with an OTLP HTTP
// exporter. The endpoint is read from OTEL_EXPORTER_OTLP_ENDPOINT (default
// http://localhost:4318). Call the returned shutdown func on exit.
func initTracer(ctx context.Context) (func(context.Context) error, error) {
	endpoint := os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
	if endpoint == "" {
		endpoint = "http://localhost:4318"
	}

	exporter, err := otlptracehttp.New(ctx,
		otlptracehttp.WithEndpointURL(fmt.Sprintf("%s/v1/traces", endpoint)),
		otlptracehttp.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("create trace exporter: %w", err)
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(newResource()),
	)
	otel.SetTracerProvider(tp)

	// W3C TraceContext + Baggage so context headers are injected into outbound
	// requests and extracted from inbound ones by otelhttp / otelgrpc.
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{},
		propagation.Baggage{},
	))

	return tp.Shutdown, nil
}

// initMeter configures the global OTel meter provider using a Prometheus
// exporter. Metrics are exposed at /metrics for Prometheus to scrape — no
// push or context needed. Call the returned shutdown func on exit.
func initMeter() (func(context.Context) error, error) {
	exporter, err := otelprom.New()
	if err != nil {
		return nil, fmt.Errorf("create prometheus exporter: %w", err)
	}

	mp := metric.NewMeterProvider(
		metric.WithReader(exporter),
		metric.WithResource(newResource()),
	)
	otel.SetMeterProvider(mp)
	return mp.Shutdown, nil
}
