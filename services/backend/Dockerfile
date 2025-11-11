FROM golang:1.25 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Ensure we're doing a static build with no CGO dependencies
ENV CGO_ENABLED=0 GOOS=linux GOARCH=amd64

RUN go build -o lotus ./internal/main.go

FROM debian:bullseye-slim

RUN useradd -m -s /bin/bash lotususer

WORKDIR /home/lotususer

COPY --from=builder /app/lotus .

RUN chown lotususer:lotususer lotus

USER lotususer

EXPOSE 8080
EXPOSE 50051

CMD ["./lotus"]
