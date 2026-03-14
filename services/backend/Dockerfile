FROM golang:1.25 AS builder

WORKDIR /app

COPY --link go.mod go.sum ./
RUN go mod download

COPY --link . .

ENV CGO_ENABLED=0 GOOS=linux GOARCH=amd64

RUN go build -o lotus ./internal/

FROM scratch

# CA certs for HTTPS calls
COPY --link --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Timezone data (if you need it)
COPY --link --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

COPY --link --from=builder /app/lotus /lotus

# Run as nonroot (65534 is nobody)
USER 65534

EXPOSE 8080
EXPOSE 50051

ENTRYPOINT ["/lotus"]
